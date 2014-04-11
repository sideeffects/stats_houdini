
from django import template

register = template.Library()

#-------------------------------------------------------------------------------
@register.inclusion_tag('events_annotate.html')
def show_annotation_title(events, date):
    """
    To show the annotation (event) title when we hover the mouse over the 
    annotated date.
    """
    text = str(date.date())
    
    for e in events:
        if e[0] == date:
            text = str(date.date()) + " - " + e[1]
            break
    
    return {'value': text}

#-------------------------------------------------------------------------------
@register.simple_tag
def aggregated_date(field_name, aggregation="daily"):
    """
    Return the bit of query for the datetime aggregation.
    """
    aggregation = aggregation.lower()    
    
    # Validation 
    valid_agg = ["monthly", "weekly", "yearly", "daily"]
    assert (aggregation in valid_agg)
    
    #  By default we assume it is a daily aggregation
    agg_date = "cast(cast({0} AS date) AS datetime)" . format(field_name) 
    
    if aggregation== "monthly":
        agg_date = """cast(concat(date_format({0}, '%%Y-%%c'), '-01') AS 
                      datetime)""" . format(field_name)
        
    elif aggregation== "weekly":
        # The aggregation query will return the first day of each week
        agg_date = """
                   cast( DATE_SUB( DATE_ADD( MAKEDATE( year({0}),1),
                   INTERVAL week({0}) WEEK) ,
                   INTERVAL WEEKDAY( DATE_ADD(MAKEDATE(year({0}),1),
                   INTERVAL week({0}) WEEK ) )
                   DAY ) AS datetime ) """ . format(field_name)
    
    elif aggregation== "yearly":
        agg_date = """cast(concat(date_format({0}, '%%Y'), '-01-01') AS 
                      datetime)""" . format(field_name)               
    
    return agg_date

#-------------------------------------------------------------------------------
@register.simple_tag
def where_between(field_name, start_date, end_date):
    """
    Return the bit of query for the dates interval.
    """
    
    str = """ {0} between date_format('{1}', '%%Y-%%c-%%d %%H:%%i:%%S')
                and date_format('{2}', '%%Y-%%c-%%d 23:%%i:%%S')
           """ .format( field_name,
                        start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        end_date.strftime("%Y-%m-%d %H:%M:%S"))
    
    return str 
    