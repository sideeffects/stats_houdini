from houdini_stats.models import *
from houdini_licenses.models import *

from qsstats import QuerySetStats
from django.db.models import Avg, Sum, Count
from django.db import connections, connection 
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from utils import get_time
import time
import datetime
import settings
from dircache import annotate

#===============================================================================
def _get_start_request(request):
    """
    Get start date from the request.
    """
    return request.GET.get("start", None)

#------------------------------------------------------------------------------- 
def _get_end_request(request):
    """
    Get end date from the request.
    """
    return request.GET.get("end", None)

#-------------------------------------------------------------------------------     
def _series_range(start_request, end_request):
    """
    Series range parameter to pass for the reports
    """
    # Get the time interval for the graphs
    if start_request is not None:
        t = time.strptime(start_request, "%d/%m/%Y")
        start = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    else:
        # We launched the site in August
        start = settings.STARTING_DATE

    if end_request is not None:
        t = time.strptime(end_request, "%d/%m/%Y")
        end = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    else:
        end = datetime.datetime.now()

    # By default, time_series will get the count
    return [start, end]

#------------------------------------------------------------------------------- 
def _get_aggregation(get_vars):
    """
    Get aggregation from the request.GET.
    """
    # For aggregation 
    valid_agg = ["monthly", "weekly", "yearly", "daily"]
    if "ag" not in get_vars:
        return None
    
    aggregation = get_vars["ag"].lower()
    
    if aggregation not in valid_agg and aggregation !="inherit":
        raise NotFoundError("Not valid aggregation")
    elif aggregation=="inherit":
        return None  
    
    return aggregation 

#------------------------------------------------------------------------------- 
def get_common_vars(request):
    """
    Get all variables that will be used for the reports.
    """
    return _get_start_request(request), _get_end_request(request), \
           _series_range(_get_start_request(request), 
                         _get_end_request(request)), \
           _get_aggregation(request.GET)

#-------------------------------------------------------------------------------
def _fill_missing_dates_with_zeros(time_series, agg_by, interval):
    """
    When aggregating licenses, we don't get back any months that
    have no activity. Using dateutil, we will find such months
    months, and add them with to the report, with a count of 0.
    """
    result_time_series = []
    dates = [x[0] for x in time_series]

    # Determine the first date that will be in the result time series.  If
    # we're aggregating, we need to step through the dates starting with the
    # first day of the week/month/year.
    current_date = interval[0]
    if agg_by == "week":
        # Find the Monday at the beginning of the week.
        current_date -= relativedelta(days=interval[0].weekday())
    elif agg_by == "month":
        current_date = current_date.replace(day=1)
    elif agg_by == "year":
        current_date = current_date.replace(day=1, month=1)
    elif agg_by == "daily":
        agg_by = "day"
    else:
        assert False, "Unknown aggregation type"

    # Loop through all the dates from the start up to and including the end,
    # filling any missing data points with zeros.
    index = 0
    
    while current_date <= interval[1]:
        if current_date in dates: 
            result_time_series.append([current_date, time_series[index][1]])
            index += 1
        else:
            result_time_series.append([current_date, 0])

        current_date += relativedelta(**{agg_by + "s": 1})

    return result_time_series

#-------------------------------------------------------------------------------
def _time_series(queryset, date_field, interval, func=None, agg=None):
    if agg in (None, "daily"): 
        qsstats = QuerySetStats(queryset, date_field, func)
        return qsstats.time_series(*interval)
    else:
        # Custom aggregation was set (weekly/monthly/yearly)
        agg_by = agg[:-2]

        # We need to set the range dynamically
        interval_filter = {date_field + "__gte" : interval[0],
                           date_field + "__lte" : interval[1]}

        # Slightly raw-ish SQL query
        result = (queryset.extra(select={agg_by: connections[queryset.db]
                             .ops.date_trunc_sql(agg_by, date_field)})
                             .values_list(agg_by)
                             .annotate(dcount=Count(date_field))
                             .filter(**interval_filter)
                             .order_by(agg_by))
        
        return _fill_missing_dates_with_zeros(result, agg_by, interval)

