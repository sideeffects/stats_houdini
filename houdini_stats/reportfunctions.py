from houdini_stats.models import *
from houdini_licenses.models import *
from houdini_surveys.models import *
from houdini_forum.models import *

from django.db import connections
from django.db.models import Avg, Sum, Count
from django.db.models import get_model
from django.template import Context, Template

from collections import defaultdict
import datetime
from dircache import annotate
from operator import *

import utils             
import time_series 

#===============================================================================

def _get_cursor(db_name):
    """
    Given a db name returns a cursor.
    """
    return connections[db_name].cursor()

#-------------------------------------------------------------------------------
def _get_sum_values(tuples):
    """
    Get summarised values.  
    """
    return sum(counts for date, counts in tuples)

#-------------------------------------------------------------------------------
def get_events_in_range(series_range, aggregation, fill_empty_string = True):
    """
    Get all the events in the give time period. Return the results as a time
    serie [date, event_name]
    """
    
    string_query = """
        select {% aggregated_date "date" aggregation %} AS mydate, 
               group_concat(title separator ', ') AS my_title
        from houdini_stats_event
        where {% where_between "date" start_date end_date %}
        group by mydate
        order by mydate"""
    
    return get_sql_data_for_report(string_query,'stats', locals(),
                                   fill_zeros = False, 
                                   fill_empty_string = fill_empty_string)

#-------------------------------------------------------------------------------
def get_sql_data_for_report(string_query, db_name, context_vars, 
                            fill_zeros = True, fill_empty_string = False):
    """
    Generic function to get data for reports, doing sql queries using a cursor.
    
    This func will receive the string with the query, the database name to 
    create a cursor and the context vars using in the query.
    
    Explanation of the last 3 params:
    
    1. fill_zeros:  For time series the dates that have no value will be filled 
    with zeros. 
    
    Sometimes we want to execute a query but the query wont retrieve datetimes,
    it wont be a time series, but different kind of data. For example data used 
    for pie charts, for this cases we set fill_zeros= False so that we don't
    treat the data as time series.
    
    2. fill_empty_string: sometimes we want to fill with an empty string 
    instead of with zeros
    """
    
    context_vars = context_vars.copy()
    
    context_vars["start_date"] = context_vars['series_range'][0] 
    context_vars["end_date"] = context_vars['series_range'][1]
    
    cursor = _get_cursor(db_name)
    tpl_header =  "{% load reports_tags %} "
         
    tpl = Template(tpl_header + string_query)
    
    cursor.execute(tpl.render(Context(context_vars)), [])
    
    #print tpl.render(Context(context_vars))
    
    series = [(row[0], row[1]) for row in cursor.fetchall()]
    
    
    if not fill_zeros and fill_empty_string:
        return time_series.fill_missing_dates_with_zeros(series,
                                              context_vars['aggregation'][:-2], 
                                              context_vars['series_range'],
                                              True) 
    if not fill_zeros:
        return series
    
        
    return time_series.fill_missing_dates_with_zeros(series,
                                              context_vars['aggregation'][:-2], 
                                              context_vars['series_range'])  


#-------------------------------------------------------------------------------
def get_orm_data_for_report(query_set, time_field, series_range, 
                            aggregation = None, func = None):
    """
    Generic function to get data for reports, using django orm for the queries.
    
    This function will receive the queryset, the name of the time field to be 
    passed to the time series function, the series range, the aggregation and 
    the function to be passed for aggregation in the time series.    
    """
    
    return time_series.time_series(query_set, time_field, 
                                   series_range, func, aggregation)
     
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
    
    users_for_maya, users_for_unity, count_total = \
                                          _get_common_for_hou_engine_breakdown()
    
    users_count = [("Maya | Unity", users_for_maya.count(), 
                                    users_for_unity.count())]
    
    users_over_time = time_series.merge_time_series(
                                          time_series.get_time_series_sequences(
                                              [users_for_maya, users_for_unity],
                                              interval= series_range, 
                                              aggregation= aggregation,
                                              date_field ="date"))
    
    return {"count_total": count_total, 
            "user_answers_count" : users_count, 
            "user_answers_over_time": users_over_time }

#-------------------------------------------------------------------------------

