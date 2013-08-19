
from houdini_stats.models import *
from qsstats import QuerySetStats
from django.db.models import Avg, Sum, Count
from django.db import connection
from collections import defaultdict
import datetime

#===============================================================================
def _time_series(queryset, date_field, interval, func=None, agg=None):
    if agg is None: 
        qsstats = QuerySetStats(queryset, date_field, func)
        return qsstats.time_series(*interval)

    else:
        # Custom aggregation was set (weekly/monthly/yearly)
        agg_by = agg[:-2]

        # We need to set the range dynamically
        interval_filter = {date_field + "__gte" : interval[0],
                           date_field + "__lte" : interval[1]}

        # Slightly raw-ish SQL query
        result = queryset.extra(select={agg_by: connections[queryset.db].ops.date_trunc_sql(agg_by, date_field)}) \
                             .values_list(agg_by) \
                             .annotate(dcount=Count(date_field)) \
                             .filter(**interval_filter) \
                             .order_by(agg_by)

        return _add_missing(result, agg_by)

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
    # Get all Uptimes
    uptimes = Uptime.objects.values('machine_config') \
                            .annotate(m_count=Count('machine_config')) \
                            .order_by('date')
    
    return _time_series(uptimes, 'date', series_range, 
                                          func=Avg('number_of_seconds'), 
                                          agg=aggregation)

#-------------------------------------------------------------------------------   
def average_usage_by_machine(start_date, end_date):
    """
    Get Houdini average usage by machine. Column Chart.
    """

    cursor = connection.cursor()
    cursor.execute("""
        select day, avg(total_seconds)
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
    
    #TODO: build the data by filling the empty days too.
    return [(row[0], row[1]) for row in cursor.fetchall()]

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
# Houdini Versions and Builed related reports

def usage_by_hou_version_or_build(build=False, hou_product=""):
    """
    Usage by Houdini version or builds. Aggregating or not by product.
    """
    
    dict_values_app = defaultdict(int)
    
    for machine_config in MachineConfig.objects.exclude(houdini_major_version=0,
                                                        product=""):
        # Build houdini version
        houdini_version = str(machine_config.houdini_major_version) +  "."+ \
                          str(machine_config.houdini_minor_version) 
        # Add build if needed
        if build: 
            houdini_version += "." + machine_config.houdini_build_number
            
        suffix = "Houdini "     
        combination = suffix + houdini_version
        if hou_product != "":
            # Build combination houdini product and houdini version
            if hou_product in machine_config.product:
                combination = hou_product + " " + houdini_version 
                if not suffix in machine_config.product:
                    combination = suffix + combination
                dict_values_app[combination] += 1
        else:
            dict_values_app[combination] += 1
   
    return [[houdini, count] for houdini, count in
                                     dict_values_app.iteritems()]


