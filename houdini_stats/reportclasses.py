from django.db import connections
from django.template import Context, Template

import time_series

class Report(object):
    def name(self):
        pass

class ChartReport(Report):
    def title(self):
        pass

    def get_data(self, series_range, aggregation):
        pass

    def chart_columns(self):
        pass

    def chart_options(self):
        return ""

    def supports_aggregation(self):
        return True

    def show_date_picker(self):
        return True

    def minimum_start_date(self):
        return None

    def generate_template_placeholder_code(self):
        # TODO: Clean this up!
        return '''
    <div class="graph-title">''' + self.title() + '''</div>
    <br>
    <div id="''' + self.name() + '''" class="wide graph"></div>
    <br>
'''

    def generate_template_graph_drawing(self, report_number):
        # TODO: Clean this up!
        format_dict = dict(
            report_number=report_number,
            name=self.name(),
            options=self.chart_options())
        return (
            ("""{%% data report_data.%(name)s "count%(report_number)s" %%}\n"""
                % format_dict) +
            self.chart_columns() + "\n" +
            "{% enddata %}\n" +
            ("""{%% graph "%(name)s" "count%(report_number)s" %(options)s %%}"""
                % format_dict)
        )

class SqlReport(ChartReport):
    def _get_cursor(self, db_name):
        """Given a db name returns a cursor."""
        return connections[db_name].cursor()

    def get_sql_data_for_report(
            self, string_query, db_name, context_vars, 
            fill_zeros=True, fill_empty_string=False):
        """
        Generic function to get data for reports, doing sql queries using a
        cursor.
        
        This func will receive the string with the query, the database name to
        create a cursor and the context vars using in the query.
        
        Explanation of the last 3 params:
        
        1. fill_zeros:  For time series the dates that have no value will be
        filled with zeros. 
        
        Sometimes we want to execute a query but the query wont retrieve
        datetimes, it wont be a time series, but different kind of data. For
        example data used for pie charts, for this cases we set fill_zeros=
        False so that we don't treat the data as time series.
        
        2. fill_empty_string: sometimes we want to fill with an empty string 
        instead of with zeros
        """
        
        context_vars = context_vars.copy()
        
        context_vars["start_date"] = context_vars['series_range'][0] 
        context_vars["end_date"] = context_vars['series_range'][1]
        
        cursor = self._get_cursor(db_name)
        tpl_header =  "{% load reports_tags %} "
             
        tpl = Template(tpl_header + string_query)
        cursor.execute(tpl.render(Context(context_vars)), [])
        
        series = [(row[0], row[1]) for row in cursor.fetchall()]

        if not fill_zeros and fill_empty_string:
            return time_series.fill_missing_dates_with_zeros(
                series,
                context_vars['aggregation'][:-2], 
                context_vars['series_range'],
                True) 
        if not fill_zeros:
            return series

        return time_series.fill_missing_dates_with_zeros(
            series,
            context_vars['aggregation'][:-2], 
            context_vars['series_range'])  

#----------------------------------------------------------------------------

class AverageUsageByMachine(SqlReport):
    """
    Get Houdini average usage by machine. Column Chart.
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

