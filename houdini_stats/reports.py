from houdini_stats.models import *
from houdini_licenses.models import *
from houdini_surveys.models import *
from houdini_forum.models import *

from django.db.models import Avg, Sum, Count
from django.db import connections
from collections import defaultdict

from utils import get_percent, get_lat_and_long, seconds_to_multiple_time_units
                   
import time_series 
import time
import datetime
from dircache import annotate
from operator import *

from django.template import Context, Template
    
#===============================================================================

def _get_list_of_tuples_from_list(list):
    """
    Get a list of tuples from a list.
    
    For example given:    
    
    [1,2,3,4,5,6]
    
    Return [(1,2),(3,4)(5,6)]
    
    """
    output = []
    item = []
    
    for i in list:
        item.append(i)
        if len(item) == 2:
            output.append(item)
            item = []
    if item:
        output.append(item) 
    
    return output

#-------------------------------------------------------------------------------   

def _get_cursor(db_name):
    """
    Given a db name returns a cursor.
    """
    return connections[db_name].cursor()
#-------------------------------------------------------------------------------

def _get_sql_report_data(string_query, db_name, context_vars):
    """
    Generic function to get data for reports which use cursors.
    
    This func will receive the query, the database name to create a cursor.
    The the period range, the aggregation. And will also receive as parameter
    the time unit we want the data to be presented.    
    """
    
    context_vars = context_vars.copy()
    
    context_vars["start_date"] = context_vars['series_range'][0] 
    context_vars["end_date"] = context_vars['series_range'][1]
    
    if context_vars['aggregation'] is None:
        context_vars['aggregation'] = "daily"
    
    cursor = _get_cursor(db_name)
    tpl_header =  "{% load reports_tags %} "
         
    tpl = Template(tpl_header + string_query)
    
    cursor.execute(tpl.render(Context(context_vars)))
    
    # Build time serie from the data in the cursor and fill with zeros the 
    # empty dates
    return time_series.fill_missing_dates_with_zeros(
                               [(row[0], row[1]) for row in cursor.fetchall()],
                               context_vars['aggregation'][:-2], 
                               context_vars['series_range'])  
    
#===============================================================================
# Houdini Crashes related reports

def get_hou_crashes_over_time(series_range):
    """
    Get Houdini Crashes over time, in a give date range. Line Chart.index
    """
    # Get Crashes
    houdini_crashes = HoudiniCrash.objects.all()
    
    return time_series.time_series(houdini_crashes, 'date', series_range)

#-------------------------------------------------------------------------------
def get_hou_crashes_group_by_os(series_range):
    """
    Get Houdini Crashes grouped by operating system, in a give date range.
    Pie Chart.
    """
    # Get Crashes
    houdini_crashes_query = HoudiniCrash.objects.all()
    
    return times_series.time_series(houdini_crashes_query,'date', series_range)

#-------------------------------------------------------------------------------
def get_hou_crashes_group_by_product(series_range):
    """
    Get Houdini Crashes grouped by product (Apprentice, Houdini FX, etc), 
    in a give date range. Pie.
    """
    # Get Crashes
    houdini_crashes_query = HoudiniCrash.objects.all()
    
    return times_series.time_series(houdini_crashes_query,'date', series_range)

#===============================================================================
# Houdini Uptime related reports

def average_session_length(series_range, aggregation):
    """
    Get Houdini average session length. Column Chart.
    """
    
    uptimes = Uptime.objects.all()
    
    serie = time_series.time_series(uptimes, 'date', series_range, 
                                          func=Avg("number_of_seconds"), 
                                          agg=aggregation)

    return time_series.choose_unit_from_multiple_time_units_series(
           time_series.compute_time_serie(serie, seconds_to_multiple_time_units),
                                                                     "hours") 
    

    
#-------------------------------------------------------------------------------
def average_usage_by_machine(series_range, aggregation):
    """
    Get Houdini average usage by machine. Column Chart.
    """
    
    string_query = """
         select {% aggregated_date "day" aggregation %} AS mydate, avg(total_seconds)
         from (
             select machine_config_id,
             str_to_date(date_format(date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
             sum(number_of_seconds) as total_seconds
             from houdini_stats_uptime
             where {% where_between "date" start_date end_date %}
             group by machine_config_id, day
         ) as TempTable
         group by mydate
         order by mydate"""
    
    return time_series.seconds_to_time_unit_series(
        _get_sql_report_data(string_query, 'stats', locals()), 
        "hours")

#===============================================================================
# Houdini Tools Usage related reports

def _most_popular_tools_base_query():
    """
    Creates the base query for most popular tools.
    """
    return """
           select tool_name, tool_count 
           from (
              select sum(count) as tool_count, tool_name, tool_creation_mode
                from houdini_stats_houdinitoolusage
                group by tool_name 
                order by tool_count
           ) as TempTable
           """

