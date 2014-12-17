from django.db.models import Avg, Sum, Count
import django.db
from collections import defaultdict
import petl

from stats_main.genericreportclasses import *
import stats_main.utils             
import stats_main.time_series 

from houdini_stats.models import *
from stats_main.models import *
from settings import IP_PATTERNS 

#===============================================================================
linux = ['linux', 'mint', 'debian', 'ubuntu', 'fedora', 'centos', 'rhel', 
         'opensuse', 'red hat', '/sid']
windows = ['windows']
mac = ['mac', 'mavericks', 'mountain lion']

#-------------------------------------------------------------------------------
def _contains_any(string, substrings):
    for substring in substrings:
        if substring in string:
            return True
    return False

#-------------------------------------------------------------------------------
def _clean_os_names(full_os_name_and_counts_list):
    
    cleaned_list = []
    
    for os_name, count in full_os_name_and_counts_list:
        os_name = os_name.replace('"','')
        if os_name == "":
            os_name = "Unknown"
        cleaned_list.append((os_name, count))
        
    return cleaned_list

#-------------------------------------------------------------------------------        
def _get_counts_by_os_trans(full_os_name_and_counts_list):
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
        unknown_counts = 0 
         
        for os_name, count in full_os_name_and_counts_list:
            os_name = os_name.lower() 
            if _contains_any(os_name, linux):
                linux_counts+=count
            elif _contains_any(os_name, mac):
                mac_counts+=count
            elif 'windows' in os_name:
                win_counts+=count   
            else:
                #print os_name  
                unknown_counts+=count            
        
        return [('Linux', linux_counts),
                ('Mac OS', mac_counts),
                ('Windows', win_counts),
                ('Unknown', unknown_counts)]    

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
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1] 
        
        internal_machines_sending_stats = get_sql_data_for_report("""
        select {% aggregated_date "min_creation_date" aggregation %} AS mydate, 
               count(machines_count)
        from(  
            select min(str_to_date(date_format(creation_date, '%%Y-%%m-%%d'),
                                                                '%%Y-%%m-%%d')) 
                   as min_creation_date,
                   count(distinct machine_id) as machines_count 
            from stats_main_machineconfig
            where {% where_between "creation_date" start_date end_date %}
            and (ip_address like '{{ ip_pattern1 }}'
            or ip_address like '{{ ip_pattern2 }}') 
            group by machine_id
            order by min_creation_date)
        as TempTable
        group by mydate
        order by mydate""",
        'stats', locals())
        
        external_machines_sending_stats = get_sql_data_for_report("""
        select {% aggregated_date "min_creation_date" aggregation %} AS mydate, 
               count(machines_count)
        from(  
            select min(str_to_date(date_format(creation_date, '%%Y-%%m-%%d'),
                                                                '%%Y-%%m-%%d')) 
                   as min_creation_date,
                   count(distinct machine_id) as machines_count 
            from stats_main_machineconfig
            where {% where_between "creation_date" start_date end_date %}
            and ip_address not like '{{ ip_pattern1 }}'
            and ip_address not like '{{ ip_pattern2 }}' 
            group by machine_id
            order by min_creation_date)
        as TempTable
        group by mydate
        order by mydate""",
        'stats', locals())

        return time_series.merge_time_series([external_machines_sending_stats,
                                 get_events_in_range(series_range, aggregation),  
                                 internal_machines_sending_stats])
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}
              {% show_annotation_title events val %} 
        {% endcol %}
        {% col "number" "# of external machines " %}{{ val }}{% endcol %}    
        {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
        {% col "number" "# of internal machines " %}{{ val }}{% endcol %}
       """
    
    def chart_options(self):
        return '"opt_count_with_legend"'

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
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1] 
        
        internal_machines_sending_stats = get_sql_data_for_report(
                """
                select mydate, count( distinct machine )
                from (
                select {% aggregated_date "u.date" aggregation %} AS mydate, 
                   mc.machine_id AS machine
                from houdini_stats_uptime u, stats_main_machineconfig mc
                where mc.id = u.stats_machine_config_id
                and {% where_between "u.date" start_date end_date %}
                and (mc.ip_address like '{{ ip_pattern1 }}'
                or mc.ip_address like '{{ ip_pattern2 }}') 
                ORDER BY u.date
                ) as tempTable
                GROUP BY mydate
                ORDER BY mydate  
               """ ,
               'stats', locals())
        
        external_machine_sending_stats = get_sql_data_for_report(
                """
                select mydate, count( distinct machine )
                from (
                select {% aggregated_date "u.date" aggregation %} AS mydate, 
                   mc.machine_id AS machine
                from houdini_stats_uptime u, stats_main_machineconfig mc
                where mc.id = u.stats_machine_config_id
                and {% where_between "u.date" start_date end_date %}
                and mc.ip_address not like '{{ ip_pattern1 }}'
                and mc.ip_address not like '{{ ip_pattern2 }}' 
                ORDER BY u.date
                ) as tempTable
                GROUP BY mydate
                ORDER BY mydate  
               """ ,
               'stats', locals())
 
        return time_series.merge_time_series([external_machine_sending_stats, 
                                 get_events_in_range(series_range, aggregation),
                                 internal_machines_sending_stats])
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}
              {% show_annotation_title events val %} 
        {% endcol %}
        {% col "number" "# of external machines " %}{{ val }}{% endcol %}
        {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
        {% col "number" "# of internal machines " %}{{ val }}{% endcol %}
       """
    
    def chart_options(self):
        return '"opt_count_with_legend"'

#-------------------------------------------------------------------------------

class MachinesSendingStatsByOS(HoudiniStatsReport):
    """
    Machines sending stats by Operating System. Pie Chart.
    """
    
    def get_query(self):
        return "" 
    
    def get_data(self, series_range, aggregation):
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1] 
        
        machines_sending_stats_by_os = get_sql_data_for_report(
               self.get_query(), 'stats', 
                locals(),
                fill_zeros = False)
        
        # Clean os names
        machines_sending_stats_by_os = _clean_os_names(
                                                   machines_sending_stats_by_os)
        
        # Apply transformation to the data
        general_machines_os_names_and_counts = _get_counts_by_os_trans(
                                           machines_sending_stats_by_os)
        
        return [general_machines_os_names_and_counts, 
                machines_sending_stats_by_os]
        
    
    def chart_columns(self):
        return """
        {% col "string" "OS" %}"{{ val }}"{% endcol %}
        {% col "number" "Count" %}{{ val }}{% endcol %}
       """
    
    def chart_options(self):
        return '"out_options_smaller"'
    
    def chart_count(self):
        return 2  