#-------------------------------------------------------------------------------
def _merge_time_series(time_series_sequences):
    """Given a sequence in the form
        [
            [(0, 10), (1, 20), (2, 15),],
            [(0, 5), (1, 4), (2, 22),]
        ]
    return a sequence of the form
        [
            (0, 10, 5),
            (1, 20, 
            4),
            (2, 15, 22),
        ]
    Note that the first elements (the 0's, 1's and 2's in the example above)
    must be the same.
    """
    # zip will put the data into the form
    #    [
    #        ((0, 10), (0, 5)),
    #        ((1, 20), (1, 4)),
    #        ((2, 15), (3, 22)),
    #    ]
    assert _time_series_x_axes_line_up(time_series_sequences), \
        "Time series x axes do not line up"
    return [(pairs[0][0],) + tuple(pair[1] for pair in pairs)
        for pairs in zip(*time_series_sequences)]

#-------------------------------------------------------------------------------
def _time_series_x_axes_line_up(time_series_sequences):
    """Return whether or not a sequence of time series all contain the same
    x values.
    """
    for pairs in zip(*time_series_sequences):
        if [pair[0] for pair in pairs] != [pairs[0][0]] * len(pairs):
            return False
    return True

#-------------------------------------------------------------------------------
def _compute_time_series(time_series_sequences, operation):
    """Given a sequence in the form
        [
            [(0, 10), (1, 20), (2, 15),],
            [(0, 5), (1, 4), (2, 22),]
        ]
    and an operation of the form
        lambda v0, v1: v0 * v1
    return
        [(0, 50), (1, 80), (2, 330)]
    """
    assert _time_series_x_axes_line_up(time_series_sequences), \
        "Time series x axes do not line up"
    return [(pairs[0][0], operation(*tuple(pair[1] for pair in pairs)))
        for pairs in zip(*time_series_sequences)]

#-------------------------------------------------------------------------------
def _compute_time_serie(time_serie, operation):
    """Given a time series in the form
        
        [(x, 10), (y, 20), (z, 15)]
    
    and an operation of the form
        lambda v1: v1 * 2
    return
        [(x, 20), (y, 40), (z, 30)]
    """
    return [tuple((pair[0], operation(pair[1]))) for pair in time_serie]

#-------------------------------------------------------------------------------
def _get_right_time(time_serie, time_key="seconds"):
    """Given a time series in the form
        
        [(x,  {'hours': 0, 'seconds': 0, 'minutes': 0, 'days': 0}),
         (y,  {'hours': 0, 'seconds': 0, 'minutes': 0, 'days': 0})),
         (z,  {'hours': 0, 'seconds': 0, 'minutes': 0, 'days': 0}))
        ]
    
    and an a time key like: minutes, hours, days, seconds
    return
        [(x, num), (y, num), (z, num)]
    """
    return  [tuple((pair[0], pair[1][time_key])) for pair in time_serie]

#===============================================================================
# Houdini Crashes related reports

def get_hou_crashes_over_time(series_range):
    """
    Get Houdini Crashes over time, in a give date range. Line Chart.index
    """
    # Get Crashes
    houdini_crashes = HoudiniCrash.objects.all()
    
    return _time_series(houdini_crashes, 'date', series_range)

#-------------------------------------------------------------------------------
def get_hou_crashes_group_by_os(series_range):
    """
    Get Houdini Crashes grouped by operating system, in a give date range.
    Pie Chart.
    """
    # Get Crashes
    houdini_crashes_query = HoudiniCrash.objects.all()
    
    return _time_series(houdini_crashes_query,'date', series_range)

#-------------------------------------------------------------------------------
def get_hou_crashes_group_by_product(series_range):
    """
    Get Houdini Crashes grouped by product (Apprentice, Houdini FX, etc), 
    in a give date range. Pie.
    """
    # Get Crashes
    houdini_crashes_query = HoudiniCrash.objects.all()
    
    return _time_series(houdini_crashes_query,'date', series_range)

#===============================================================================
# Houdini Uptime related reports

def average_session_length(series_range, aggregation):
    """
    Get Houdini average session length. Column Chart.
    """
    
    uptimes = Uptime.objects.all()
    
    time_serie = _time_series(uptimes, 'date', series_range, 
                                          func=Avg("number_of_seconds"), 
                                          agg=aggregation)

    return _get_right_time(_compute_time_serie(time_serie, get_time), "minutes") 
    
