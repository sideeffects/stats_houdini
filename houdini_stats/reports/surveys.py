from houdini_stats.genericreportclasses import *
from houdini_surveys.models import *

import houdini_stats.utils             
import houdini_stats.time_series
import apprentice

#===============================================================================
# Surveys Database reports

def _get_questions_from_survey(survey_id, exclude_question_id=None):
    """
    Get a questions from survey id.
    """   
    if exclude_question_id:
        return Questions.objects.filter(survey_id=survey_id).exclude(
                                                id=exclude_question_id)
        
    return Questions.objects.filter(survey_id=survey_id)

#-------------------------------------------------------------------------------

def _get_answers_from_question(question_id):
    """
    Get answers from a question id.
    """   
    return QuestionAnswers.objects.filter(question_id=question_id)

#-------------------------------------------------------------------------------

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
    Users who subscribed for the Maya plugin
    """
    return _get_user_answers_by_qid_aid(question_id=44, answer_id=229)     

#-------------------------------------------------------------------------------
@cacheable    
def _get_unity_users():
    """
    Users who subscribed for the Unity plugin
    """
    return _get_user_answers_by_qid_aid(question_id=44, answer_id=230)

#-------------------------------------------------------------------------------
# Houdini Engine Survey Reports

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
 
#-------------------------------------------------------------------------------
# Apprentice follow-up Survey Reports

def _get_common_for_apprentice_followup_survey():
            
    survey_id = 2
    questions =  _get_questions_from_survey(survey_id, 8)
    
    questions_answers = {}
    
    for q in questions:
        answers_for_questions= _get_answers_from_question(q.id)
        questions_answers[q.id] = {"question": q.question, 
                                   "answers" : answers_for_questions}
    
    return questions_answers 
    
#-------------------------------------------------------------------------------

class PercentageUsersWhoRepliedApprenticeSurvey(ChartReport):
    """
    Percentage of users who replied the Apprentice Survey, from Apprentice
    Activations. Column Chart.
    """  
    def name(self):
        return "percentage_survey_users_response_from_apprentice_activations"

    def title(self):
        return """
               Percentage of Users who replied the Survey from Apprentice 
               Activations"""
    
    def get_data(self, series_range, aggregation):
        
        survey_id = 2
        questions = _get_questions_from_survey(survey_id)
        questions_ids = tuple(int(q.id) for q in questions)
    
        string_query = """
            select {% aggregated_date "date" aggregation %} AS mydate, 
               count(distinct(user_id))
            from user_answers
            where question_id in {{ questions_ids }} and 
              {% where_between "date" start_date end_date %}
            group by mydate
            order by mydate"""
        
        user_counts = get_sql_data_for_report(string_query,'surveys', locals())
        apprentice_activations = apprentice.get_apprentice_total_activations(
                                                      series_range, aggregation)
        
        return time_series.get_percentage_from_total(apprentice_activations, 
                                                     user_counts)

    def chart_columns(self):
        return """
             {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
             {% col "number" "% of user" %}{{ val }}{% endcol %}
            """
    
    def chart_options(self):
        return '"opt_count_percentage_column"'

#-------------------------------------------------------------------------------
class ApprenticeFollowUpSurvey(ChartReport):
    """
    Apprentice Followup Survey Reports. Pie Charts.
    """  
    
    questions_tuples = []
    questions_and_total_counts = {}
    user_answers = {}
    
    def name(self):
        return "apprentice_follow_up_survey_results"

    def get_data(self, series_range, aggregation):
        # For apprentice survey pie charts
        self.questions_tuples, self.questions_and_total_counts, self.user_answers = ( 
                    self._apprentice_followup_survey(series_range, aggregation))        
        
        return self.user_answers

    def _apprentice_followup_survey(self, series_range, aggregation):
        """
        Get questions and answers for Apprentice Followup Survey
        """
        questions_and_answers = _get_common_for_apprentice_followup_survey()
        questions_and_total_counts = {}
        sorted_answers = {}
        user_answers_total_count_list = []
        index_q = 0
        
        for key, value in questions_and_answers.items():
            index_q +=1
            question_id = key
            answers = value["answers"]
            answers_count = {}
            user_answers_total_count = 0
            
            for answer in answers:
                user_answers = _get_user_answers_by_qid_aid(
                                                   question_id=question_id, 
                                                   answer_id=answer.id,
                                                   series_range = series_range)
                answers_count[answer.answer] = user_answers.count()    
                user_answers_total_count += user_answers.count()
                
            questions_and_total_counts[index_q] = {"text": value["question"],
                                             "count": user_answers_total_count}         
            sorted_answers[index_q] = sorted(answers_count.items(), 
                                               key=lambda x:x[1], reverse=True)
    
        # Form pairs with questions numbers Ex. [[1, 2], [3, 4], [5]]
        questions_tuples = houdini_stats.utils.get_list_of_tuples_from_list(
                                                    questions_and_total_counts)
        
        return questions_tuples, questions_and_total_counts, sorted_answers  

    def chart_columns(self):
        return """
         {% col "string" "Answer" %}"{{ val }}"{% endcol %}
         {% col "number" "# of users that selected this choice" %}
                {{ val }}
         {% endcol %}
         """
    
    def chart_options(self):
        return '"out_options"'

    def generate_template_placeholder_code(self):
        """
        Showing pie charts with apprentice survey answers, in pairs of two.
        Two pie charts beside each other.
        """      
        placeholder_html_string = ""
          
        for q_tuple in self.questions_tuples:
            placeholder_html_string += '''<table> 
                     <tr>'''
            count = 1
            
            for key,value in self.questions_and_total_counts.items():
                
                if key == q_tuple[0]:
                    placeholder_html_string+='''
                    <td> 
                     <div class="graph-title">''' + value["text"] + ''' </div>
                      <div>
                      <br>
                       <span> &nbsp;&nbsp;&nbsp;&nbsp; 
                        Total number of answers: ''' + str(value["count"]) + '''
                       </span> 
                      </div>
                      <br>
                      <div id="''' + self.name() + str(count) + '''"> 
                      </div>
                      <br>
                    </td>'''
                
                elif len(q_tuple) == 2 and key == q_tuple[1]:
                    placeholder_html_string+= '''
                    <td>
                     <div class="graph-title">'''+ value["text"] + '''</div>
                     <div>
                     <br>
                      <span> &nbsp;&nbsp;&nbsp;&nbsp; 
                       Total number of answers: ''' +str(value["count"]) + '''
                      </span> 
                     </div>
                     <br>
                     <div id="''' + self.name() + str(count) + '''">
                     </div>
                     <br>
                    </td> '''
                 
                count+= 1
            placeholder_html_string += '</tr> </table>'               
        
        return placeholder_html_string
        
    def generate_template_graph_drawing(self):
        """
        Draw pie charts besides each other.
        """  
        format_dict = dict(
            name=self.name(),
            options=self.chart_options())
        
        template_string = ""
        
        for k, v in self.user_answers.items():
            #series["answer_" + str(k)] = v
            format_dict['index'] = k
            template_string += (
            ("""{%% data report_data.%(name)s.%(index)d "%(name)s%(index)d" %%}\n"""
                    % format_dict) +
                self.chart_columns() + "\n" +
                "{% enddata %}\n" +
                ("""{%% graph "%(name)s%(index)d" "%(name)s%(index)d" %(options)s %%}"""
                    % format_dict)
            ) + "\n" 
                 
        return template_string

  