from stats_main.genericreportclasses import *
import stats_main.utils             
import stats_main.time_series 

from django.db.models import Avg, Sum, Count
from collections import defaultdict
from houdini_stats.models import *


#===============================================================================
# Houdini Usage Report Classes

class HoudiniStatsReport(ChartReport):
    """
    Class to represent all reports with data obtained from inside Houdini.
    """
    
    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE
#-------------------------------------------------------------------------------
    
class NewMachinesOverTime(HoudiniStatsReport):
    """
    New machines subscribed to Stats over time. Area Chart.
    """  
    def name(self):
        return "new_machines_over_time"

    def title(self):
        return "Number of New Machines Subscribed"

    def get_data(self, series_range, aggregation):
        # Observation: When aggregating different dates the query don't take  
        # into account that the machine configs might have been inserted to the  
        # DB in an earlier period of time and counts machine configs that might 
        # have been inserted earlier, since the distinct operator just do the 
        # lookup in the given time range. 
        string_query = """
        select {% aggregated_date "min_creation_date" aggregation %} AS mydate, 
               count(machines_count)
        from(  
            select min(str_to_date(date_format(creation_date, '%%Y-%%m-%%d'),
                                                                '%%Y-%%m-%%d')) 
                   as min_creation_date,
                   count(distinct machine_id) as machines_count 
            from houdini_stats_machineconfig
            where {% where_between "creation_date" start_date end_date %}
            group by machine_id
            order by min_creation_date)
        as TempTable
        group by mydate
        order by mydate"""

        return get_sql_data_for_report(string_query,'stats', locals())
    
    def chart_aditional_message(self):
        return "{% include 'hou_reports_message.html' %}" 
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "# of new machines" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_area_wide"'

#-------------------------------------------------------------------------------

class MachinesActivelySendingStats(HoudiniStatsReport):
    """
    How many machines are actively sending stats. Area Chart.
    """
    def name(self):
        return "machines_actively_sending_stats"

    def title(self):
        return "Number of Machines Actively Sending Stats"

    def get_data(self, series_range, aggregation):
        string_query = """
            select mydate, count( distinct machine )
            from (
            select {% aggregated_date "u.date" aggregation %} AS mydate, 
                   mc.machine_id AS machine
            from houdini_stats_uptime u, houdini_stats_machineconfig mc
            where mc.id = u.machine_config_id
            and {% where_between "u.date" start_date end_date %}
            ORDER BY u.date
            ) as tempTable
            GROUP BY mydate
            ORDER BY mydate  
            """
        return get_sql_data_for_report(string_query,'stats', locals())
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "# of machines " %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_area_wide"'

#-------------------------------------------------------------------------------