#-------------------------------------------------------------------------------   
def average_usage_by_machine(series_range, aggregation):
    """
    Get Houdini average usage by machine. Column Chart.
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"

    cursor = connection.cursor()
    cursor.execute("""
        select cast(day as datetime), avg(total_seconds)
        from (
            select machine_config_id, str_to_date(date_format(date, '%%Y-%%m-%%d'), '%%Y-%%m-%%d') as day,
                sum(number_of_seconds) as total_seconds
                from houdini_stats_uptime
                where date between date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
                    and date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S')
                group by machine_config_id, day
        ) as TempTable
        group by day
        order by day""".format(
            start_date.strftime("%Y-%m-%d %H:%M:%S"),
            end_date.strftime("%Y-%m-%d %H:%M:%S"))
        )  
    
    time_serie = [(row[0], row[1]) for row in cursor.fetchall()]
    serie = _get_right_time(_compute_time_serie(time_serie, get_time),"minutes")
    
    return _fill_missing_dates_with_zeros(serie, aggregation, series_range)
                                  
#===============================================================================
# Houdini Nodes Usage related reports

def most_popular_nodes(node_usage_count, limit):
    """
    Most popular nodes, the ones with more than node_usage_count number of usage. 
    Column Chart.
    """
    cursor = connection.cursor()
    cursor.execute("""
        select node_type, node_count 
        from (
            select sum(count) as node_count, node_type
                from houdini_stats_nodetypeusage
                group by node_type 
                order by node_count
        ) as TempTable
        where node_count >={0}
        order by node_count desc
        limit {1}
       """.format(node_usage_count, limit)    
       ) 
    
    return [(row[0], row[1]) for row in cursor.fetchall()]

#===============================================================================
# Houdini Versions and Builds related reports

def usage_by_hou_version_or_build(all=True, build=False, is_apprentice=False):
    """
    Usage by Houdini version or builds. Aggregating or not by product.
    """
    
    dict_values_app = defaultdict(int)
    
    mc_query_set = ""
    if all:
        mc_query_set =  MachineConfig.objects.exclude(houdini_major_version=0,
                                                       product="")
    else:
        mc_query_set = MachineConfig.objects.filter(is_apprentice=
                                                    is_apprentice).exclude(
                                                        houdini_major_version=0,
                                                        product="")
        
    for machine_config in mc_query_set:
        # Build houdini version
        houdini_version = str(machine_config.houdini_major_version) +  "."+ \
                          str(machine_config.houdini_minor_version) 
        # Add build if needed
        if build: 
            houdini_version += "." + machine_config.houdini_build_number
            
        suffix = "Houdini "     
        combination = suffix + houdini_version
        
        if is_apprentice and machine_config.is_apprentice:
            # Build combination houdini product and houdini version
            combination = "Apprentice" + " " + houdini_version 
            if not suffix in machine_config.product:
                combination = suffix + combination
            dict_values_app[combination] += 1
        else:
            dict_values_app[combination] += 1
   
    return [[houdini, count] for houdini, count in
                                     dict_values_app.iteritems()]


#===============================================================================
# General reports

def get_users_over_time(series_range, aggregation):
    """
    Get machine configs over time.
    """
    apprentice_activations_over_time(series_range, aggregation)
    return _time_series(MachineConfig.objects.all(), 'last_active_date', 
                                                 series_range, agg=aggregation)

#===============================================================================
# Houdini Licenses related reports

def apprentice_activations_over_time(series_range, aggregation):
    """
    Get Apprentice Activations over time. Line Chart.
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"

    nc_custid = 2711
    cursor = connections['licensedb'].cursor()
    
    cursor.execute("""
        select cast(activation_date as datetime)
                          as date, 
               count(*) as num_activated
        from (
            select from_days(min(to_days(Keystrings.CreateDate))) as 
                   activation_date 
            from Servers, Keystrings
            where Servers.CustID='{0}'
            and Servers.ServerID=Keystrings.ServerID
            and Keystrings.KType='LICENSE'
            group by Servers.ServerID
        ) as TempTable
        where activation_date between date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S')
                         and date_format('{2}', '%%Y-%%c-%%d %%H:%%i:%%S')
        group by date  
        order by date  
        """.format(nc_custid, 
                   start_date.strftime("%Y-%m-%d %H:%M:%S"),
                   end_date.strftime("%Y-%m-%d %H:%M:%S")
                  )
        )  
    
    return [(row[0], row[1]) for row in cursor.fetchall()]

