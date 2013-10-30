from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from static_data import *

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


#-------------------------------------------------------------------------------
def _add_common_context_params(request, series_range, agg=None, params = None):
    """
    Given a dictionary of template context parameters, add entries to it that
    are common to all the pages where the user can log in and return a new
    dictionary.
    """
    new_params = {
        'is_logged_in' : request.user.is_authenticated(),
        'user':request.user,
        'top_menu_options': top_menu_options_ordered,
        "range": series_range,
        "aggregation": agg,
        "date_format": "M j"
        }
    new_params.update(params)
    return new_params

#-------------------------------------------------------------------------------
def _get_active_menu_option_info(selected_menu, selected_option_key):
    """Return a dict with all the information we need from an active menu option.
    For example, for crashes:
    
    dict = {'key': 'uptime',
            'name': 'Session Information',
            'menu_view': 'houdini_reports',
            'prev_option': {'key': 'overview', name: "Overview" },
            'next_option': {'key': 'crashes', name: "Crashes" }
    }
    """
        
    prev_option_key = top_menu_options_nexts_prevs[selected_option_key]['prev']
    prev_option_name =  top_menu_options[selected_menu]['menu_options']\
                                [prev_option_key] if prev_option_key!="" else "" 
    
    next_option_key = top_menu_options_nexts_prevs[selected_option_key]['next']
    next_option_name = top_menu_options[selected_menu]['menu_options']\
                                [next_option_key] if next_option_key!="" else "" 
    
    return  {'key': selected_option_key,
            'name': top_menu_options[selected_menu]['menu_options'][selected_option_key],
            'menu_view': top_menu_options[selected_menu]['menu_view'],
            
            'prev_option': {'key': prev_option_key, 
                            'name': prev_option_name},
            
            'next_option': {'key': next_option_key, 
                            'name': next_option_name}
         
    }
    
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
    
    return render_response("index.html",
                           _add_common_context_params(request,[None, None], None,
                           { 'url': reverse("index"),
                            'show_date_picker': False,
                           }), request
                          )


#-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
@login_required
def hou_reports_view(request, dropdown_option_key):
    """
    Analytics from data we collect from inside Houdini.
    """
    series = {}
    pies = {}
    url_to_reverse = {}
    
    show_date_picker = True   
    
    if not dropdown_option_key:
        dropdown_option_key = "overview"
       
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    
    if dropdown_option_key == "overview":
        series['users_over_time'] = reports.get_users_over_time(
                                                     series_range, aggregation)
        
    if dropdown_option_key == "uptime":
        series['hou_average_session_length'] = reports.average_session_length(
                                                     series_range, aggregation)
        series['hou_average_usage_by_machine'] = reports.average_usage_by_machine(
                                                                   series_range, 
                                                                   aggregation) 
    if dropdown_option_key == "crashes":
        series['hou_crashes_over_time'] = reports.get_hou_crashes_over_time(
                                                                  series_range)    
    if dropdown_option_key == "node_usage":
        show_date_picker = False    
        series['hou_most_popular_nodes'] = reports.most_popular_nodes(
                                                              node_usage_count,
                                                              limit)   
    if dropdown_option_key == "versions_and_builds":
        show_date_picker = False 
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
    
    return render_response("hou_reports.html", 
                           _add_common_context_params(request, series_range, 
                                                      aggregation,
                            {'series': series,
                             'pies': pies,
                             'url': reverse("hou_reports", 
                                           kwargs={"dropdown_option_key": dropdown_option_key}),
                             'dropdown_option_key': dropdown_option_key,
                             'show_date_picker': show_date_picker,
                             'active_houdini': True,
                             'active_menu': top_menu_options['houdini']['menu_name'],
                             'active_menu_option_info': _get_active_menu_option_info(
                                                 'houdini', dropdown_option_key)
                                                  
                             }), request
                           )                          

