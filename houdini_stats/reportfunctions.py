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

   
def get_apprentice_total_activations(series_range, aggregation):
    """
    Get Apprentice Activations over time.
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
    