class AvgNumConnectionsFromSameMachine(HoudiniStatsReport):
    """
    Average number of individual successful connections from the same machine.
    Column Chart.
    """  
    def name(self):
        return "avg_num_conn_from_same_machine"

    def title(self):
        return "Average Num of Individual Connections From the Same Machine "

    def get_data(self, series_range, aggregation):
        #TO IMPROVE (YB): Take into account the connections that resulted into 
        # crashes, which means take the crashes table into account too, to compute 
        # the results for the average (Maybe doing a merge using Panda?). 
        
        string_query = """
             select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_records)
             from (
                 select machine_config_id,
                 str_to_date(date_format(date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') 
                 as day,
                 count(machine_config_id) as total_records
                 from houdini_stats_uptime
                 where {% where_between "date" start_date end_date %}
                 group by machine_config_id, day
             ) as TempTable
             group by mydate
             order by mydate"""
        
        return get_sql_data_for_report(string_query,'stats', locals())      
        
    def chart_columns(self):
        return """
         {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
         {% col "number" "Avg # of connections" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_wide_column"'

#===============================================================================
# Houdini Uptime Report Classes

class AverageSessionLength(HoudiniStatsReport):
    """
    Houdini average session length. Column Chart.
    """
    def name(self):
        return "average_session_lenght"

    def title(self):
        return "Average Session Lenght (in hours)"

    def get_data(self, series_range, aggregation):
        
        series = get_orm_data_for_report(Uptime.objects.all(), 'date', 
                     series_range, aggregation, func=Avg("number_of_seconds"))

        # Transform the result from seconds into the proper time unit.
        return time_series.choose_unit_from_multiple_time_units_series(
           time_series.compute_time_serie(
               series, stats_main.utils.seconds_to_multiple_time_units), 
                                                                      "hours") 

    def chart_columns(self):
        return """
       {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
       {% col "number" "# of hours" %}{{ val }}{% endcol %}
       """
    
    def chart_aditional_message(self):
        return "{% include 'hou_reports_message.html' %}" 
    
    def chart_options(self):
        return '"opt_count_wide_column"'

#------------------------------------------------------------------------------- 
   
class AverageUsageByMachine(HoudiniStatsReport):
    """
    Houdini average usage by machine. Column Chart.
    """
    def name(self):
        return "average_usage_by_machine"

    def title(self):
        return "Average Usage by Machine (in hours)"

    def get_data(self, series_range, aggregation):
        string_query = """
             select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_seconds)
             from (
                 select machine_config_id,
                 str_to_date(date_format(date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d')
                    as day,
                 sum(number_of_seconds) as total_seconds
                 from houdini_stats_uptime
                 where {% where_between "date" start_date end_date %}
                 group by machine_config_id, day
             ) as TempTable
             group by mydate
             order by mydate"""

        # Transform the result from seconds into the proper time unit.
        return time_series.seconds_to_time_unit_series(
            get_sql_data_for_report(string_query, 'stats', locals()), 
            "hours")

    def chart_columns(self):
        return """
       {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
       {% col "number" "# of hours" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_wide_column"'

#===============================================================================
# Houdini Crashes Report Classes

class NumCrashesOverTime(HoudiniStatsReport):
    """
    Houdini crashes over time. Line Chart.
    """
    def name(self):
        return "num_crashes_over_time"

    def title(self):
        return "Number of Crashes Over Time"

    def get_data(self, series_range, aggregation):
        
        return get_orm_data_for_report(HoudiniCrash.objects.all(),
                   'date', series_range, aggregation)

    def chart_aditional_message(self):
        return "{% include 'hou_reports_message.html' %}" 
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "# of crashes" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_area_wide"'

#-------------------------------------------------------------------------------

class NumOfMachinesSendingCrashesOverTime(HoudiniStatsReport):
    """
    Number of indididual machines sending crashes over time. Column Chart.
    """    
    def name(self):
        return "num_machines_sending_crashes"

    def title(self):
        return "Number of Individual Machines Sending Crashes Over Time"

    def get_data(self, series_range, aggregation):
        string_query = """
         select {% aggregated_date "day" aggregation %} AS mydate, 
                sum(total_records)
         from (
             select machine_config_id,
             str_to_date(date_format(date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
             count( DISTINCT machine_config_id ) AS total_records
             from houdini_stats_houdinicrash
             where {% where_between "date" start_date end_date %}
             group by machine_config_id
         ) as TempTable
         group by mydate
         order by mydate"""
    
        return get_sql_data_for_report(string_query,'stats', locals())  
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Number of machines" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_wide_column"'

#-------------------------------------------------------------------------------

class AvgNumCrashesFromSameMachine(HoudiniStatsReport):
    """
    Average number of crashes emitted from the same machine. Column Chart.
    """    
    def name(self):
        return "avg_num_crashes_same_machine"

    def title(self):
        return "Average Num of Crashes From the Same Machine"

    def get_data(self, series_range, aggregation):
        string_query = """
         select {% aggregated_date "day" aggregation %} AS mydate, 
                avg(total_records)
         from (
             select machine_config_id,
             str_to_date(date_format(date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
             count(machine_config_id) as total_records
             from houdini_stats_houdinicrash
             where {% where_between "date" start_date end_date %}
             group by machine_config_id, day
         ) as TempTable
         group by mydate
         order by mydate"""
    
        return get_sql_data_for_report(string_query,'stats', locals()) 
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Avg # of crashes" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_wide_columnGreen"'

#-------------------------------------------------------------------------------

class CrashesByOS(HoudiniStatsReport):
    """
    Houdini crashes by os. PieChart report.
    """    
    def name(self):
        return "crashes_by_os"

    def title(self):
        return "Houdini Crashes by Operating Systems"

    def get_data(self, series_range, aggregation): 
        string_query = """
            SELECT os, count_by_os 
            FROM(  
            SELECT from_days( min( to_days( date ) ) ) AS min_date, 
                   mc.operating_system AS os, count( * ) AS count_by_os
            FROM houdini_stats_houdinicrash AS c, houdini_stats_machineconfig 
                 AS mc
            WHERE c.machine_config_id = mc.id 
                  AND {% where_between "date" start_date end_date %}
            GROUP BY os
            ORDER BY min_date)
            as TempTable
            ORDER BY count_by_os desc
        """
    
        full_os_names_and_counts = get_sql_data_for_report(string_query,
             'stats', locals(), fill_zeros = False)
         
        # Apply transformation to the data
        general_os_names_and_counts = self._get_hou_crashes_by_os_trans(
                                          full_os_names_and_counts)
    
        return [general_os_names_and_counts, full_os_names_and_counts]  
        
    def _get_hou_crashes_by_os_trans(self, full_os_name_and_counts_list):
        """
        This function does a data transformation.
        
        Receiving a list form (example):
        [(u'linux-x86_64-gcc4.4', 57L), 
        (u'linux-x86_64-gcc4.6', 38L), (u'linux-x86_64-gcc4.7', 18L), 
        (u'darwin-x86_64-clang5.1-MacOSX10.9', 16L), 
        (u'darwin-x86_64-clang4.1-MacOSX10.8', 2L), 
        (u'windows-i686-cl17', 1L)]
    
        Return a list of a more general level, and adding the OS with the same
        type, for example:
        
        [(u'Linux', 113L), 
        (u'Mac', 18L), 
        (u'Windows', 1L)]
        """
        
        linux_counts = 0
        mac_counts = 0
        win_counts= 0
         
        for os_name, count in full_os_name_and_counts_list:
            if 'linux' in os_name:
                linux_counts+=count
            elif 'darwin' in os_name:
                mac_counts+=count
            elif 'windows' in os_name:
                win_counts+=count         
                 
        return [('Linux', linux_counts),
                ('Mac OS', mac_counts),
                ( 'Windows', win_counts)]    
    
    def chart_columns(self):
        return """
        {% col "string" "OS" %}"{{ val }}"{% endcol %}
        {% col "number" "Count" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"out_options"'
    
    def chart_count(self):
        return 2

#-------------------------------------------------------------------------------

class CrashesByProduct(HoudiniStatsReport):
    """
    Houdini crashes by product (Houdini Commercial, Houdini Apprentice,
    Hbatch, etc). PieChart report.
    """    
    def name(self):
        return "crashes_by_product"

    def title(self):
        return "Houdini Crashes by Product"

    def get_data(self, series_range, aggregation): 
        
        string_query = """
            SELECT concat_ws( '-', mc.product, mc.is_apprentice), 
            count( * ) as counts
            FROM houdini_stats_houdinicrash AS c, 
                 houdini_stats_machineconfig AS mc
            WHERE c.machine_config_id = mc.id
                  AND {% where_between "date" start_date end_date %}
            GROUP BY mc.product, mc.is_apprentice
            ORDER BY counts desc
        """
    
        crashes_by_product_list = get_sql_data_for_report(string_query,'stats', 
                                      locals(), fill_zeros = False)
    
        return self._get_hou_crashes_by_product_trans(crashes_by_product_list) 

    def _get_hou_crashes_by_product_trans(self, crashes_by_product_list):
        """
        This function does a data transformation.
        
        Receiving a list in the form (example):
        
        [(u'Houdini-0', 138L), 
         (u'Hbatch-0', 2L), 
         (u'Houdini-1', 2L),
         (u'Hescape-0', 1L), 
         (u'Mplay-0', 1L)]
      
        In the data, in the tuple, the first element represents the Houdini 
        product name, the suffix '-0', or '0-1' is there to identify if the 
        product is apprentice or not. The second element in the tuple is the 
        counts of crashes registered in DB for this specific product.
        
        Return a list were the suffix '-1' will be substituted by 'Apprentice'
        and the suffix '-0' will be eliminated, returning a list of the form: 
        
        [(u'Houdini', 138L), 
         (u'Hbatch', 2L), 
         (u'Houdini Apprentice', 2L),
         (u'Hescape', 1L), 
         (u'Mplay', 1L)]
        """
        import re
        REPLACEMENTS = dict([('-1', ' Apprentice'), ('-0', '')])
                         
        def replacer(m):
            return REPLACEMENTS[m.group(0)]
    
        r = re.compile('|'.join(REPLACEMENTS.keys()))
        return [(r.sub(replacer, tup[0]), tup[1]) for tup in \
                crashes_by_product_list]  
    
    def chart_columns(self):
        return """
        {% col "string" "Product" %}"{{ val }}"{% endcol %}
        {% col "number" "Count" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"out_options"'
    
#===============================================================================
# Houdini Tools Usage related reports

class MostPopularTools(HoudiniStatsReport):
    """
    Most popular houdini tools. Column Chart.
    """  
    def name(self):
        return "most_popular_tools"

    def title(self):
        return "Most Popular Houdini Tools"
    
    def supports_aggregation(self):
        return False
    
    def tool_usage_count(self):
        """
        How many times does the tool needs to be used to be shown the chart.
        """
        return 3
    
    def creation_mode(self):
        """
        Where was the tool created: "(1,2,3)" -  shelf, viewer, network 
        """ 
        return "(1,2,3)"

    def get_data(self, series_range, aggregation):
        
        tool_usage_count = self.tool_usage_count()
        tool_creation_mode = self.creation_mode()

        string_query = """
            select tool_name, tool_count 
               from (
               select sum(count) as tool_count, tool_name, tool_creation_mode
                from houdini_stats_houdinitoolusage
                where {% where_between "date" start_date end_date %}
                group by tool_name 
                order by tool_count
           ) as TempTable
           where tool_count >=  {{ tool_usage_count }} and 
           tool_creation_mode in {{ tool_creation_mode }} 
           order by tool_count desc
           limit 20
        """
        
        return get_sql_data_for_report(string_query, 'stats', locals(), 
                   fill_zeros=False)
    
    def chart_aditional_message(self):
        return "{% include 'hou_reports_message.html' %}" 
    
    def chart_columns(self):
        return """
        {% col "string" "Houdini Tool" %}"{{ val }}"{% endcol %}
        {% col "number" "# of times used" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        return '"opt_count_wide_column"'

#-------------------------------------------------------------------------------

class MostPopularToolsShelf(MostPopularTools):
    """
    Most popular houdini tools from the Shelf. Column Chart.
    """  
    def name(self):
        return "most_popular_tools_shelf"

    def title(self):
        return "Most Popular Houdini Tools from the Shelf"
    
    def creation_mode(self):
        """
        Where was the tool created: "(1)" -  shelf 
        """ 
        return "(1)"

    def chart_options(self):
        return '"opt_count_wide_columnGreen"'
    
    def chart_aditional_message(self):
        return "" 

#-------------------------------------------------------------------------------

class MostPopularToolsViewer(MostPopularTools):
    """
    Most popular houdini tools from the Viewer. Column Chart.
    """  
    def name(self):
        return "most_popular_tools_viewer"

    def title(self):
        return "Most Popular Houdini Tools from the Viewer"
    
    def creation_mode(self):
        """
        Where was the tool created: "(2)" -  viewer 
        """ 
        return "(2)"

    def chart_options(self):
        return '"opt_count_wide_columnYellow"'    
    
    def chart_aditional_message(self):
        return "" 
    
#-------------------------------------------------------------------------------

class MostPopularToolsNetwork(MostPopularTools):
    """
    Most popular houdini tools from the Network. Column Chart.
    """  
    def name(self):
        return "most_popular_tools_network"

    def title(self):
        return "Most Popular Houdini Tools from the Network"
    
    def creation_mode(self):
        """
        Where was the tool created: "(3)" -  network 
        """ 
        return "(3)"

    def chart_options(self):
        return '"opt_count_wide_columnPurple"' 
    
    def chart_aditional_message(self):
        return "" 
    
#===============================================================================
# Houdini Versions and Builds related reports

class VersionsAndBuilds(HoudiniStatsReport):
    """
    Houdini versions and builds. Pie Charts.
    """  
    def name(self):
        return "versions_and_builds"

    def title(self):
        return "Houdini Versions and Builds"
    
    def supports_aggregation(self):
        return False

    def show_date_picker(self):
        return False
    
    def query_set(self):        
        return MachineConfig.objects.exclude(houdini_major_version=0, 
                                             product="") 
    
    def get_data(self, series_range, aggregation):
        
        # All machines with all products
        machines_queryset = self.query_set()
        # Transform the result from seconds into the proper time unit.
        return self._get_versions_builds_trans(machines_queryset)
    
    def _get_versions_builds_trans(self, machines_queryset):
        """
        Transform the query set to get the product name and counts to draw
        the pie charts. 
        """
        
        dict_hou_version_counts = defaultdict(int)
        dict_hou_version_builds_counts = defaultdict(int)
        
        for machine_config in machines_queryset:
            
            # Fill houdini version dict
            houdini_version = str(machine_config.houdini_major_version) + "."+\
                          str(machine_config.houdini_minor_version) 
            chart_hou_version_text = self.chart_leyend_text() + " " +\
                                         houdini_version
            dict_hou_version_counts[chart_hou_version_text] += 1
                          
            # Fill houdini version builds dict
            houdini_version_build = houdini_version + "." +\
                                     machine_config.houdini_build_number
            chart_hou_version_build_text = self.chart_leyend_text() + " " +\
                                               houdini_version_build
            dict_hou_version_builds_counts[chart_hou_version_build_text] += 1
        
        return [self._return_product_counts_list(dict_hou_version_counts),
                self._return_product_counts_list(
                     dict_hou_version_builds_counts)] 
        
    def _return_product_counts_list(self, dict_hou_versions_or_builds_counts):
        
        return [[houdini, count] for houdini, count in
                   dict_hou_versions_or_builds_counts.iteritems()] 
            
    
    def chart_leyend_text(self):
        """
        Suffix to be used in the pie charts, Ex. Houdinie Apprentice or 
        Houdini Commercial, or simply Houdini we are showing all versions and 
        builds.
        """
        return "Houdini"
    
    def chart_aditional_message(self):
        return "{% include 'hou_reports_message.html' %}" 
    
    def chart_columns(self):
        return """
        {% col "string" "Name" %}"{{ val }}"{% endcol %}
        {% col "number" "Value" %}{{ val }}{% endcol %}
       """
    
    def chart_options(self):
        return '"out_options"'
    
    def chart_count(self):
        return 2
    
#------------------------------------------------------------------------------- 
   
class VersionsAndBuildsApprentice(VersionsAndBuilds):
    """
    Houdini Apprentice versions and builds. Pie Charts.
    """  
    def name(self):
        return "versions_and_builds_apprentice"

    def title(self):
        return "Houdini Apprentice Versions and Builds"
    
    def query_set(self):        
        return MachineConfig.objects.filter(is_apprentice=True).exclude(
                  houdini_major_version=0, product="")
    
    def chart_leyend_text(self):
        return "Houdini Apprentice"
    
    def chart_aditional_message(self):
        return "" 

#-------------------------------------------------------------------------------  
  
class VersionsAndBuildsCommercial(VersionsAndBuilds):
    """
    Houdini Commercial versions and builds. Pie Charts.
    """  
    def name(self):
        return "versions_and_builds_commercial"

    def title(self):
        return "Houdini Commercial Versions and Builds"
    
    def query_set(self):        
        return MachineConfig.objects.filter(is_apprentice=False).exclude(
                  houdini_major_version=0, product="")
    
    def chart_leyend_text(self):
        return "Houdini FX"    
    
    def chart_aditional_message(self):
        return "" 
    
        

   