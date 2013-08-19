
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

import datetime
import settings
import reports
from api import API

#===============================================================================

# Min mumber of node usage we will show in graph
node_usage_count = 5
# Max number of rows we are going to get by query
limit = 20
# Houdini base products
apprentice = "Apprentice"
commercial = "Houdini FX"

#===============================================================================

def render_response(page, vals, request):
    """
    Wrapper for Django's render_to_response that creates and passes in
    the context instance object.
    """
    context_instance = RequestContext(request)
    return render_to_response(page, vals, context_instance=context_instance)

#------------------------------------------------------------------------------- 
def _get_start_request(request):
    """
    Get start date from the request.
    """
    return request.GET.get("start", None)

#------------------------------------------------------------------------------- 
def _get_end_request(request):
    """
    Get end date from the request.
    """
    return request.GET.get("end", None)

#-------------------------------------------------------------------------------     
def _series_range(start_request, end_request):
    """
    Series range parameter to pass for the reports
    """    
    # Get the time interval for the graphs
    if start_request is not None:
        t = time.strptime(start_request, "%d/%m/%Y")
        start = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    else:
        # We launched the site in August
        start = settings.STARTING_DATE

    if end_request is not None:
        t = time.strptime(end_request, "%d/%m/%Y")
        end = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    else:
        end = datetime.datetime.now()
    
    # By default, time_series will get the count
    return [start, end]

#------------------------------------------------------------------------------- 
def _get_aggregation(request):
    """
    Get aggregation from the request.
    """
    # For aggregation 
    valid_agg = ["monthly", "weekly", "yearly"]
    if "ag" not in request:
        return None
    
    aggregation = request.GET["ag"].lower()    
    return aggregation if aggregation in valid_agg else None

#------------------------------------------------------------------------------- 
def _get_common_vars(request):
    """
    Get all variables that will be used for the reports.
    """
    return _get_start_request(request), _get_end_request(request), \
           _series_range(_get_start_request(request), 
                         _get_end_request(request)), \
           _get_aggregation(request.GET)

#===============================================================================
@require_http_methods(["POST"])
@csrf_exempt
def api_view(request):
    """
    Dispatch requests for API URLs.
    """
    api = API()
    return api.dispatch(request)

#-------------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
def index_view(request):
    """
    Home page analytics.
    """
    series = {}
    pies = {}
    
    start_request, end_request, series_range, aggregation = _get_common_vars(
                                                                        request)

    series['hou_average_session_length'] = reports.average_session_length(
                                                     series_range, aggregation)
    series['hou_average_usage_by_machine'] = reports.average_usage_by_machine(
                                                          series_range[0],
                                                          series_range[1]) 
    
   # Pie Charts
    pies['houdini_versions'] =  reports.usage_by_hou_version_or_build()
    pies['houdini_builds'] =  reports.usage_by_hou_version_or_build(True)
    
    pies['houdini_versions_apprentice'] =  reports.usage_by_hou_version_or_build(
                                               hou_product=apprentice)
    pies['houdini_builds_apprentice'] =  reports.usage_by_hou_version_or_build(
                                                      build=True, 
                                                      hou_product=apprentice)
    
    pies['houdini_versions_commercial'] =  reports.usage_by_hou_version_or_build(
                                               hou_product=commercial)
    pies['houdini_builds_commercial'] =  reports.usage_by_hou_version_or_build(
                                                      build=True, 
                                                      hou_product=commercial)
    
    return render_response("index.html",
                          {"series": series,
                           "pies": pies,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_index": True},
                            request)
    
#-------------------------------------------------------------------------------    
@require_http_methods(["GET", "POST"])
def hou_crashes_view(request):
    """
    Houdini crashes reports.
    """
    series = {}
    start_request, end_request, series_range, aggregation = _get_common_vars(
                                                                        request)

    series['hou_crashes_over_time'] = reports.get_hou_crashes_over_time(
                                                                  series_range)    
    return render_response("hou_crashes_reports.html",
                          {"series": series,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_crashes": True},
                            request)
    
#-------------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
def hou_nodes_usage_view(request):
    """
    Houdini nodes usage reports.
    """
    series = {}
    start_request, end_request, series_range, aggregation = _get_common_vars(
                                                                        request)
    series['hou_most_popular_nodes'] = reports.most_popular_nodes(
                                                              node_usage_count,
                                                              limit)
    
    return render_response("hou_node_usage_reports.html",
                          {"series": series,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_nodes_usage": True},
                            request)
    
#-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
def hou_versions_and_builds_view(request):
    """
    Houdini nodes usage reports.
    """
    pies = {}
    start_request, end_request, series_range, aggregation = _get_common_vars(
                                                                        request)
    # Pie Charts
    pies['houdini_versions'] =  reports.usage_by_hou_version_or_build()
    pies['houdini_builds'] =  reports.usage_by_hou_version_or_build(True)
    
    pies['houdini_versions_apprentice'] =  reports.usage_by_hou_version_or_build(
                                               hou_product=apprentice)
    pies['houdini_builds_apprentice'] =  reports.usage_by_hou_version_or_build(
                                                      build=True, 
                                                      hou_product=apprentice)
    
    pies['houdini_versions_commercial'] =  reports.usage_by_hou_version_or_build(
                                               hou_product=commercial)
    pies['houdini_builds_commercial'] =  reports.usage_by_hou_version_or_build(
                                                      build=True, 
                                                      hou_product=commercial)
    
    return render_response("hou_versions_builds_reports.html",
                          {"pies": pies,
                           "range": [start_request,end_request] if (start_request and 
                                                        end_request) else None,
                           "date_format": "M j",
                           "active_ver_builds": True},
                            request)
   
    