from houdini_stats.genericreportclasses import *
from houdini_stats.models import *

from django.db.models import Avg, Sum, Count

import houdini_stats.utils             
import houdini_stats.time_series 

#===============================================================================
# Houdini Usage Report Classes

class NewMachinesOverTime(SqlReport):
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

        return self.get_sql_data_for_report(string_query,'stats', locals())
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "# of new machines" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_area_wide"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE

#-------------------------------------------------------------------------------

class MachinesActivelySendingStats(SqlReport):
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
        return self.get_sql_data_for_report(string_query,'stats', locals())
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "# of machines " %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_area_wide"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE

#-------------------------------------------------------------------------------

class AvgNumConnectionsFromSameMachine(SqlReport):
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
                 str_to_date(date_format(date, '%%Y-%%m-%%d'),'%%Y-%%m-%%d') as day,
                 count(machine_config_id) as total_records
                 from houdini_stats_uptime
                 where {% where_between "date" start_date end_date %}
                 group by machine_config_id, day
             ) as TempTable
             group by mydate
             order by mydate"""
        
        return self.get_sql_data_for_report(string_query,'stats', locals())      
        
    def chart_columns(self):
        return """
         {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
         {% col "number" "Avg # of connections" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_wide_column"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE   

#===============================================================================
# Houdini Uptime Report Classes

class AverageSessionLength(OrmReport):
    """
    Houdini average session length. Column Chart.
    """
    def name(self):
        return "average_session_lenght"

    def title(self):
        return "Average Session Lenght (in hours)"

    def get_data(self, series_range, aggregation):
        
        series = self.get_orm_data_for_report(Uptime.objects.all(), 'date', 
                     series_range, aggregation, func=Avg("number_of_seconds"))

        # Transform the result from seconds into the proper time unit.
        return time_series.choose_unit_from_multiple_time_units_series(
           time_series.compute_time_serie(
               series,houdini_stats.utils.seconds_to_multiple_time_units), "hours") 

    def chart_columns(self):
        return """
       {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
       {% col "number" "# of hours" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_wide_column"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE

#------------------------------------------------------------------------------- 
   
class AverageUsageByMachine(SqlReport):
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
            self.get_sql_data_for_report(string_query, 'stats', locals()), 
            "hours")

    def chart_columns(self):
        return """
       {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
       {% col "number" "# of hours" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_wide_column"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE

#===============================================================================
# Houdini Crashes Report Classes

class NumCrashesOverTime(OrmReport):
    """
    Houdini crashes over time. Line Chart.
    """
    def name(self):
        return "num_crashes_over_time"

    def title(self):
        return "Number of Crashes Over Time"

    def get_data(self, series_range, aggregation):
        
        return self.get_orm_data_for_report(HoudiniCrash.objects.all(),
                   'date', series_range, aggregation)

    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "# of crashes" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_area_wide"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE

class NumOfMachinesSendingCrashesOverTime(SqlReport):
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
    
        return self.get_sql_data_for_report(string_query,'stats', locals())  
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Number of machines" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_wide_column"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE

#-------------------------------------------------------------------------------

class AvgNumCrashesFromSameMachine(SqlReport):
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
    
        return self.get_sql_data_for_report(string_query,'stats', locals()) 
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Avg # of crashes" %}{{ val }}{% endcol %}
       """

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return '"opt_count_wide_columnGreen"'

    def minimum_start_date(self):
        import settings
        return settings.HOUDINI_REPORTS_START_DATE

#-------------------------------------------------------------------------------




#-------------------------------------------------------------------------------





    