#-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
@login_required
def hou_licenses_view(request, dropdown_option_key):
    """
    Houdini licenses reports.
    """
    series = {}
    
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    
    if not dropdown_option_key:
        dropdown_option_key = "apprentice_activations"
    
    
    if dropdown_option_key == "downloads":
        
        all_downloads, commercial_downloads, apprentice_downloads, \
        merge = reports.get_num_software_downloads(series_range, aggregation)
        
        series["software_downloads"] = merge 
        
        series["percentages"] = reports.get_percentage_downloads(
                                                  all_downloads, 
                                                  apprentice_downloads,
                                                  commercial_downloads)
    
    if dropdown_option_key == "apprentice_activations":
        
        apprentice_activations = reports.apprentice_activations_over_time(
                                                      series_range, aggregation) 
        apprentice_downloads = reports.get_apprentice_downloads(series_range, 
                                                                    aggregation)
        series['apprentice_lic_over_time'] = reports._merge_time_series([
                                                        apprentice_activations,
                                                        apprentice_downloads])
        series['apprentice_act_percentages'] = reports.get_percentage_of_total(
                                                    apprentice_downloads, 
                                                    apprentice_activations)
    
    return render_response("licenses_reports.html",
                           _add_common_context_params(request, series_range,
                                                      aggregation,
                            {'series': series,
                             'active_licenses': True,
                             'url': reverse("hou_licenses",
                                    kwargs={"dropdown_option_key": dropdown_option_key}),
                             'show_date_picker': True,
                             'active_menu': top_menu_options['licensing']['menu_name'],
                             'active_menu_option_info': _get_active_menu_option_info(
                                                 'licensing', dropdown_option_key)
                             }), request
                           )
                          
#-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
@login_required
def hou_surveys_view(request, dropdown_option_key):
    """
    Houdini surveys reports.
    """
    series = {}
    
    if not dropdown_option_key:
        dropdown_option_key = "sidefx_labs"
        
    show_date_picker = True    
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    count_total =0
    
    if dropdown_option_key == "sidefx_labs":
        hou_engine_reports_data = reports.hou_engine_maya_unity_breakdown(
                                                      series_range, aggregation) 
        count_total = hou_engine_reports_data["count_total"]
        
        series['user_answers_maya_unity_count'] = \
                                   hou_engine_reports_data["user_answers_count"]
        series['user_answers_maya_unity_over_time'] = \
                               hou_engine_reports_data["user_answers_over_time"]
    
    
    if dropdown_option_key == "apprentice_followup":
        show_date_picker = False
        questions_and_total_counts, user_answers = reports.apprentice_followup_survey()
                            
        # This contains the questions text and total count
        series["questions_and_total_counts"] = questions_and_total_counts
        
        # Each set of answers will be passed as a serie key from range
        # (answer_1 to answer_5) because of the way google charts process the
        # data passed.
        for k,v in user_answers.items():
            series["answer_"+str(k)] = v
    
    return render_response("surveys_reports.html", 
                           _add_common_context_params(request, series_range, 
                                                      aggregation,                                                      
                            {'series': series,
                             'active_surveys': True,
                             'url': reverse("hou_surveys", 
                                           kwargs={"dropdown_option_key": dropdown_option_key}),
                             'count_total': count_total,
                             'dropdown_option_key': dropdown_option_key,
                             'show_date_picker': show_date_picker,
                             'active_menu': top_menu_options['surveys']['menu_name'],
                             'active_menu_option_info': _get_active_menu_option_info(
                                                 'surveys', dropdown_option_key)
                             }), request
                           )
    
 #-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
@login_required
def hou_forum_view(request, dropdown_option_key):
    """
    Houdini forum reports.
    """
    series = {}
    
    if not dropdown_option_key:
        dropdown_option_key = "login_registration"
     
    total_forum = 0
    total_openid = 0    
    
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    
    if dropdown_option_key == "login_registration":   
        series["users_forum_openid"] = reports.get_active_users_forum_and_openid(
                                                          series_range, aggregation)
        breakdown, total_forum, total_openid = reports.openid_providers_breakdown(
                                                          series_range, aggregation)   
        series['open_id_breakdown'] = breakdown
    
    return render_response("forum_reports.html", 
                           _add_common_context_params(request, series_range,
                                                      aggregation,
                            {'series': series,
                             'total_forum': total_forum,
                             'total_openid': total_openid,
                             'active_forum': True,
                             'url': reverse("hou_forum",
                                       kwargs={"dropdown_option_key": dropdown_option_key}),
                             'show_date_picker': True,
                             'active_menu': top_menu_options['sidefx.com']['menu_name'],
                             'active_menu_option_info': _get_active_menu_option_info(
                                                 'sidefx.com', dropdown_option_key)
                             }), request
                           )   
                           