from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout

import datetime
import settings
import reports
import urllib

#===============================================================================

# Min mumber of node usage we will show in graph
node_usage_count = 100
# Max number of rows we are going to get by query
limit = 20
# Houdini base products
apprentice = "Apprentice"
commercial = "Commercial"

#Possible products: houdini (Houdini FX), hexper (Houdini FX experimental), 
#hescape (base Houdini), hbatch (Batch), mantra (Mantra), mplay (MPlay)

#===============================================================================

def render_response(page, vals, request):
    """
    Wrapper for Django's render_to_response that creates and passes in
    the context instance object.
    """
    context_instance = RequestContext(request)
    return render_to_response(page, vals, context_instance=context_instance)

#-------------------------------------------------------------------------------
def make_url_absolute(url):
    """
    Make sure a URL starts with '/'.
    """
    if not url.startswith('/'):
        url = "/" + url
    return url         

#-------------------------------------------------------------------------------
def _add_GET_param_to_path(path, param_name):
    """
    To add the given param name to the GET request url
    """
    prefix = ("&" if "?" in path else "?")
    
    return path + prefix + param_name

#-------------------------------------------------------------------------------
def _remove_POST_param_from_path(path, param_name):
    """
    To remove the the given param name from the POST request url
    """
    return path.replace("?" + param_name, "").replace(
                "&" + param_name , "")

