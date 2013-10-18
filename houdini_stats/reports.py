from houdini_stats.models import *
from houdini_licenses.models import *
from houdini_surveys.models import *
from houdini_forum.models import *

from qsstats import QuerySetStats
from django.db.models import Avg, Sum, Count
from django.db import connections
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from utils import get_time
import time
import datetime
from settings import REPORTS_START_DATE
from dircache import annotate
from operator import *


#===============================================================================
def _get_start_request(request):
    """
    Get start date from the request.
    """
    start_request = request.GET.get("start", None)
    
    if start_request is not None:
        t = time.strptime(start_request, "%d/%m/%Y")
        start = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    else:
        # We launched the site in August
        start = REPORTS_START_DATE
    
    return start

#------------------------------------------------------------------------------- 
def _get_end_request(request):
    """
    Get end date from the request.
    """
    end_request = request.GET.get("end", None)
    
    if end_request is not None:
        t = time.strptime(end_request, "%d/%m/%Y")
        end = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    else:
        end = datetime.datetime.now()

    return end

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
def get_common_vars_for_charts(request):
    """
    Get all variables that will be used for the reports.
    """
    return [_get_start_request(request), _get_end_request(request)], \
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
def _get_time_series_sequences(
        queryset_sequences, interval, aggregation=None,
        date_field="created", func=None):
    """
    This function takes a sequence of querysets and apply time_series to each 
    of them using the arguments passed in the given order.
    """
    
    return [_time_series(queryset, date_field, interval, func, aggregation)
        for queryset in queryset_sequences]

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

    cursor = connections['stats'].cursor()
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
    cursor = connections['stats'].cursor()
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

#===============================================================================
# Surveys Database reports

def _get_user_answers_by_qid_aid(question_id=None, answer_id=None, 
                                 series_range=None):
    """
    Get user answers by the filters given as parameters.
    """
    queryset = UserAnswers.objects.all()
        
    if question_id is not None and answer_id is not None:
        # Both filters are not None
        queryset = queryset.filter(
            question_id=question_id, answer_id=answer_id)
    elif question_id is not None:
        # Assumed then answer_id none otherwise will be case above 
        queryset = queryset.filter(question_id=question_id)
    elif answer_id is not None:
        # Assumed then question_id is none otherwise will be first case 
        queryset = queryset.filter(answer_id=answer_id)
    
    #TODO: filter by dates too
#    if series_range is not None:
#        print series_range
#        return queryset.filter(date__range=[datetime.date(series_range[0]),
#                                            datetime.date(series_range[1])
#                                            ])
    
    return queryset

#-------------------------------------------------------------------------------

def get_questions_from_survey(survey_id, exclude_question_id=None):
    """
    Get a questions from survey id.
    """   
    if exclude_question_id:
        return Questions.objects.filter(survey_id=survey_id).exclude(
                                                id=exclude_question_id)
        
    return Questions.objects.filter(survey_id=survey_id)

#-------------------------------------------------------------------------------

def get_answers_from_question(question_id):
    """
    Get answers from a question id.
    """   
    return QuestionAnswers.objects.filter(question_id=question_id)
    
#-------------------------------------------------------------------------------

def _get_common_for_hou_engine_breakdown():
    
    question_id = 44
    answer_id_maya=229
    answer_id_unity=230
    
    users_for_maya= _get_user_answers_by_qid_aid(question_id=question_id,
                                                 answer_id=answer_id_maya)
    
    users_for_unity= _get_user_answers_by_qid_aid(question_id=question_id, 
                                                  answer_id=answer_id_unity)
    
    return users_for_maya, users_for_unity, (users_for_maya.count() + \
                                             users_for_unity.count()) 

#-------------------------------------------------------------------------------

