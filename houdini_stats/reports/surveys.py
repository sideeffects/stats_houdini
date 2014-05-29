from houdini_stats.genericreportclasses import *
from houdini_surveys.models import *

import houdini_stats.utils             
import houdini_stats.time_series

#===============================================================================
# Surveys Database reports

def _get_user_answers_by_qid_aid(question_id=None, answer_id=None, 
                                 series_range=None):
    """
    Get user answers by the filters given as parameters.
    """
    queryset = UserAnswers.objects.all()
        
    if question_id is not None and answer_id is not None:
        # Both filters are not None
        queryset = queryset.filter(
            question_id=question_id, answer_id=answer_id)
    elif question_id is not None:
        # Assumed then answer_id none otherwise will be case above 
        queryset = queryset.filter(question_id=question_id)
    elif answer_id is not None:
        # Assumed then question_id is none otherwise will be first case 
        queryset = queryset.filter(answer_id=answer_id)
    
    if series_range is not None:
        return queryset.filter(date__range=[series_range[0],
                                            series_range[1]
                                            ])
    return queryset
#-------------------------------------------------------------------------------

@cacheable
def _get_maya_users():
    """
    Count of users who subscribed for the Maya plugin
    """
    return _get_user_answers_by_qid_aid(question_id=44, answer_id=229)     

#-------------------------------------------------------------------------------
@cacheable    
def _get_unity_users():
    """
    Count of users who subscribed for the Unity plugin
    """
    return _get_user_answers_by_qid_aid(question_id=44, answer_id=230)

#-------------------------------------------------------------------------------

class BreakdownMayaUnityCounts(ChartReport):
    """
    Breakdown of users who subscribed to Maya or Unity plugin. Column Chart.
    """  
    def name(self):
        return "breakdown_maya_unity_counts"

    def title(self):
        return "Breakdown of Users who subscribed for Maya or Unity plugin"
    
    def get_data(self, series_range, aggregation):
        return [("Maya | Unity", _get_maya_users().count(), 
                                 _get_unity_users().count())]
        
    def chart_aditional_information_above(self):
        count_total = _get_maya_users().count() + _get_unity_users().count()
        
        return """<div><br>
         <span> &nbsp;&nbsp;&nbsp;&nbsp; 
          Total number of answers (since the survey was launch): {0}
         </span>   
         </div>""".format(str(count_total))
        
    def chart_columns(self):
        return """
            {% col "string" "3D Tool" %}"{{ val }}"{% endcol %}
            {% col "number" "# of users registered" %}{{ val }}{% endcol %}
            {% col "number" "# of users registered" %}{{ val }}{% endcol %}
            """
    
    def chart_options(self):
        return '"opt_count_column"'
    

#-------------------------------------------------------------------------------

class BreakdownMayaUnityOverTime(ChartReport):
    """
    Breakdown of users who subscribed to Maya or Unity plugin. Column Chart.
    """  
    def name(self):
        return "breakdown_maya_unity_overtime"

    def title(self):
        return ""

    def get_data(self, series_range, aggregation):
        return time_series.merge_time_series(
                   time_series.get_time_series_sequences(
                                       [_get_maya_users(), _get_unity_users()],
                                       interval= series_range, 
                                       aggregation= aggregation,
                                       date_field ="date"))
    
    def chart_columns(self):
        return """
            {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
            {% col "number" "Maya" %}{{ val }}{% endcol %}
            {% col "number" "Unity" %}{{ val }}{% endcol %}
            """

    def chart_options(self):
        return '"opt_count_with_legend"'    
  