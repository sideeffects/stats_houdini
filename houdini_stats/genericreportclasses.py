from django.db import connections
from django.template import Context, Template

import time_series

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
        return ""

    def supports_aggregation(self):
        return True

    def show_date_picker(self):
        return True

    def minimum_start_date(self):
        return None
 
    def generate_template_placeholder_code(self, report_count=1):
        """
        Generate the template placeholder to draw the chart.
        The param report_count will specify how many reports will be draw under 
        the same div. By default we always have just one report under place
        holder.
        """        
        
        # Work in progress
#         report_title = '''<div class="graph-title">''' + self.title() + '''</div>
#         <br>'''
#        
#         report_placeholder = ''' <div id="''' + self.name() + '''
#         " class="wide graph"></div> <br> '''
#         
#         #if report_count > 1:
#         #    for i in range(1, report
        
        return '''
    <div class="graph-title">''' + self.title() + '''</div>
    <br>
    <div id="''' + self.name() + '''" class="wide graph"></div>
    <br>
    '''

    def generate_template_graph_drawing(self, report_number, report_count=1):
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
#-------------------------------------------------------------------------------

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


#-------------------------------------------------------------------------------

class OrmReport(ChartReport):    
    
    def get_orm_data_for_report(self,query_set, time_field, series_range, 
                            aggregation = None, func = None):
        """
        Function to get data for reports, using django orm for the queries.
        
        This function will receive the queryset, the name of the time field to
        be passed to the time series function, the series range, the aggregation 
        and the function to be passed for aggregation in the time series.    
        """
        
        return time_series.time_series(query_set, time_field, 
                                       series_range, func, aggregation)
    