def hou_engine_maya_unity_breakdown(series_range, aggregation):
    """
    Get breakdown of labs users who want Maya vs Unity plugin.
    Two graphs, a Column Chart showing the number of uses that selected
    Maya or Unity and, a Line Chart with the two lines for the users that 
    subscribed to Maya or Unity, over time.
    """
    
    users_for_maya, users_for_unity, count_total = _get_common_for_hou_engine_breakdown()
    
    users_count = [("Maya | Unity", users_for_maya.count(), users_for_unity.count())]
    
    users_over_time = _merge_time_series(_get_time_series_sequences([users_for_maya, users_for_unity],
                       interval= series_range, aggregation= aggregation,
                       date_field ="date"))
    
    return {"count_total": count_total, 
            "user_answers_count" : users_count, 
            "user_answers_over_time": users_over_time }

#-------------------------------------------------------------------------------

def _get_common_for_apprentice_followup_survey():
            
    survey_id = 2
    questions = get_questions_from_survey(survey_id, 8)
    
    questions_answers = {}
    
    for q in questions:
        answers_for_questions= get_answers_from_question(q.id)
        questions_answers[q.id] = {"question": q.question, 
                                   "answers" : answers_for_questions}
    
    return questions_answers 
    
#-------------------------------------------------------------------------------

def apprentice_followup_survey():
    """
    Get breakdown of labs users who want Maya vs Unity plugin.
    Two graphs, a Column Chart showing the number of uses that selected
    Maya or Unity and, a Line Chart with the two lines for the users that 
    subscribed to Maya or Unity, over ti <div class="graph-title">Users subscribed to Houdini Analytics </div>me.
    """
    
    questions_and_answers = _get_common_for_apprentice_followup_survey()
    questions_and_total_counts = {}
    sorted_answers = {}
    user_answers_total_count_list = []
    index_q = 0
    
    for key, value in questions_and_answers.items():
        
        index_q +=1
        question_id = key
        answers = value["answers"]
        answers_count = {}
        user_answers_total_count = 0
        
        for answer in answers:
            
            user_answers = _get_user_answers_by_qid_aid(
                                                    question_id=question_id, 
                                                    answer_id=answer.id)
            answers_count[answer.answer] = user_answers.count()    
            user_answers_total_count += user_answers.count()
            
        questions_and_total_counts[index_q] = {"text": value["question"],
                                                "count": user_answers_total_count}         
        sorted_answers[index_q] = sorted(answers_count.items(), 
                                                key=lambda x:x[1], reverse=True)

    return questions_and_total_counts, sorted_answers  

#===============================================================================
# Forum Database reports

def _get_active_users_over_time(series_range, aggregation):
    """
    Number of active users registered in SideFX website over time
    """
    
    return _time_series(MosUsers.objects.filter(user_active=1).exclude(id=-1),
                                  'registerdate', series_range, agg=aggregation)

#-------------------------------------------------------------------------------

def _get_active_users_by_method_per_day(start_date, end_date, openid=False):
    """
    Get count active users that registered with forum or open id per day, 
    given a period of time.
    """
    
    to_compare = "= u.id"
    if openid:
        to_compare = "IS NULL"
        
    cursor = connections['mambo'].cursor()    
    common_query = """
                   SELECT cast( cast( u.registerDate AS date ) AS datetime ) 
                          AS new_date, COUNT(u.id) AS user_count
                   FROM mos_users u
                   LEFT JOIN oid_user_to_mos_user a ON a.mos_user_id = u.id
                   WHERE u.id != -1
                   AND u.user_active =1
                   AND u.registerDate between date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
                         and date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S')
                   AND u.registerDate!= "0000-00-00 00:00:00"      
                   AND a.mos_user_id
                   """.format(start_date.strftime("%Y-%m-%d %H:%M:%S"),
                              end_date.strftime("%Y-%m-%d %H:%M:%S"))
    
    cursor.execute("{0} {1} {2}"
          .format(common_query, to_compare, "GROUP BY new_date ORDER BY new_date"))  
    
    return [(row[0], row[1]) for row in cursor.fetchall()]    

#-------------------------------------------------------------------------------
def _get_cumulative_values(tuples):
    """
    """
    return sum(user_count for date, user_count in tuples)

