from django.db import connections
from django.template import Context, Template

from cachedqueries import cacheable
import time_series

#===============================================================================

def _get_cursor(db_name):
        """Given a db name returns a cursor."""
        return connections[db_name].cursor()

@cacheable
def get_sql_data_for_report(
        string_query, db_name, context_vars, 
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
        
        cursor = _get_cursor(db_name)
        tpl_header =  "{% load reports_tags %} "
             
        tpl = Template(tpl_header + string_query)
        
        #print tpl.render(Context(context_vars))
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
        
#-------------------------------------------------------------------------------

@cacheable
def get_orm_data_for_report(query_set, time_field, series_range, 
                            aggregation = None, func = None):
        """
        Function to get data for reports, using django orm for the queries.
        
        This function will receive the queryset, the name of the time field to
        be passed to the time series function, the series range, the aggregation 
        and the function to be passed for aggregation in the time series.    
        """
        
        return time_series.time_series(query_set, time_field, 
                                       series_range, func, aggregation)

#-------------------------------------------------------------------------------
@cacheable
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
    
#===============================================================================

registered_report_classes = []
            
class ReportMetaclass(type):
    def __new__(cls, name, bases, dct):
        result_class = type.__new__(cls, name, bases, dct)
        registered_report_classes.append(result_class)
        return result_class

#-------------------------------------------------------------------------------

def find_report_class(name):
    return [cls for cls in registered_report_classes
        if cls.__name__ == name][0]

#-------------------------------------------------------------------------------
        
class Report(object):
    __metaclass__ = ReportMetaclass
      
    def name(self):
        """
        Each report in the same page must have a unique name.
        """
        pass
#-------------------------------------------------------------------------------

class ChartReport(Report):
    def title(self):
        pass

    def get_data(self, series_range, aggregation):
        pass
    
    def chart_columns(self):
        pass

    def chart_options(self):
        # TODO: Add report types, and determine default options from that type.
        # TODO: Allow each class to contribute to the options template.
        return ""
    
    def chart_count(self):
        """
        How many charts to be drawn under the same placeholder.
        For pie charts we can have more than one chart.
        """
        return 1  
    
    def chart_aditional_message(self):
        return "" 
    
    def supports_aggregation(self):
        return True

    def show_date_picker(self):
        return True

    def minimum_start_date(self):
        import settings
        return settings.REPORTS_START_DATE
 
    def generate_template_placeholder_code(self):
        """
        Generate the template placeholder to draw the chart.
        Usually we have just one report under placeholder, but there are cases
        in the pie charts that we draw more than one pie chart under the same
        placeholder.
        """        
        
        report_title = '''
        <div class="graph-title">''' + self.title() + '''</div>
        <br>'''
        
        # How many charts to paint under the same placeholder
        chart_count = self.chart_count() 
        
        if chart_count==1:
            report_placeholder = ''' 
            <div id="''' + self.name() + '''" class="wide graph"></div> 
            <br> '''
        else:
            report_placeholder = ''' 
            <div>
            '''
            # Draw more than one report inline, under the same report tittle
            for i in range(1, chart_count+1):
                report_placeholder += '''
                <div id="''' + self.name() + str(i) + '''" style="display: inline-block">
                </div> 
                '''
            report_placeholder +='''
            </div>
            '''   
        return self.chart_aditional_message() + report_title + report_placeholder

    def generate_template_graph_drawing(self):
        """
        Generate the graph drawing template placeholder to draw the chart.
        Usually we have just one report to draw, but there are cases
        in the pie charts that we want to paint more than one pie chart under 
        the same placeholder.
        """  
        
        # How many charts to be painted
        chart_count = self.chart_count() 
        
        format_dict = dict(
            name=self.name(),
            options=self.chart_options())
        
        template_string = ""
        if chart_count==1:
            template_string =  (
                ("""{%% data report_data.%(name)s "%(name)s" %%}\n"""
                    % format_dict) +
                self.chart_columns() + "\n" +
                "{% enddata %}\n" +
                ("""{%% graph "%(name)s" "%(name)s" %(options)s %%}"""
                    % format_dict)
            )
        else:
            for i in range(1, chart_count+1):
                format_dict['index'] = i-1
                format_dict['count'] = i
                template_string += (
                ("""{%% data report_data.%(name)s.%(index)d "%(name)s%(count)d" %%}\n"""
                    % format_dict) +
                self.chart_columns() + "\n" +
                "{% enddata %}\n" +
                ("""{%% graph "%(name)s%(count)d" "%(name)s%(count)d" %(options)s %%}"""
                    % format_dict)
                 ) + "\n" 
        return template_string 
        
#-------------------------------------------------------------------------------

    



