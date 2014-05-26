from houdini_stats.genericreportclasses import *
from houdini_stats.models import *

import houdini_stats.utils             
import houdini_stats.time_series

#===============================================================================

# Common query functions

def _get_data_for_hou_download_reports(series_range, aggregation, 
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
@cacheable
def get_all_hou_downloads(series_range, aggregation):
    """
    Get all downloads
    """
    return _get_data_for_hou_download_reports(series_range, aggregation)

#-------------------------------------------------------------------------------  
@cacheable
def get_hou_apprentice_downloads(series_range, aggregation):
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
    return _get_data_for_hou_download_reports(series_range, aggregation,
                                       sql_where_statement, sql_join_statement) 
    
#------------------------------------------------------------------------------- 
@cacheable
def get_hou_commercial_downloads(series_range, aggregation):
    """
    Get commercial downloads
    """
    
    sql_where_statement = """and downloads.apprentice_user_id IS NULL 
                             and user_id != -1"""  
    return _get_data_for_hou_download_reports(series_range, 
                                               aggregation, sql_where_statement)

#------------------------------------------------------------------------------- 
class HoudiniDownloadsOverTime(ChartReport):
    """
    Houdini Downloads over time. Line Chart.
    """  
    def name(self):
        return "hou_downloads_over_time"

    def title(self):
        return "Houdini Downloads Over Time"

    def get_data(self, series_range, aggregation):
       
        return time_series.merge_time_series([
                       get_all_hou_downloads(series_range, aggregation), 
                       get_events_in_range(series_range, aggregation), 
                       get_hou_commercial_downloads(series_range, aggregation), 
                       get_hou_apprentice_downloads(series_range, aggregation)])
        
    def chart_columns(self):
        return """
         {% col "string" "Date" %}
            {% show_annotation_title events val %} 
         {% endcol %}
            
         {% col "number" "Total Downloads" %}{{ val }}{% endcol %}
         {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
         {% col "number" "Houdini Commercial Downloads" %}{{ val }}{% endcol %}
         {% col "number" "Houdini Apprentice Downloads" %}{{ val }}{% endcol %}
        """

    def chart_options(self):
        return '"opt_count_with_legend"'
    
#------------------------------------------------------------------------------- 
    
class CommercialVsApprenticeDownloadsInPercentages(ChartReport):
    """
    Percentage of Commercial and Apprentice Downloads from the total. 
    Column Chart.
    """  
    
    def name(self):
        return "commercial_vs_apprentice_downloads_percentages"

    def title(self):
        return "Commercial vs Apprentice Downloads"

    def get_data(self, series_range, aggregation):
        
        commercial_percentages = time_series.get_percentage_from_total(
                        get_all_hou_downloads(series_range, aggregation), 
                        get_hou_commercial_downloads(series_range, aggregation))
        
        apprentice_percentages = time_series.get_percentage_from_total(
                        get_all_hou_downloads(series_range, aggregation), 
                        get_hou_apprentice_downloads(series_range, aggregation))
    
        return time_series.merge_time_series([commercial_percentages, 
                                              apprentice_percentages])
        
    def chart_columns(self):
        return """
    {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
    {% col "number" "% of Houdini Commercial Downloads" %}{{ val }}{% endcol %}
    {% col "number" "% of Houdini Apprentice Downloads" %}{{ val }}{% endcol %}
   """

    def chart_options(self):
        return '"opt_count_percentage_column"'  
    