#-------------------------------------------------------------------------------             
def get_active_users_forum_and_openid(series_range, aggregation):
    """
    Number of users active that registered with forum or open id
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"

    # To get all users registered in the given interval
    all_users_serie = _get_active_users_over_time(series_range, aggregation)
    
    # Creating the time serie from the results of the cursor
    forum_serie = _get_active_users_by_method_per_day(start_date, end_date) 
    #Filling the empty dates
    forum_serie = _fill_missing_dates_with_zeros(forum_serie, aggregation,
                                                                  series_range) 
   
    # Creating the time serie from the results of the cursor
    openid_serie = _get_active_users_by_method_per_day(start_date, end_date, 
                                                        openid=True) 
    # Filling the empty dates
    openid_serie = _fill_missing_dates_with_zeros(openid_serie, aggregation, 
                                                                series_range)
    return _merge_time_series([all_users_serie, forum_serie, openid_serie])

#-------------------------------------------------------------------------------
def openid_providers_breakdown(series_range, aggregation):
    """
    Breakdown of open id user by providers
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"
    
    total_forum = _get_cumulative_values(_get_active_users_by_method_per_day(
                                                   start_date, end_date, False))
    total_openid= 0
    
    providers = {"forum":{"provider": "http://www.facebook.com/",
                          "count": total_forum},
                 "facebook": {"provider": "http://www.facebook.com/",
                              "count": 0},
                 "orbolt": {"provider": "https://www.orbolt.com/openid/",
                            "count": 0},
                 "gmail": {"provider": "https://www.google.com/accounts/",
                           "count": 0},
                 "yahoo": {"provider": "https://www.google.com/accounts/",
                           "count": 0},
                 "windowslive": {"provider": "https://profile.live.com/",
                                 "count": 0},
                 "linkedin": {"provider": "http://www.linkedin.com/pub/",
                              "count": 0},
                 "aol": {"provider": ".aofrom operator import *l",
                         "count": 0} 
                }
    
    cursor = connections['mambo'].cursor()
    
    cursor.execute("""SELECT provider_url FROM oid_user_to_mos_user a
                      LEFT JOIN mos_users u ON u.id = a.mos_user_id 
                      WHERE 
                      u.registerDate between date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
                         and date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S')
                      AND u.registerDate!= "0000-00-00 00:00:00"      
                      AND u.id = a.mos_user_id
                      """.format(start_date.strftime("%Y-%m-%d %H:%M:%S"),
                                 end_date.strftime("%Y-%m-%d %H:%M:%S")))
                   
    all_providers =  [row[0] for row in cursor.fetchall()]
    #total_openid= len(all_providers)
    
    
    for provider in all_providers:
        if providers["facebook"]["provider"] in provider:
            providers["facebook"]["count"] +=1 
            total_openid +=1
        
        if providers["gmail"]["provider"] in provider:
            providers["gmail"]["count"] +=1
            total_openid +=1       
        
        elif providers["yahoo"]["provider"] in provider:
            providers["yahoo"]["count"] +=1
            total_openid +=1 
        
        elif providers["orbolt"]["provider"] in provider:
            providers["orbolt"]["count"] +=1
            total_openid +=1  
        
        elif providers["windowslive"]["provider"] in provider:
            providers["windowslive"]["count"] +=1
            total_openid +=1 
        
        elif providers["linkedin"]["provider"] in provider:
            providers["linkedin"]["count"] +=1
            total_openid +=1                    
    
        elif providers["aol"]["provider"] in provider:
            providers["aol"]["count"] +=1
            total_openid +=1        
    
    # Sort providers by count descendent order
    sorted_providers= sorted(providers.items(),
                             key=lambda x:getitem(x[1],'count'), 
                             reverse=True)
    
    return [(key.title(),value["count"]) for key, value in sorted_providers], \
            total_forum, total_openid 

#-------------------------------------------------------------------------------
def get_num_of_user_registered_and_asked_to_susbcribe(series_range, aggregation):
    """
    Number of users registered and asked to subscribe, over time
    """
    return _time_series(MachineConfig.objects.filter(asked_to_subscribe=1),
                              'last_active_date',series_range, agg=aggregation)

    