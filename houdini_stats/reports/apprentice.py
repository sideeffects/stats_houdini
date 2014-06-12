from houdini_stats.genericreportclasses import *
from downloads import *

import houdini_stats.utils             
import houdini_stats.time_series

#===============================================================================
# Common query functions

@cacheable
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

#-------------------------------------------------------------------------------

@cacheable
def get_apprentice_new_activations(series_range, aggregation):
    """
    Get Apprentice Activations over time. 
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

@cacheable
def get_apprentice_reactivations(total_activations, new_activations):
    """
    Get Apprentice Re-activations over time. 
    """
    
    return time_series.get_difference_between_series(total_activations, 
                                                     new_activations)
    
#-------------------------------------------------------------------------------    
@cacheable
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
@cacheable
def get_apprentice_hd_licenses_cumulative(hd_licenses_series, range_start_date):
    """
    Get Apprentice HD Licenses cumulative over time.
    """
    
    cursor =  houdini_stats.genericreportclasses._get_cursor('licensedb')
    
    string_query = """
        select sum(KTokens) as num_licenses
        from Keystrings
        where Product = 'HOUDINI-APPRENTICE-HD' and Disabled = 'N'
            and KType = 'LICENSE'
            and (LicType = 'PURCHASED' or LicType = 'SUBSCRIPTION')
            and CreateDate <= date_format('{0}', '%%Y-%%c-%%d %%H:%%i:%%S')
        """.format(range_start_date.strftime("%Y-%m-%d %H:%M:%S"))
    cursor.execute(string_query, [])
    
    cumulative_val = cursor.fetchall()[0][0]
    if cumulative_val is None:
        cumulative_val = 0
        
    return _get_cumulative_values(cumulative_val, hd_licenses_series)

    
#-------------------------------------------------------------------------------

class ApprenticeActivationsVsDownloads(ChartReport):
    """
    Apprentice Activations Vs Apprentice Downloads. Line Chart.
    """  
    def name(self):
        return "app_activations_vs_downloads"

    def title(self):
        return "Apprentice Activations vs Apprentice Downloads"

    def get_data(self, series_range, aggregation):
        
        apprentice_total_activations = get_apprentice_total_activations(
                                           series_range, aggregation) 
        apprentice_new_activations = get_apprentice_new_activations(
                                          series_range, aggregation) 
        apprentice_reactivations = get_apprentice_reactivations(
                                       apprentice_total_activations,
                                       apprentice_new_activations)
        
        return time_series.merge_time_series([
                   apprentice_total_activations, 
                   get_events_in_range(series_range, aggregation), 
                   apprentice_new_activations,
                   apprentice_reactivations,                   
                   get_hou_apprentice_downloads(series_range, aggregation)])
        
    def chart_columns(self):
        return """
           {% col "string" "Date" %}
              {% show_annotation_title events val %} 
           {% endcol %}
            
           {% col "number" "Apprentice Total Activations (including reactivations)" %}
              {{ val }}
           {% endcol %}
           {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
           {% col "number" "NEW Apprentice Activations" %}{{ val }}{% endcol %}
           {% col "number" "Apprentice Reactivations" %}{{ val }}{% endcol %}
           {% col "number" "Apprentice Downloads" %}{{ val }}{% endcol %}
        """

    def chart_options(self):
        return '"opt_count_with_legend"'


#------------------------------------------------------------------------------- 
    
class ApprenticeActivationsAndReactivationsPercentages(ChartReport):
    """
    Percentage of new apprentice activations and re-activations from total
    activations. Column Chart.
    """  
    
    def name(self):
        return "new_apprentice_activations_reactivations_percentages"

    def title(self):
        return "Percentage of NEW Apprentice Activations and Reactivations"

    def get_data(self, series_range, aggregation):
        
        apprentice_total_activations = get_apprentice_total_activations(
                                           series_range, aggregation) 
        apprentice_new_activations = get_apprentice_new_activations(
                                          series_range, aggregation) 
        apprentice_reactivations = get_apprentice_reactivations(
                                       apprentice_total_activations,
                                       apprentice_new_activations)
      
        return time_series.merge_percentage_two_series_one_total(
                                                  apprentice_total_activations,
                                                  apprentice_new_activations, 
                                                  apprentice_reactivations)    
    def chart_columns(self):
        return """
         {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
         {% col "number" "% of NEW Apprentice Activations" %}{{ val }}{% endcol %}
         {% col "number" "% of Apprentice Reactivations" %}{{ val }}{% endcol %}
     """

    def chart_options(self):
        return '"opt_count_percentage_column"'
    
    
#------------------------------------------------------------------------------- 
    
class PercentagesApprenticeNewActivationsFromApprenticeDownloads(ChartReport):
    """
    Percentage of new apprentice activations from apprentice downloads.
    Column Chart.
    """  
    
    def name(self):
        return "percentages_new_apprentice_activations_from_downloads"

    def title(self):
        return """Percentage of NEW Apprentice Activations from Apprentice 
               Downloads"""

    def get_data(self, series_range, aggregation):
        
        return time_series.get_percentage_from_total(
                   get_hou_apprentice_downloads(series_range, aggregation), 
                   get_apprentice_new_activations(series_range, aggregation))
        
    def chart_columns(self):
        return """
         {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
         {% col "number" "% of NEW Apprentice Activations" %}{{ val }}{% endcol %}
        """

    def chart_options(self):
        return '"opt_count_percentage_column"' 
     
#------------------------------------------------------------------------------- 

class ApprenticeHdLicensesOverTime(ChartReport):
    """
    Apprentice Activations Hd Licenses OverTime. Line Chart.
    """  
    def name(self):
        return "apprentice_hd_licenses"

    def title(self):
        return "Apprentice HD Licenses"

    def get_data(self, series_range, aggregation):
        
        return time_series.merge_time_series([
                get_apprentice_hd_licenses_over_time(series_range, aggregation), 
                get_events_in_range(series_range, aggregation)]) 
                   
    def chart_columns(self):
        return """
           {% col "string" "Date" %}
              {% show_annotation_title events val %} 
           {% endcol %}
           {% col "number" "# of Apprentice HD Licenses" %}{{ val }}{% endcol %}
           {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
        """

    def chart_options(self):
        return '"opt_count_wide"'
    
#------------------------------------------------------------------------------- 

class ApprenticeHdCumulativeLicensesOverTime(ChartReport):
    """
    Apprentice Activations Hd Cumulative Licenses OverTime. Area Chart.
    """  
    def name(self):
        return "apprentice_hd_cumulative_licenses"

    def title(self):
        return "Cumulative Apprentice HD Licenses"

    def get_data(self, series_range, aggregation):
        
        return get_apprentice_hd_licenses_cumulative(
                 get_apprentice_hd_licenses_over_time(series_range, aggregation), 
                 series_range[0])
        
    def chart_columns(self):
        return """
            {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
            {% col "number" "# of Apprentice HD Licenses Cumulative" %}
               {{ val }}
            {% endcol %}
        """

    def chart_options(self):
        return '"opt_count_area_wide"'    

#------------------------------------------------------------------------------- 

class ApprenticeActivationsHeatmap(HeatMapReport):
    """
    Apprentice Activations. Heatmap.
    """  
    def name(self):
        return "apprentice_activations_heatmap"

    def title(self):
        return "Apprentice Activations (including reactivations) Heatmap"

    def get_data(self, series_range, aggregation):
                
        string_query = """
        select cast(cast(Keystrings.CreateDate AS date) AS datetime) AS mydate, IPAddress
        from NCHistory, Keystrings, Servers
        where NCHistory.KSID=Keystrings.KSID
            and Keystrings.ServerID=Servers.ServerID
            and {% where_between "Keystrings.CreateDate" start_date end_date %} 
        group by Servers.ServerID, mydate
        """
        ip_addresses = get_sql_data_for_report(string_query,'licensedb', locals())
        
        return  self._get_lat_long_trans(ip_addresses)
    
    def _get_lat_long_trans(self, ip_addresses):
        """
        From the ip addressed by date, get the latitudes and longitudes.
        """
       
        lat_longs =  []
        for ip_address in ip_addresses:
            lat_long = houdini_stats.utils.get_lat_and_long(ip_address[1])
            if lat_long is not None:
                lat_longs.append(lat_long)
        return lat_longs
    