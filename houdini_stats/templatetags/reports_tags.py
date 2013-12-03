
from django import template

register = template.Library()

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