#===============================================================================
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Log the user in.
    """
    # Getting the page, so display it.  Also handle the case where they didn't
    # send credentials.
    from django.core.urlresolvers import resolve
        
    if request.method == "GET" or "username" not in request.POST:
        next = (request.GET if request.method == "GET" else request.POST).get(
                "next", reverse("index"))
        
        return render_response("login.html",
                          {"next": next,
                           'is_logged_in' : request.user.is_authenticated(),
                            'user':request.user,
                            'stay_on_login_after_failure': True },   
                            request)  
    # Get the page to redirect to after login.  If they failed to login,
    # we'll go to that path by default but if they attempted to log in from
    # this page originally then we'll stay here.  Otherwise, that other page
    # might redirect them back here and double-encode the "invalid_login"
    # variable.
    next = make_url_absolute(request.POST["next"])
    if "stay_on_login_after_failure" in request.POST:
        path_for_failed_login = (
            request.get_full_path() + "?" +
            urllib.urlencode({"next": next}, True))
    else:
        path_for_failed_login = next

    # Get credentials and authenticate.
    username = request.POST["username"]
    password = request.POST["password"]

    user = authenticate(username=username, password=password)

    # Unrecognized user.
    if user is None:
        # Redirect to the same page, but display a message to say they've
        # logged in incorrectly.
        if "invalid_login" in path_for_failed_login:
            return redirect(path_for_failed_login)
        else:
            return render_response("login.html",
                          {"next": next,
                           'is_logged_in' : False,
                            'user': None,
                            'invalid_login': True },   
                            request)  
            #return redirect(
            #   _add_GET_param_to_path(path_for_failed_login, "invalid_login"))

    # See if the user has been locked out.
    if not user.is_active:
        raise UnauthorizedError(errmsg.AUTH_ACCOUNT_LOCKED, user=username)

    # If the user came from a page that forced the login popup to appear
    # or it has previously appeared because of an invalid login, remove the
    # parameter from the destination page.
    next = _remove_POST_param_from_path(next, "invalid_login")
        
    login(request, user)
    return redirect(next) 

#-------------------------------------------------------------------------------
@require_GET
@login_required
def logout_view(request):
    """
    Log the user out.
    """
    logout(request)
    return redirect(reverse("index"))

#-------------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
@login_required
def index_view(request):
    """
    Home page analytics.
    """
    series = {}
    
    start_request, end_request, series_range, aggregation = reports.get_common_vars(
                                                                        request)
    series['users_over_time'] = reports.get_users_over_time(
                                                     series_range, aggregation)
    
    return render_response("index.html",
                          {"series": series,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_index": True,
                           'is_logged_in' : request.user.is_authenticated(),
                           'url': "/index",
                           'user':request.user},
                            request)
    
#-------------------------------------------------------------------------------  

@require_http_methods(["GET", "POST"])
@login_required
def hou_uptime_view(request):
    """
    Houdini uptime reports.
    """
    series = {}
    
    start_request, end_request, series_range, aggregation = reports.get_common_vars(
                                                                        request)
    
    series['hou_average_session_length'] = reports.average_session_length(
                                                     series_range, aggregation)
    series['hou_average_usage_by_machine'] = reports.average_usage_by_machine(
                                                                   series_range, 
                                                                   aggregation) 
    
    return render_response("uptime.html",
                          {"series": series,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_uptime": True,
                           'is_logged_in' : request.user.is_authenticated(),
                           'url': "/index/uptime",
                           'user':request.user},
                            request)
    
#-------------------------------------------------------------------------------    
@require_http_methods(["GET", "POST"])
@login_required
def hou_crashes_view(request):
    """
    Houdini crashes reports.
    """
    series = {}
    start_request, end_request, series_range, aggregation = reports.get_common_vars(
                                                                        request)

    series['hou_crashes_over_time'] = reports.get_hou_crashes_over_time(
                                                                  series_range)    
    return render_response("hou_crashes_reports.html",
                          {"series": series,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_crashes": True,
                           'is_logged_in' : request.user.is_authenticated(),
                           'url': "/index/crashes",
                           'user':request.user},
                            request)
    
#-------------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
@login_required
def hou_nodes_usage_view(request):
    """
    Houdini nodes usage reports.
    """
    series = {}
    start_request, end_request, series_range, aggregation = reports.get_common_vars(
                                                                        request)
    series['hou_most_popular_nodes'] = reports.most_popular_nodes(
                                                              node_usage_count,
                                                              limit)
    
    return render_response("hou_node_usage_reports.html",
                          {"series": series,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_nodes_usage": True,
                           'is_logged_in' : request.user.is_authenticated(),
                           'url': "/index/node_usage",
                           'user':request.user},
                            request)
    
#-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
@login_required
def hou_versions_and_builds_view(request):
    """
    Houdini nodes usage reports.
    """
    pies = {}
    start_request, end_request, series_range, aggregation = reports.get_common_vars(
                                                                        request)
    # Pie Charts
    pies['houdini_versions'] =  reports.usage_by_hou_version_or_build()
    pies['houdini_builds'] =  reports.usage_by_hou_version_or_build(build=True)
    
    pies['houdini_versions_apprentice'] =  reports.usage_by_hou_version_or_build(
                                               all=False, is_apprentice=True)
    pies['houdini_builds_apprentice'] =  reports.usage_by_hou_version_or_build(
                                                      all=False,
                                                      build=True, 
                                                      is_apprentice=True)
    
    pies['houdini_versions_commercial'] =  reports.usage_by_hou_version_or_build(
                                                                      all=False)
    pies['houdini_builds_commercial'] =  reports.usage_by_hou_version_or_build(
                                                      all=False,
                                                      build=True)
    
    return render_response("hou_versions_builds_reports.html",
                          {"pies": pies,
                           "range": [start_request,end_request] if (start_request and 
                                                        end_request) else None,
                           "date_format": "M j",
                           "active_ver_builds": True,
                           'is_logged_in' : request.user.is_authenticated(),
                           'url': "/index/versions_and_builds",
                           'user':request.user},
                            request)
 
#-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
@login_required
def hou_licenses_view(request):
    """
    Houdini licenses reports.
    """
    series = {}
    
    start_request, end_request, series_range, aggregation = reports.get_common_vars(
                                                                        request)
    series['apprentice_lic_over_time'] = reports.apprentice_activations_over_time(
                                                          series_range, aggregation) 
    
    return render_response("licenses_reports.html",
                          {"series": series,
                           "range": [start_request,end_request] if (
                                       start_request and end_request) else None,
                           "date_format": "M j",
                           "active_licenses": True,
                           'is_logged_in' : request.user.is_authenticated(),
                           'url': "/index/licenses",
                           'user':request.user},
                            request)