#-------------------------------------------------------------------------------
class InternalMachinesSendingStatsByOS(MachinesSendingStatsByOS):
    """
    Internal machines sending stats by Operating System. Pie Chart.
    """
    def name(self):
        return "internal_machines_actively_sending_stats_by_os"

    def title(self):
        return "Internal Machines Sending Stats by Operating System "

    def get_query(self):
        
        return """
                SELECT os, count_by_os 
                FROM(  
                SELECT from_days( min( to_days( date ) ) ) AS min_date, 
                    mc.operating_system AS os, 
                    count(distinct(mc.machine_id)) AS count_by_os
                from houdini_stats_uptime AS u, stats_main_machineconfig as mc
                where mc.id = u.stats_machine_config_id
                   AND {% where_between "date" start_date end_date %}
                and (mc.ip_address like '{{ ip_pattern1 }}'
                or mc.ip_address like '{{ ip_pattern2 }}')    
                GROUP BY os
                ORDER BY min_date)
                as TempTable
                ORDER BY os
                """ 

#-------------------------------------------------------------------------------
class ExternalMachinesSendingStatsByOS(MachinesSendingStatsByOS):
    """
    External machines sending stats by Operating System. 
    Pie Chart.
    """
    def name(self):
        return "external_machines_actively_sending_stats_by_os"

    def title(self):
        return "External Machines Sending Stats by Operating System "

    def get_query(self):
        
        return """
                SELECT os, count_by_os 
                FROM(  
                SELECT from_days( min( to_days( date ) ) ) AS min_date, 
                    mc.operating_system AS os, 
                    count(distinct(mc.machine_id)) AS count_by_os
                from houdini_stats_uptime AS u, stats_main_machineconfig as mc
                where mc.id = u.stats_machine_config_id
                   AND {% where_between "date" start_date end_date %}
                and mc.ip_address not like '{{ ip_pattern1 }}'
                and mc.ip_address not like '{{ ip_pattern2 }}'   
                GROUP BY os
                ORDER BY min_date)
                as TempTable
                ORDER BY os
                """ 

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
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1] 
        
        internal_machines_sending_stats = get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_records)
            from (
                 select u.stats_machine_config_id,
                 str_to_date(date_format(u.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') 
                 as day,
                 count(u.stats_machine_config_id) as total_records
                 from houdini_stats_uptime u, stats_main_machineconfig mc
                 where mc.id = u.stats_machine_config_id
                 and {% where_between "u.date" start_date end_date %}
                 and (mc.ip_address like '{{ ip_pattern1 }}'
                 or mc.ip_address like '{{ ip_pattern2 }}') 
                 group by u.stats_machine_config_id, day
             ) as TempTable
             group by mydate
             order by mydate
             """,
             'stats', locals())
        
        external_machines_sending_stats = get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_records)
            from (
                 select u.stats_machine_config_id,
                 str_to_date(date_format(u.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') 
                 as day,
                 count(u.stats_machine_config_id) as total_records
                 from houdini_stats_uptime u, stats_main_machineconfig mc
                 where mc.id = u.stats_machine_config_id
                 and {% where_between "u.date" start_date end_date %}
                 and mc.ip_address not like '{{ ip_pattern1 }}'
                 and mc.ip_address not like '{{ ip_pattern2 }}' 
                 group by u.stats_machine_config_id, day
            ) as TempTable
            group by mydate
            order by mydate
            """,
            'stats', locals())
 
        return time_series.merge_time_series([external_machines_sending_stats, 
                                 internal_machines_sending_stats])

    def chart_columns(self):
        return """
          {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
          {% col "number" "Avg # of connections from external machines" %}
             {{ val }}
          {% endcol %}
          {% col "number" "Avg # of connections from internal machines" %}
             {{ val }}
          {% endcol %}
       """

    def chart_options(self):
        return '"opt_count_with_legend"'
    
#===============================================================================
# Houdini Uptime Report Classes

class AverageSessionLength(HoudiniStatsReport):
    """
    Houdini average session length. Column Chart.
    """
    def name(self):
        return "average_session_length"

    def title(self):
        return "Average Session Length (in minutes)"

    def get_data(self, series_range, aggregation):
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1] 
         
        internal_machines_sending_stats = time_series.seconds_to_time_unit_series(
            get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_uptime_seconds)
             from (
                 select u.stats_machine_config_id,
                 str_to_date(date_format(u.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d')
                    as day,
                 (u.number_of_seconds - u.idle_time) as total_uptime_seconds
                 from houdini_stats_uptime u, stats_main_machineconfig mc,
                      houdini_stats_houdinimachineconfig hmc
                 where mc.id = u.stats_machine_config_id 
                 and  mc.id = hmc.machine_config_id
                 and {% where_between "u.date" start_date end_date %}
                 and (hmc.product != 'Mantra' and 
                      hmc.product != 'Hbatch')   
                 and (mc.ip_address like '{{ ip_pattern1 }}'
                 or mc.ip_address like '{{ ip_pattern2 }}') 
                 group by day
             ) as TempTable
             group by mydate
             order by mydate
             """,
             'stats', locals()), 
             "minutes")
          
        external_machines_sending_stats = time_series.seconds_to_time_unit_series(
            get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_uptime_seconds)
             from (
                 select u.stats_machine_config_id,
                   str_to_date(date_format(u.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d')
                   as day,
                   (u.number_of_seconds - u.idle_time) as total_uptime_seconds
                 from houdini_stats_uptime u, stats_main_machineconfig mc,
                      houdini_stats_houdinimachineconfig hmc
                 where mc.id = u.stats_machine_config_id 
                 and  mc.id = hmc.machine_config_id
                 and {% where_between "u.date" start_date end_date %}
                 and (hmc.product != 'Mantra' and 
                      hmc.product != 'Hbatch')   
                 and mc.ip_address not like '{{ ip_pattern1 }}'
                 and mc.ip_address not like '{{ ip_pattern2 }}' 
                 group by day
             ) as TempTable
             group by mydate
             order by mydate
             """,
             'stats', locals()), 
             "minutes")
   
        return time_series.merge_time_series([external_machines_sending_stats, 
                                 internal_machines_sending_stats])      
        
    def chart_columns(self):
        return """
           {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
           {% col "number" "Avg session length for external machines" %}
              {{ val }}
           {% endcol %}
           {% col "number" "Avg session length for internal machines" %}
              {{ val }}
           {% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_with_legend"'

#-------------------------------------------------------------------------------
   
class AverageUsageByMachine(HoudiniStatsReport):
    """
    Houdini average usage by machine. Column Chart.
    """
    def name(self):
        return "average_usage_by_machine"

    def title(self):
        return "Average Usage by Machine (in minutes)"

    def get_data(self, series_range, aggregation):     
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1] 
         
        internal_machines_sending_stats = time_series.seconds_to_time_unit_series(
            get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_seconds)
             from (
                 select u.stats_machine_config_id,
                 str_to_date(date_format(u.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d')
                    as day,
                 sum(u.number_of_seconds - u.idle_time) as total_seconds
                 from houdini_stats_uptime u, stats_main_machineconfig mc
                 where mc.id = u.stats_machine_config_id
                 and {% where_between "u.date" start_date end_date %}
                 and (mc.ip_address like '{{ ip_pattern1 }}'
                 or mc.ip_address like '{{ ip_pattern2 }}') 
                 group by u.stats_machine_config_id, day
             ) as TempTable
             group by mydate
             order by mydate
             """,
             'stats', locals()), 
             "minutes")
          
        external_machines_sending_stats = time_series.seconds_to_time_unit_series(
            get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                    avg(total_seconds)
             from (
                 select u.stats_machine_config_id,
                 str_to_date(date_format(u.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d')
                    as day,
                 sum(u.number_of_seconds - u.idle_time) as total_seconds
                 from houdini_stats_uptime u, stats_main_machineconfig mc
                 where mc.id = u.stats_machine_config_id
                 and {% where_between "u.date" start_date end_date %}
                 and mc.ip_address not like '{{ ip_pattern1 }}'
                 and mc.ip_address not like '{{ ip_pattern2 }}' 
                 group by u.stats_machine_config_id, day
             ) as TempTable
             group by mydate
             order by mydate
             """,
             'stats', locals()), 
             "minutes")
        
        return time_series.merge_time_series([external_machines_sending_stats, 
                                 internal_machines_sending_stats])    

    def chart_columns(self):
       return """
           {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
           {% col "number" "Avg usage for external machines" %}
              {{ val }}
           {% endcol %}
           {% col "number" "Avg usage for internal machines" %}
              {{ val }}
           {% endcol %}
        """
    def chart_options(self):
        return '"opt_count_with_legend"'

#-------------------------------------------------------------------------------

class BreakdownOfApprenticeUsage(HoudiniStatsReport):
    """
    Breakdown of users who subscribed to Maya or Unity plugin. Column Chart.
    """  
    def __init__(self, version_tuple):
        self.version_tuple = version_tuple[:]

    def _version_name(self):
        return "%s.%s" % self.version_tuple

    def name(self):
        return "breakdown_of_apprentice_usage%s_%s" % self.version_tuple

    def title(self):
        return ("Time Spent in Houdini %s by Apprentice Users" +
            " (Histogram in Minutes)") % self._version_name()

    def get_data(self, series_range, aggregation):
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1] 
        major_version = self.version_tuple[0]
        minor_version = self.version_tuple[1]
        
        string_query = """
            select
                stats_main_machineconfig.machine_id as m_id,
                min(date) as first_date,
                max(date) as last_date,
                sum(number_of_seconds - idle_time) / 60 as non_idle_minutes,
                count(*) as num_sessions
            from
                houdini_stats_uptime,
                stats_main_machineconfig,
                houdini_stats_houdinimachineconfig
            where stats_machine_config_id=stats_main_machineconfig.id
            and stats_machine_config_id=
                houdini_stats_houdinimachineconfig.machine_config_id
            and is_apprentice=1 and product="Houdini" 
            and houdini_major_version = {{ major_version }}
            and houdini_minor_version = {{ minor_version }}
            and ip_address not like '{{ ip_pattern1 }}'
            and ip_address not like '{{ ip_pattern2 }}' 
            group by m_id
            having {% where_between "first_date" start_date end_date %}
            order by first_date;
        """

        string_query = expand_templated_query(string_query, locals())
        return self._get_histogram_trans(string_query)
    
    def _get_histogram_trans(self, string_query):
        bin_size_in_minutes = 2
        max_minutes = 240

        connection = django.db.connections["stats"]
        table1 = petl.fromdb(connection, string_query, [])
        table2 = petl.rangeaggregate(
            table1, "non_idle_minutes", bin_size_in_minutes, len, minv=0)

        result = []
        for minutes, value in table2[1:]:
            if minutes[0] <= max_minutes and minutes[1] > max_minutes:
                result.append(["%s+" % minutes[0], value])
            elif minutes[0] > max_minutes:
                result[-1][1] += value
            else:
                result.append(("%s - %s" % (minutes[0], minutes[1]), value))
        return result

    def chart_columns(self):
       return """
           {% col "string" "# minutes" %}"{{ val }}"{% endcol %}
           {% col "number" "# users" %}{{ val }}{% endcol %}
        """

    def chart_options(self):
        return '"opt_count_wide_columnGreen"'

class BreakdownOfApprenticeUsageH13(BreakdownOfApprenticeUsage):
    def __init__(self):
        super(BreakdownOfApprenticeUsageH13, self).__init__((13, 0))

class BreakdownOfApprenticeUsageH14(BreakdownOfApprenticeUsage):
    def __init__(self):
        super(BreakdownOfApprenticeUsageH14, self).__init__((14, 0))

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
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1]
        
        internal_machines_sending_stats = get_sql_data_for_report(
                """
                select {% aggregated_date "c.date" aggregation %} AS mydate, 
                       count(*) as total_records
                from houdini_stats_houdinicrash c, stats_main_machineconfig mc
                where mc.id = c.stats_machine_config_id
                and {% where_between "c.date" start_date end_date %}
                and (mc.ip_address like '{{ ip_pattern1 }}'
                or mc.ip_address like '{{ ip_pattern2 }}') 
                GROUP BY mydate
                ORDER BY mydate  
               """ ,
               'stats', locals())
        
        external_machine_sending_stats = get_sql_data_for_report(
                """
                select {% aggregated_date "c.date" aggregation %} AS mydate, 
                       count(*) as total_records
                from houdini_stats_houdinicrash c, stats_main_machineconfig mc
                where mc.id = c.stats_machine_config_id
                and {% where_between "c.date" start_date end_date %}
                and mc.ip_address not like '{{ ip_pattern1 }}'
                and mc.ip_address not like '{{ ip_pattern2 }}'
                GROUP BY mydate
                ORDER BY mydate  
               """ ,
               'stats', locals())
 
        return time_series.merge_time_series([external_machine_sending_stats, 
                                 get_events_in_range(series_range, aggregation),
                                 internal_machines_sending_stats])
         
        
    def chart_columns(self):
        return """
        {% col "string" "Date" %}
              {% show_annotation_title events val %} 
        {% endcol %}
        {% col "number" "# of crashes for external machines " %}
           {{ val }}
        {% endcol %}
        {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
        {% col "number" "# of crashes for internal machines " %}
           {{ val }}
        {% endcol %}
       """
    
    def chart_options(self):
        return '"opt_count_with_legend"'
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
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1]
        
        internal_machines_sending_stats = get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                   sum(total_records)
            from (
                select c.stats_machine_config_id,
                str_to_date(date_format(c.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
                count( DISTINCT c.stats_machine_config_id ) AS total_records
                from houdini_stats_houdinicrash c, stats_main_machineconfig mc
                where mc.id = c.stats_machine_config_id
                and {% where_between "c.date" start_date end_date %}
                and (mc.ip_address like '{{ ip_pattern1 }}'
                or mc.ip_address like '{{ ip_pattern2 }}') 
                group by c.stats_machine_config_id
            ) as TempTable
            group by mydate
            order by mydate
            """ ,
            'stats', locals())
        
        external_machine_sending_stats = get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                   sum(total_records)
            from (
                select c.stats_machine_config_id,
                str_to_date(date_format(c.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
                count( DISTINCT c.stats_machine_config_id ) AS total_records
                from houdini_stats_houdinicrash c, stats_main_machineconfig mc
                where mc.id = c.stats_machine_config_id
                and {% where_between "c.date" start_date end_date %}
                and mc.ip_address not like '{{ ip_pattern1 }}'
                and mc.ip_address not like '{{ ip_pattern2 }}'
                group by c.stats_machine_config_id
            ) as TempTable
            group by mydate
            order by mydate
            """ ,
            'stats', locals())
 
        return time_series.merge_time_series([external_machine_sending_stats, 
                                 get_events_in_range(series_range, aggregation),
                                 internal_machines_sending_stats])
    
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}
              {% show_annotation_title events val %} 
        {% endcol %}
        {% col "number" "# of individual external machines" %}
           {{ val }}
        {% endcol %}
        {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
        {% col "number" "# of individual internal machines " %}
           {{ val }}
        {% endcol %}
       """
    
    def chart_options(self):
        return '"opt_count_with_legend"'

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
        
        ip_pattern1 = IP_PATTERNS[0] 
        ip_pattern2 = IP_PATTERNS[1]
        
        internal_machines_sending_stats = get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                   avg(total_records)
            from (
                select c.stats_machine_config_id,
                str_to_date(date_format(c.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
                count( c.stats_machine_config_id ) AS total_records
                from houdini_stats_houdinicrash c, stats_main_machineconfig mc
                where mc.id = c.stats_machine_config_id
                and {% where_between "c.date" start_date end_date %}
                and (mc.ip_address like '{{ ip_pattern1 }}'
                or mc.ip_address like '{{ ip_pattern2 }}') 
                group by c.stats_machine_config_id, day
            ) as TempTable
            group by mydate
            order by mydate
            """ ,
            'stats', locals())
        
        external_machine_sending_stats = get_sql_data_for_report(
            """
            select {% aggregated_date "day" aggregation %} AS mydate, 
                   avg(total_records)
            from (
                select c.stats_machine_config_id,
                str_to_date(date_format(c.date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
                count( c.stats_machine_config_id ) AS total_records
                from houdini_stats_houdinicrash c, stats_main_machineconfig mc
                where mc.id = c.stats_machine_config_id
                and {% where_between "c.date" start_date end_date %}
                and mc.ip_address not like '{{ ip_pattern1 }}'
                and mc.ip_address not like '{{ ip_pattern2 }}'
                group by c.stats_machine_config_id, day
            ) as TempTable
            group by mydate
            order by mydate
            """ ,
            'stats', locals())
 
        return time_series.merge_time_series([external_machine_sending_stats, 
                                 get_events_in_range(series_range, aggregation),
                                 internal_machines_sending_stats])
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}
              {% show_annotation_title events val %} 
        {% endcol %}
        {% col "number" "Avg # of crashes for external machines " %}
           {{ val }}
        {% endcol %}
        {% col "string" "" "annotation" %}"{{ val }}"{% endcol %}
        {% col "number" "Avg # of crashes for internal machines " %}
           {{ val }}
        {% endcol %}
       """
    
    def chart_options(self):
        return '"opt_count_with_legend"'


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
            FROM houdini_stats_houdinicrash AS c, stats_main_machineconfig 
                 AS mc
            WHERE c.stats_machine_config_id = mc.id 
                  AND {% where_between "date" start_date end_date %}
            GROUP BY os
            ORDER BY min_date)
            as TempTable
            ORDER BY count_by_os desc
        """
    
        full_os_names_and_counts = get_sql_data_for_report(string_query,
             'stats', locals(), fill_zeros = False)
         
        # Clean os names
        full_os_names_and_counts = _clean_os_names(full_os_names_and_counts) 
        
        # Apply transformation to the data
        general_os_names_and_counts = _get_counts_by_os_trans(
                                          full_os_names_and_counts)
    
        return [general_os_names_and_counts, full_os_names_and_counts]  
        
    
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
            SELECT concat_ws( '-', hmc.product, hmc.is_apprentice), 
            count( * ) as counts
            FROM houdini_stats_houdinicrash AS c, 
                 stats_main_machineconfig AS mc,
                 houdini_stats_houdinimachineconfig AS hmc
            WHERE c.stats_machine_config_id = hmc.machine_config_id
                  AND {% where_between "date" start_date end_date %}
            GROUP BY hmc.product, hmc.is_apprentice
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
        
        return MachineConfig.objects.exclude(get_extra_fields__houdini_major_version=0, 
                                            get_extra_fields__product="") 
        
        #return HoudiniMachineConfig.objects.exclude(houdini_major_version=0, 
        #                                       product="") 
    
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
            houdini_version = str(machine_config.get_extra_fields.houdini_major_version) + "."+\
                          str(machine_config.get_extra_fields.houdini_minor_version) 
            chart_hou_version_text = self.chart_leyend_text() + " " +\
                                         houdini_version
            dict_hou_version_counts[chart_hou_version_text] += 1
                          
            # Fill houdini version builds dict
            houdini_version_build = houdini_version + "." +\
                                     machine_config.get_extra_fields.houdini_build_number
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
        return MachineConfig.objects.filter(
                   get_extra_fields__is_apprentice=True).exclude(
                   get_extra_fields__houdini_major_version=0, 
                   get_extra_fields__product="")
    
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
        return MachineConfig.objects.filter(
                  get_extra_fields__is_apprentice=False).exclude(
                  get_extra_fields__houdini_major_version=0, 
                  get_extra_fields__product="")
    
    def chart_leyend_text(self):
        return "Houdini FX"    
    
    def chart_aditional_message(self):
        return "" 
    
        

   