def _get_common_for_apprentice_followup_survey():
            
    survey_id = 2
    questions =  get_questions_from_survey(survey_id, 8)
    
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
    questions_tuples = utils.get_list_of_tuples_from_list(
                                                    questions_and_total_counts)
    
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
        select {% aggregated_date "date" aggregation %} AS mydate, 
               count(distinct(user_id))
        from user_answers
        where question_id in {{ questions_ids }} and 
              {% where_between "date" start_date end_date %}
        group by mydate
        order by mydate"""
        
    return get_sql_data_for_report(string_query,'surveys', locals())
     
#===============================================================================
# Side Effects Website reports

def get_active_users_by_method_per_day(series_range, aggregation, openid=False):
    """
    Get count active users that registered with forum or open id per day, 
    given a period of time. 
    
    Function used from get_active_users_forum_and_openid report.
    """
    
    to_compare = "= u.id"
    if openid:
        to_compare = "IS NULL"
        
    string_query = """
          select {% aggregated_date "registerDate" aggregation %} AS mydate, 
                 COUNT(u.id) AS user_count
          FROM mos_users u
          JOIN oid_user_to_mos_user a ON a.mos_user_id = u.id
          WHERE u.id != -1
          AND u.user_active =1
          AND {% where_between "registerDate" start_date end_date %}     
          AND u.registerDate!= "0000-00-00 00:00:00"      
          AND a.mos_user_id {{ to_compare }}
          GROUP BY mydate
          ORDER BY mydate
          """
     
    return get_sql_data_for_report(string_query, 'mambo', locals())

#-------------------------------------------------------------------------------             
def get_active_users_forum_and_openid(series_range, aggregation,
                                      events_to_annotate ):
    """
    Number of users active that registered with forum or open id.
    """
    
    # To get all users registered in the given interval
    all_users_series = get_orm_data_for_report(
                          MosUsers.objects.filter(user_active=1).exclude(id=-1), 
                          'registerdate', series_range, aggregation)
    
    # Filling with zeros the empty dates in the events
    events_to_annotate = time_series.fill_missing_dates_with_zeros(
                                          events_to_annotate, aggregation[:-2], 
                                                            series_range, True) 
    
    # Creating the time serie from the results of the cursor
    forum_series = get_active_users_by_method_per_day(series_range, aggregation) 
    
    # Creating the time serie from the results of the cursor
    openid_series = get_active_users_by_method_per_day(series_range, aggregation, 
                                                        openid=True) 
    # Return all the series merged
    return time_series.merge_time_series([all_users_series, events_to_annotate,
                                          forum_series, openid_series])


#-------------------------------------------------------------------------------
# Global providers list to be used in the reports for users login
PROVIDERS = {
             "forum":{"provider": "", "count": 0},
             "facebook": {"provider": "https://www.facebook.com/", "count": 0},
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
             "aol": {"provider": ".aofrom operator import *l", "count": 0}
             }

#-------------------------------------------------------------------------------
def _get_total_active_users_forum(series_range, aggregation):
    """
    Get total number of users who logged in with forum.
    """
    forum_series = get_active_users_by_method_per_day(series_range, aggregation)
    
    return sum(counts for date, counts in forum_series)

#-------------------------------------------------------------------------------    
def _get_total_active_openid(all_openid_providers):    
    """
    Get total number of users who logged in with openid. 
    """
    
    total_openid = 0  
    for provider in all_openid_providers:
        # Always increase total_openid count
        total_openid +=1
        
        if PROVIDERS["facebook"]["provider"] in provider:
            PROVIDERS["facebook"]["count"] +=1 
        
        elif PROVIDERS["gmail"]["provider"] in provider:
            PROVIDERS["gmail"]["count"] +=1
            
        elif PROVIDERS["yahoo"]["provider"] in provider:
            PROVIDERS["yahoo"]["count"] +=1
            
        elif PROVIDERS["orbolt"]["provider"] in provider:
            PROVIDERS["orbolt"]["count"] +=1
            
        elif PROVIDERS["windowslive"]["provider"] in provider:
            PROVIDERS["windowslive"]["count"] +=1
            
        elif PROVIDERS["linkedin"]["provider"] in provider:
            PROVIDERS["linkedin"]["count"] +=1
            
        elif PROVIDERS["aol"]["provider"] in provider:
            PROVIDERS["aol"]["count"] +=1
            
    return total_openid 
#-------------------------------------------------------------------------------
def _get_sorted_openid_providers_list():     
    """
    Sort providers by count descendent order
    """
     
    return sorted(PROVIDERS.items(), key=lambda x:getitem(x[1],'count'), 
                             reverse=True) 
    
#-------------------------------------------------------------------------------
def get_all_openid_providers(series_range, aggregation):
    """
    Get all open id provider with which users ha registered.
    """
    string_query = """
             SELECT {% aggregated_date "u.registerDate" aggregation %} AS mydate,
                    provider_url 
             FROM oid_user_to_mos_user a
             LEFT JOIN mos_users u ON u.id = a.mos_user_id 
             WHERE 
             {% where_between "u.registerDate" start_date end_date %}  
             AND u.registerDate!= "0000-00-00 00:00:00"      
             AND u.id = a.mos_user_id
             """
     
    return get_sql_data_for_report(string_query, 'mambo', locals(), 
                                   fill_zeros = False)

#-------------------------------------------------------------------------------

def openid_providers_breakdown(series_range, aggregation):
    """
    Breakdown of open id user by providers
    """
    
    start_date = series_range[0] 
    end_date = series_range[1]
    
    total_forum = _get_total_active_users_forum(series_range, aggregation)
    PROVIDERS["forum"]["count"] = total_forum
    
    all_openid_providers = [provider[1] for provider in get_all_openid_providers(
                                                    series_range, aggregation)]
    
    total_openid = _get_total_active_openid(all_openid_providers)
    sorted_providers = _get_sorted_openid_providers_list()
    
    return [(key.title(),value["count"]) for key, value in sorted_providers], \
            total_forum, total_openid 

#===============================================================================
# Houdini Licenses and downloads related reports

def apprentice_new_activations_over_time(series_range, aggregation):
    """
    Get Apprentice Activations over time. Line Chart.
    """
    
    nc_custid = 2711
    
    string_query = """
        select {% aggregated_date "activation_date" aggregation %} AS mydate, 
               count(*) as num_activated
        from (
            select from_days(min(to_days(Keystrings.CreateDate))) as 
                       activation_date 
                from Servers, Keystrings
                where Servers.CustID='{{ nc_custid }}'
                and Servers.ServerID=Keystrings.ServerID
                and Keystrings.KType='LICENSE'
                group by Servers.ServerID
        ) as TempTable
        where {% where_between "activation_date" start_date end_date %}
        group by mydate  
        order by mydate  
       """
        
    return get_sql_data_for_report(string_query,'licensedb', locals())    

#-------------------------------------------------------------------------------

def apprentice_total_activations_over_time(series_range, aggregation):
    """
    Get Apprentice Activations over time. Line Chart.
    """
    
    nc_custid = 2711
    
    string_query = """
        select {% aggregated_date "activation_date" aggregation %} AS mydate, 
               count(*) as num_activated
        from (
            select cast(cast(CreateDate as date) as datetime) as 
                       activation_date 
                from Servers, Keystrings
                where Servers.CustID='{{ nc_custid }}'
                and Servers.ServerID=Keystrings.ServerID
                and Keystrings.KType='LICENSE'
                group by Servers.ServerID, activation_date 
        ) as TempTable
        where {% where_between "activation_date" start_date end_date %}
        group by mydate  
        order by mydate  
       """
        
    return get_sql_data_for_report(string_query,'licensedb', locals())     
#-------------------------------------------------------------------------------

def get_apprentice_hd_licenses_over_time(series_range, aggregation):
    """
    Get Apprentice HD Licenses generated over time. Line Chart.
    """
    
    # Not queriying entitlements
    string_query = """
        select {% aggregated_date "CreateDate" aggregation %} AS mydate, 
               sum(KTokens) as num_licenses
        from Keystrings
        where Product = 'HOUDINI-APPRENTICE-HD' and Disabled = 'N'
            and KType = 'LICENSE'
            and (LicType = 'PURCHASED' or LicType = 'SUBSCRIPTION')
            and {% where_between "CreateDate" start_date end_date %}
        group by mydate  
        order by mydate  
       """
        
    return get_sql_data_for_report(string_query,'licensedb', locals())   
    
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

def get_apprentice_activations_by_geo(series_range, aggregation):
    """
    Get Apprentice HD Licenses by Geography. Ip address.
    Heatmap report.
    """

    string_query = """
        select cast(cast(Keystrings.CreateDate AS date) AS datetime) AS mydate, IPAddress
        from NCHistory, Keystrings, Servers
        where NCHistory.KSID=Keystrings.KSID
            and Keystrings.ServerID=Servers.ServerID
            and {% where_between "Keystrings.CreateDate" start_date end_date %} 
        group by Servers.ServerID, mydate
        """

    dates_ips = get_sql_data_for_report(string_query,'licensedb', locals())  
    
    lat_longs =  []
    for dates_ip in dates_ips:
        lat_long = utils.get_lat_and_long(dates_ip[1])
        if lat_long is not None:
            lat_longs.append(lat_long)
    
    return lat_longs

#-------------------------------------------------------------------------------
def _get_data_for_houdini_download_reports(series_range, aggregation, 
                                          sql_where_statement='',
                                          sql_join_statement=''):
    """
    Get data for download reports, total downloads, commercial and apprentice
    will use this same function.
    """
    
    string_query = """
         select {% aggregated_date 'downloads.dls_time' aggregation %} AS mydate, 
                count(downloads.id)
         from dls_houdini_downloads AS downloads
         {{ sql_join_statement }}
         where {% where_between 'downloads.dls_time' start_date end_date %}  
         {{ sql_where_statement }}
         group by mydate  
         order by mydate
        """
    
    return get_sql_data_for_report(string_query,'mambo', locals()) 
 
#------------------------------------------------------------------------------- 
def get_all_houdini_downloads(series_range, aggregation):
    """
    Get all downloads
    """
    return _get_data_for_houdini_download_reports(series_range, aggregation)

#-------------------------------------------------------------------------------  

def get_houdini_apprentice_downloads(series_range, aggregation):
    """
    Get apprentice downloads
    """
    sql_join_statement = """
                  inner join dls_apprentice_users AS apprentice 
                  ON downloads.apprentice_user_id = apprentice.id
                  """ 
    sql_where_statement = """
            and downloads.apprentice_user_id IS NOT NULL
            and user_id = -1   
            """                          
    return _get_data_for_houdini_download_reports(series_range, aggregation,
                                       sql_where_statement, sql_join_statement) 
    
#------------------------------------------------------------------------------- 
def get_houdini_commercial_downloads(series_range, aggregation):
    """
    Get commercial downloads
    """
    
    sql_where_statement = """and downloads.apprentice_user_id IS NULL 
                             and user_id != -1"""  
    return _get_data_for_houdini_download_reports(series_range, 
                                               aggregation, sql_where_statement)

#-------------------------------------------------------------------------------    
def get_merge_houdini_downloads(all_downloads, apprentice_downloads, 
                                      commercial_downloads, events_to_annotate):
    """
    Get a time series with a merfe of all the houdini downloads, and the event
    to anootate. These stats are houdini downloads through the website per day. 
    """
    return time_series.merge_time_series([all_downloads, events_to_annotate, 
                              commercial_downloads, apprentice_downloads])
                                                                                    
#-------------------------------------------------------------------------------
def get_percentage_of_total(total_serie, fraction_serie):
    """
    Get which percentage is each element of a serie from the same element 
    (same date) on another serie. Column Chart.
    """      
    return time_series.compute_time_series(
        [fraction_serie, total_serie], utils.get_percent)  

#-------------------------------------------------------------------------------
def get_difference_between_series(series1, series2):
    """
    Get the difference between the numbers in two time series. Column Chart.
    """      
    return time_series.compute_time_series(
        [series1, series2], utils.get_difference)  
    
#-------------------------------------------------------------------------------    
def get_percentage_two_series_one_total(series_total, series1, series2):
    
    series1_percentages = get_percentage_of_total(series_total, 
                                                      series1)
    series2_percentages = get_percentage_of_total(series_total, 
                                                      series2)
    
    return time_series.merge_time_series([series1_percentages, 
                                          series2_percentages])

   
    
    