#-------------------------------------------------------------------------------  
def most_popular_tools(tool_usage_count, limit, creation_mode=0):
    """
    Most popular houdini tools, the ones with more than tool_usage_count number of usage. 
    Column Chart.
    """
    cursor = connections['stats'].cursor()
    base_query = _most_popular_tools_base_query()
    
    where_query = "where"
    if creation_mode !=0:
        where_query = where_query + " tool_creation_mode={0} and".format(
                                                                  creation_mode) 
    where_query = where_query + """ tool_count >={0} order by tool_count desc
                                    limit {1}""".format(tool_usage_count, limit)
    
    cursor.execute("{0} {1}".format(base_query, where_query)) 
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

def get_new_machines_over_time(series_range, aggregation):
    """
    Get new machines over time.
    """    
    string_query = """
        select {% aggregated_date "min_creation_date" aggregation %} AS mydate, machines_count
        from(  
            select min(str_to_date(date_format(creation_date, '%%Y-%%m-%%d'), '%%Y-%%m-%%d')) as min_creation_date,
                   count(distinct machine_id) as machines_count 
            from houdini_stats_machineconfig
            where {% where_between "creation_date" start_date end_date %}
            group by machine_id
            order by min_creation_date)
        as TempTable
        group by mydate
        order by mydate"""
        
    return _get_sql_report_data(string_query,'stats', locals())
        
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
    
    if series_range is not None:
        return queryset.filter(date__range=[series_range[0],
                                            series_range[1]
                                            ])
    
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
    
    users_over_time = time_series.merge_time_series(time_series.seconds_to_multiple_time_units_series_sequences([users_for_maya, users_for_unity],
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

def apprentice_followup_survey(series_range, aggregation):
    """
    Get breakdown of labs users who want Maya vs Unity plugin.
    Two graphs, a Column Chart showing the number of uses that selected
    Maya or Unity and, a Line Chart with the two lines for the users that 
    subscribed to Maya or Unity, over time.
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
                                                    answer_id=answer.id,
                                                    series_range = series_range)
            answers_count[answer.answer] = user_answers.count()    
            user_answers_total_count += user_answers.count()
            
        questions_and_total_counts[index_q] = {"text": value["question"],
                                                "count": user_answers_total_count}         
        sorted_answers[index_q] = sorted(answers_count.items(), 
                                                key=lambda x:x[1], reverse=True)

    # Form pairs with questions numbers Ex. [[1, 2], [3, 4], [5]]
    questions_tuples = _get_list_of_tuples_from_list(questions_and_total_counts)
    
    return questions_tuples, questions_and_total_counts, sorted_answers  

#-------------------------------------------------------------------------------
def apprentice_replied_survey_counts(series_range, aggregation):
    """
    Get the count of user who replied the apprentice survey give a time range 
    and an aggregation form.
    """
    
    survey_id = 2
    questions = get_questions_from_survey(survey_id)
    questions_ids = tuple(int(q.id) for q in questions)
    
    string_query = """
        select {% aggregated_date "date" aggregation %} AS mydate, count(distinct(user_id))
        from user_answers
        where question_id in {{ questions_ids }} and {% where_between "date" start_date end_date %}
        group by mydate
        order by mydate"""
        
    return _get_sql_report_data(string_query,'surveys', locals())
     
#===============================================================================
# Forum Database reports

def _get_active_users_over_time(series_range, aggregation):
    """
    Number of active users registered in SideFX website over time
    """
    
    return time_series.time_series(MosUsers.objects.filter(user_active=1).exclude(id=-1),
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
def _get_cumulative_values(initial_total, tuples):
    """
    Get cumulative values. 
    """
    
    if len(tuples) == 0:
        return tuples

    result = []
    total = initial_total
    for date, value in tuples:
        total += value
        result.append([date, total])

    return result

#-------------------------------------------------------------------------------
def _get_sum_values(tuples):
    """
    Get summarised values.  
    """
    return sum(counts for date, counts in tuples)

#-------------------------------------------------------------------------------             
def get_active_users_forum_and_openid(series_range, aggregation,
                                      events_to_annotate ):
    """
    Number of users active that registered with forum or open id
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"

    # To get all users registered in the given interval
    all_users_serie = _get_active_users_over_time(series_range, aggregation)
    
    # Filling with zeros the empty dates in the events
    events_to_annotate = time_series.fill_missing_dates_with_zeros(events_to_annotate, 
                                                 aggregation[:-2], series_range,
                                                 True) 
    
    # Creating the time serie from the results of the cursor
    forum_serie = _get_active_users_by_method_per_day(start_date, end_date) 
    #Filling the empty dates
    forum_serie = time_series.fill_missing_dates_with_zeros(forum_serie, aggregation[:-2],
                                                                  series_range) 
   
    # Creating the time serie from the results of the cursor
    openid_serie = _get_active_users_by_method_per_day(start_date, end_date, 
                                                        openid=True) 
    # Filling the empty dates
    openid_serie = time_series.fill_missing_dates_with_zeros(openid_serie, aggregation[:-2], 
                                                                series_range)
    
    return time_series.merge_time_series([all_users_serie, events_to_annotate, forum_serie,
                                                                  openid_serie])

#-------------------------------------------------------------------------------
def openid_providers_breakdown(series_range, aggregation):
    """
    Breakdown of open id user by providers
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"
        
    total_forum = _get_sum_values(_get_active_users_by_method_per_day(
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
    return time_series.time_series(MachineConfig.objects.filter(asked_to_subscribe=1),
                              'creation_date',series_range, agg=aggregation)

#===============================================================================
# Houdini Licenses and downloads related reports

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
    
    apprentice_activations = [(row[0], row[1]) for row in cursor.fetchall()] 
    
    return time_series.fill_missing_dates_with_zeros(apprentice_activations, 
                                          aggregation[:-2], series_range)

#-------------------------------------------------------------------------------

def get_apprentice_hd_licenses_over_time(series_range, aggregation):
    """
    Get Apprentice HD Licenses generated over time. Line Chart.
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"

    cursor = connections['licensedb'].cursor()
    
    # Not queriying entitlements
    cursor.execute("""
        select cast(CreateDate as datetime)
                          as date, 
               sum(KTokens) as num_licenses
        from Keystrings
        where Product = 'HOUDINI-APPRENTICE-HD' and Disabled = 'N'
            and KType = 'LICENSE'
            and (LicType = 'PURCHASED' or LicType = 'SUBSCRIPTION')
            and CreateDate between date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
            and date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S')
        group by date  
        order by date  
        """.format(start_date.strftime("%Y-%m-%d %H:%M:%S"),
                   end_date.strftime("%Y-%m-%d %H:%M:%S")
                  )
        )  
    
    apprentice_hd_sales = [(row[0], row[1]) for row in cursor.fetchall()] 
    
    return time_series.fill_missing_dates_with_zeros(apprentice_hd_sales, 
                                          aggregation[:-2], series_range)
    
#-------------------------------------------------------------------------------

def get_apprentice_hd_licenses_cumulative(hd_licenses_series, range_start_date):
    """
    Get Apprentice HD Licenses cumulative over time.
    """
    
    cursor = connections['licensedb'].cursor()
    
    cursor.execute("""
        select sum(KTokens) as num_licenses
        from Keystrings
        where Product = 'HOUDINI-APPRENTICE-HD' and Disabled = 'N'
            and KType = 'LICENSE'
            and (LicType = 'PURCHASED' or LicType = 'SUBSCRIPTION')
            and CreateDate <= date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
        """.format(range_start_date.strftime("%Y-%m-%d %H:%M:%S"))
                                     
        )  
    
    cumulative_val = cursor.fetchall()[0][0]
    if cumulative_val is None:
        cumulative_val = 0
        
    return _get_cumulative_values(cumulative_val, hd_licenses_series)

#-------------------------------------------------------------------------------

def get_apprentice_activations_by_geo(series_range):
    """
    Get Apprentice HD Licenses by Geography. Ip address.
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    cursor = connections['licensedb'].cursor()
    
    cursor.execute("""
        select cast(LogDate as datetime) as date, IPAddress
        from NCHistory
        where LogDate between date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
            and date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S') and
            IPAddress IS NOT NULL
        group by date  
        order by date  
        """.format(start_date.strftime("%Y-%m-%d %H:%M:%S"),
                   end_date.strftime("%Y-%m-%d %H:%M:%S")
                  )
        )  
    
    dates_ips = [(row[0], row[1]) for row in cursor.fetchall()] 
    
    lat_longs =  []
    for dates_ip in dates_ips:
        lat_long = get_lat_and_long(dates_ip[1])
        if lat_long is not None:
            lat_longs.append(lat_long)
    
    return lat_longs

#-------------------------------------------------------------------------------

def _return_common_for_download_reports(start_date, end_date):
    # Return common query strings for Houdini download reports
    common_query_start = """
                   select cast(cast(downloads.dls_time as date ) as datetime) as new_date, 
                   count(downloads.id) 
                   from dls_houdini_downloads AS downloads
                   """
    common_query_where = "where " 
    common_query_end = """
    downloads.dls_time between date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
    and date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S')
    group by new_date  
    order by new_date  
    """.format(start_date.strftime("%Y-%m-%d %H:%M:%S"),
               end_date.strftime("%Y-%m-%d %H:%M:%S"))   
    
    return common_query_start, common_query_where, common_query_end 

#-------------------------------------------------------------------------------
def _execute_cursor_query(cursor, common_query_start, join = "", 
                          common_query_where= "", common_query_end= ""):
    
    cursor.execute("{0} {1} {2} {3}"
          .format(common_query_start, join, common_query_where,  
                  common_query_end))
    
    return [(row[0], row[1]) for row in cursor.fetchall()] 

#-------------------------------------------------------------------------------
def _get_all_downloads(cursor, common_query_start, common_query_where, 
                       common_query_end):
    return _execute_cursor_query(cursor, common_query_start, "", 
                                 common_query_where, 
                                 common_query_end)

#-------------------------------------------------------------------------------
def _get_commercial_downloads(cursor, common_query_start, common_query_where,
                              common_query_end):
    
    where = """downloads.apprentice_user_id IS NULL
               and user_id != -1 and   
            """             
    return _execute_cursor_query(cursor, common_query_start, "", 
                              common_query_where + where, common_query_end )

#-------------------------------------------------------------------------------    
def _get_apprentice_downloads(cursor, common_query_start, common_query_where,
                              common_query_end):
    
    middle_join = """
                  inner join dls_apprentice_users AS apprentice 
                  ON downloads.apprentice_user_id = apprentice.id
                  """ 
    where = """
            downloads.apprentice_user_id IS NOT NULL
            and user_id = -1 and  
            """             
    return _execute_cursor_query(cursor, common_query_start, middle_join, 
                                 common_query_where + where, common_query_end ) 
 
#-------------------------------------------------------------------------------  
def get_apprentice_downloads(series_range, aggregation):
    """
    External function to be reused for getting apprentice downloads
    """
    
    if aggregation is None:
        aggregation = "daily"
    
    cursor = connections['mambo'].cursor()
    
    common_query_start, common_query_where, common_query_end = \
                           _return_common_for_download_reports(series_range[0], 
                                                                series_range[1]) 
    # Apprentice downloads    
    apprentice_downloads = _get_apprentice_downloads(cursor, common_query_start, 
                                                     common_query_where,
                                                     common_query_end)
    
    return time_series.fill_missing_dates_with_zeros(apprentice_downloads, 
                                                 aggregation[:-2], series_range)
        
#-------------------------------------------------------------------------------    
def get_num_software_downloads(series_range, aggregation, 
                               events_to_annotate):
    """
    Get num of software downloads through the website per day. 
    """
    start_date = series_range[0] 
    end_date = series_range[1]
    
    if aggregation is None:
        aggregation = "daily"

    cursor = connections['mambo'].cursor()
    
    common_query_start, common_query_where, common_query_end = \
                       _return_common_for_download_reports(start_date, end_date) 
     
    # All downloads
    all_downloads = _get_all_downloads(cursor, common_query_start,
                                       common_query_where,
                                       common_query_end)
    
    # Commercial downloads     
    commercial_downloads = _get_commercial_downloads(cursor, common_query_start, 
                                                     common_query_where,
                                                     common_query_end)
    
    # Apprentice downloads    
    apprentice_downloads = _get_apprentice_downloads(cursor, common_query_start, 
                                                     common_query_where,
                                                     common_query_end)
    
    all_downloads = time_series.fill_missing_dates_with_zeros(all_downloads, 
                                                aggregation[:-2], series_range)
    commercial_downloads = time_series.fill_missing_dates_with_zeros(commercial_downloads, 
                                                aggregation[:-2], series_range)
    apprentice_downloads = time_series.fill_missing_dates_with_zeros(apprentice_downloads, 
                                                 aggregation[:-2], series_range)
    
    return all_downloads, commercial_downloads, apprentice_downloads, \
          time_series.merge_time_series([all_downloads, events_to_annotate, 
                              commercial_downloads, apprentice_downloads])
                                                                                    
#-------------------------------------------------------------------------------
def get_percentage_of_total(total_serie, fraction_serie):
    """
    Get which percentage is each element of a serie from the same element (same date)
    on another serie. Column Chart.
    """  
    
    return time_series.compute_time_series(
        [fraction_serie, total_serie], get_percent)  
    
#-------------------------------------------------------------------------------    
def get_percentage_downloads(all_downloads, apprentice_downloads,
                              commercial_downloads):
    
    apprentice_percentages = get_percentage_of_total(all_downloads, 
                                                      apprentice_downloads)
    commercial_percentages = get_percentage_of_total(all_downloads, 
                                                      commercial_downloads)
    
    return time_series.merge_time_series([commercial_percentages, apprentice_percentages])

   
    
    
