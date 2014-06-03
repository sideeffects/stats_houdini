from houdini_stats.genericreportclasses import *
from houdini_forum.models import *
from operator import *

import houdini_stats.utils             
import houdini_stats.time_series

#===============================================================================
# Common functions for sidefx website reports

@cacheable
def _get_active_users_by_method_per_day(series_range, aggregation, openid=False):
    """
    Get count active users that registered with forum or open id per day, 
    given a period of time. 
    
    Function used from get_active_users_forum_and_openid report.
    """
    
    # If we are looking for the users who logged in with forum, they will be
    # in the most users table, but not on the mos_user_id table. We do a left
    # join
    join_sintax = """LEFT JOIN oid_user_to_mos_user oid 
                     ON u.id = oid.mos_user_id
                     WHERE oid.mos_user_id is NULL AND """
    if openid:
        # We do an inner join, the users which ids are in mos_users and in
        # oid_user_to_mos_user
        join_sintax = """INNER JOIN oid_user_to_mos_user oid 
                         ON u.id= oid.mos_user_id 
                         WHERE """
        
    string_query = """
          select {% aggregated_date "registerDate" aggregation %} AS mydate, 
                 COUNT(u.id) AS user_count
          FROM mos_users u
          {{join_sintax }}
          u.id != -1
          AND u.user_active =1
          AND {% where_between "registerDate" start_date end_date %}     
          AND u.registerDate!= "0000-00-00 00:00:00"      
          GROUP BY mydate
          ORDER BY mydate
          """
     
    return get_sql_data_for_report(string_query, 'mambo', locals())

#-------------------------------------------------------------------------------  

# Global providers list to be used in the reports for users login
PROVIDERS = {
             "forum":{"provider": "", "count": 0},
             "facebook": {"provider": "https://www.facebook.com/", "count": 0},
             "orbolt": {"provider": "https://www.orbolt.com/openid/",
                        "count": 0},
             "gmail": {"provider": "https://www.google.com/accounts/",
                           "count": 0},
             "yahoo": {"provider": "https://open.login.yahooapis.com/openid/", 
                       "count": 0},
             "windowslive": {"provider": "https://profile.live.com/", 
                             "count": 0},
             "linkedin": {"provider": "http://www.linkedin.com/pub/",
                          "count": 0},
             "aol": {"provider": ".aofrom operator import *l", "count": 0}
             }

#-------------------------------------------------------------------------------
@cacheable
def _get_all_openid_providers(series_range, aggregation):
    """
    Get all open id provider with which users ha registered.
    """
    string_query = """
             SELECT {% aggregated_date "u.registerDate" aggregation %} AS mydate,
                    provider_url 
             FROM oid_user_to_mos_user a
             INNER JOIN mos_users u ON a.mos_user_id = u.id  
             WHERE 
             u.id = a.mos_user_id
             AND {% where_between "u.registerDate" start_date end_date %}  
             AND u.registerDate!= "0000-00-00 00:00:00"      
             """
     
    return get_sql_data_for_report(string_query, 'mambo', locals(), 
                                   fill_zeros = False)

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

def _get_total_active_users_forum(series_range, aggregation):
    """
    Get total number of users who logged in with forum.
    """
    forum_series = _get_active_users_by_method_per_day(series_range, aggregation)
    
    return sum(counts for date, counts in forum_series)

#------------------------------------------------------------------------------- 
        
class NewUserRegistrationsOverTime(ChartReport):
    """
    New user registrations over time. Line Chart.
    """  
    
    def name(self):
        return "new_registrations_over_time"

    def title(self):
        return "New User Registrations Over Time"

    def get_data(self, series_range, aggregation):
        """
        Number of users active that registered with forum or open id.
        """
        
        # To get all users registered in the given interval
        all_users_series = get_orm_data_for_report(
                                       MosUsers.objects.filter(
                                       user_active=1).exclude(id=-1), 
                                      'registerdate', series_range, aggregation)
    
        # Get events to annotate
        events_to_annotate = get_events_in_range(series_range, aggregation) 
        
        # Creating the time serie from the results of the cursor
        forum_series = _get_active_users_by_method_per_day(series_range, 
                                                           aggregation) 
        # Creating the time serie from the results of the cursor
        openid_series = _get_active_users_by_method_per_day(series_range, 
                                                            aggregation, 
                                                            openid=True) 
        # Return all the series merged
        return time_series.merge_time_series([all_users_series, 
                                              events_to_annotate,
                                              forum_series, 
                                              openid_series])
    
    def chart_aditional_information_below(self):
        return '''<p>* Users who registered and then later logged in using 
                  OpenID will show up as OpenID registrations.</p>
               '''     
    
    def chart_columns(self):
        return """
          {% col "string" "Date" %}
            {% show_annotation_title events val %} 
          {% endcol %}
          {% col "number" "Total Users Registered" %}{{ val }}{% endcol %}
          {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
          {% col "number" "Total Users Registered with Forum" %}
             {{ val }}
          {% endcol %}
          {% col "number" "Total Users Registered with Openid" %}
             {{ val }}
          {% endcol %}
        """

    def chart_options(self):
        return '"opt_count_with_legend"' 
    

    
#------------------------------------------------------------------------------- 
 # TODO: Verify in more details the results of this report       
class BreakdownRegistrationsMethods(ChartReport):
    """
    Breakdown of registration methods for the selected period of time.
    Column Chart.
    """  
    
    total_forum_registrations = 0
    total_open_id_registrations = 0
    
    def name(self):
        return "breakdown_registrations_methods"

    def title(self):
        return '''Breakdown of registration methods for the selected period 
                  of time'''

    def get_data(self, series_range, aggregation):
        """
        Breakdown of open id user by providers
        """
        self.total_forum_registrations = _get_total_active_users_forum(
                                                      series_range, aggregation)
        PROVIDERS["forum"]["count"] = self.total_forum_registrations
    
        all_openid_providers = [provider[1] for provider in _get_all_openid_providers(
                                                    series_range, aggregation)]
    
        self.total_open_id_registrations = _get_total_active_openid(all_openid_providers)
        
        return [(key.title(),value["count"]) for key, value in \
                                self._get_sorted_openid_providers_list_trans()]
    
    def _get_sorted_openid_providers_list_trans(self):
        """
        Sort providers by count descendent order
        """
        return sorted(PROVIDERS.items(), key=lambda x:getitem(x[1],'count'), 
                                                                  reverse=True) 
    def chart_aditional_information_above(self):
        return '''<div>
                  <br>
                  <span> &nbsp;&nbsp;&nbsp;&nbsp; 
                  Total of user registered with forum: ''' + \
                    str(self.total_forum_registrations) + '''</span>  
                  <span> &nbsp;&nbsp;&nbsp;&nbsp; 
                         Total of user registered with openid: ''' +  \
                         str(self.total_open_id_registrations)  + ''' </span>   
                  </div>
               '''     
    
    def chart_columns(self):
        return """
           {% col "string" "Provider" %}"{{ val }}"{% endcol %}
           {% col "number" "# of users registered" %}{{ val }}{% endcol %}
        """

    def chart_options(self):
        return '"opt_count_wide_column"' 
             