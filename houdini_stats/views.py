from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import (
    require_GET, require_POST, require_http_methods)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied

import datetime
import urllib
import functools

import settings
from static_data import top_menu_options
import reports

#===============================================================================

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
            'get_request_string': (
                     "?" + urllib.urlencode(request.GET, False) if len(request.GET) 
                     else ""),     
            'is_logged_in' : request.user.is_authenticated(),
            'user':request.user,
            'top_menu_options': _build_top_menu_options(request.user, 
                                                    top_menu_options.values()),
            "range": series_range,
            "aggregation": agg,
            "date_format": "M j, Y"
        }
    new_params.update(params)
    
    return new_params

#-------------------------------------------------------------------------------
def _build_top_menu_options(user, top_menu_options_values):
    """
    Build the top menu options depending on the groups the user belongs too.
    The groups will determine which permission accesses the user has. 
    """
    top_menu_options_final = []
    
    for top_menu_info in top_menu_options_values:
        if top_menu_info.has_key('groups'):
            group_names = top_menu_info['groups']
            if _user_in_groups(user, group_names):
                top_menu_options_final.append(top_menu_info)
    return top_menu_options_final         
            
#-------------------------------------------------------------------------------
def _get_top_menu_options_next_prevs():
    "Get a dictionary with all the menu options nexts and previous."
    
    top_menu_options_nexts_prevs = {}
    for top_menu_name, top_menu_info in top_menu_options.items():
        options = top_menu_info["menu_options"].keys()
        for index, option in enumerate(options):
            prev_option = (options[index-1] if index-1 >= 0 else "")
            next_option = (options[index+1] if index+1 < len(options) else "")
            top_menu_options_nexts_prevs[option] = {
                "next": next_option,
                "prev": prev_option}

    return top_menu_options_nexts_prevs

#-------------------------------------------------------------------------------
def _get_active_menu_option_info(selected_menu, selected_option_key):
    """Return a dict with all the information we need from an active menu
    option.  For example, for crashes:

    dict = {'key': 'uptime',
            'name': 'Session Information',
            'menu_view': 'houdini_reports',
            'prev_option': {'key': 'overview', name: "Overview" },
            'next_option': {'key': 'crashes', name: "Crashes" }
    }
    """
    selected_top_menu_info = top_menu_options[selected_menu]
    menu_options = selected_top_menu_info['menu_options']

    next_prev_options = _get_top_menu_options_next_prevs()[selected_option_key]

    prev_option_key = next_prev_options['prev']
    prev_option_name = ("" if prev_option_key == ""
        else menu_options[prev_option_key])

    next_option_key = next_prev_options['next']
    next_option_name = ("" if next_option_key == ""
        else menu_options[next_option_key])

    return {
        'key': selected_option_key,
        'name': selected_top_menu_info['menu_options'][selected_option_key],
        'menu_view': selected_top_menu_info['menu_view'],
            'prev_option': {
                'key': prev_option_key,
                'name': prev_option_name
            },
            'next_option': {
                'key': next_option_key,
                'name': next_option_name
            }
        }

#-------------------------------------------------------------------------------
def _user_in_groups(user, group_names):
    """
    Function to verify if a user belongs to any of the groups given.
    """
    # If the use is staff (admin, root) we dont need to verify the groups
    if user.is_staff:
        return True
    
    return set(group.name for group in user.groups.all()).intersection(group_names)                                                     
    
#-------------------------------------------------------------------------------
def user_access(group_names=['staff', 'r&d']):
    """
    Decorator for views that checks if the user has access to the reports
    in Stats, depending on which groups they belong too.
    """
    
    def wrapper(view_function):
        
        @functools.wraps(view_function)
        def _checklogin(request, *args, **kwargs):
            
            if request.user.is_active and _user_in_groups(request.user, 
                                                          group_names):
                return view_function(request, *args, **kwargs)
            raise PermissionDenied()
        return _checklogin
    return wrapper

#===============================================================================
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Log the user in."""
    # Getting the page, so display it.  Also handle the case where they didn't
    # send credentials.
    from django.core.urlresolvers import resolve

    if request.method == "GET" or "username" not in request.POST:
        next = (request.GET if request.method == "GET" else request.POST).get(
            "next", reverse("index"))

        return render_response(
            "login.html",
            {
                "next": next,
                'is_logged_in' : request.user.is_authenticated(),
                'user':request.user,
                'stay_on_login_after_failure': True
            },
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
    if user is None:
        # Unrecognized user.  Redirect to the same page, but display a message
        # to say they've logged in incorrectly.
        if "invalid_login" in path_for_failed_login:
            return redirect(path_for_failed_login)
        else:
            return render_response("login.html",
                {
                    "next": next,
                    'is_logged_in' : False,
                    'user': None,
                    'invalid_login': True
                },
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
    """Log the user out."""
    logout(request)
    return redirect(reverse("index"))

#-------------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
@login_required
def index_view(request):
    """Home page analytics."""
    return render_response(
        "index.html",
        _add_common_context_params(
            request,
            [None, None],
            None,
            {
                'url': reverse("index"),
                'show_date_picker': False,
            }),
        request)

#-------------------------------------------------------------------------------  
@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
def hou_reports_view(request, dropdown_option_key):
    """
    Analytics from data we collect from inside Houdini.
    """
    # Min mumber of tool usage we will show in graph
    tool_usage_count = 1

    # Max number of rows we are going to get by query
    limit = 20

    series = {}
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    pies = {}
    url_to_reverse = {}
    show_date_picker = True

    if aggregation is None:
        aggregation = "daily"
    
    # Events serie 
    events_to_annotate = reports.get_events_in_range(series_range)
    events_to_annotate_filled = reports._fill_missing_dates_with_zeros(
                                           events_to_annotate, aggregation[:-2],
                                                             series_range, True) 
    if not dropdown_option_key:
        dropdown_option_key = "downloads"

    if dropdown_option_key == "downloads":
        all_downloads, commercial_downloads, apprentice_downloads, merge = \
            reports.get_num_software_downloads(
                series_range, aggregation, events_to_annotate_filled)

        series["software_downloads"] = merge

        series["percentages"] = reports.get_percentage_downloads(
            all_downloads,
            apprentice_downloads,
            commercial_downloads)

    if dropdown_option_key == "usage":
        series['users_over_time'] = reports.get_users_over_time(
            series_range, aggregation)

    if dropdown_option_key == "uptime":
        series['hou_average_session_length'] = (
            reports.average_session_length(series_range, aggregation))
        series['hou_average_usage_by_machine'] = (
            reports.average_usage_by_machine(series_range, aggregation))

    if dropdown_option_key == "crashes":
        series['hou_crashes_over_time'] = (
            reports.get_hou_crashes_over_time(series_range))

    
    if dropdown_option_key == "tools_usage":
        
        show_date_picker = False
        series['hou_most_popular_tools'] = (
            reports.most_popular_tools(tool_usage_count, limit))
        series['hou_most_popular_tools_shelf'] = (
            reports.most_popular_tools(tool_usage_count, limit, 1))
        series['hou_most_popular_tools_viewer'] = (
            reports.most_popular_tools(tool_usage_count, limit, 2))
        series['hou_most_popular_tools_network'] = (
            reports.most_popular_tools(tool_usage_count, limit, 3))
        
        print series
    
    if dropdown_option_key == "versions_and_builds":
        show_date_picker = False

        # Pie Charts
        pies['houdini_versions'] = reports.usage_by_hou_version_or_build()
        pies['houdini_builds'] = reports.usage_by_hou_version_or_build(
            build=True)
        pies['houdini_versions_apprentice'] = (
            reports.usage_by_hou_version_or_build(
                all=False,
                is_apprentice=True))
        pies['houdini_builds_apprentice'] =  (
            reports.usage_by_hou_version_or_build(
                all=False,
                build=True,
                is_apprentice=True))
        pies['houdini_versions_commercial'] = (
            reports.usage_by_hou_version_or_build(
                all=False))
        pies['houdini_builds_commercial'] = (
            reports.usage_by_hou_version_or_build(
                all=False,
                build=True))

    return render_response(
        "hou_reports.html",
        _add_common_context_params(request, series_range, aggregation, {
            'series': series,
            'pies': pies,
            'url': reverse(
                "hou_reports",
                kwargs={"dropdown_option_key": dropdown_option_key}),
            'dropdown_option_key': dropdown_option_key,
            'show_date_picker': show_date_picker,
            'active_houdini': True,
            'active_menu': top_menu_options['houdini']['menu_name'],
            'active_menu_option_info':
                _get_active_menu_option_info('houdini', dropdown_option_key)
        }),
        request)

#------------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
def hou_apprentice_view(request, dropdown_option_key):
    """Houdini Apprentice."""
    
    series = {}
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    
    if aggregation is None:
        aggregation = "daily"
    
    # Events serie 
    events_to_annotate = reports.get_events_in_range(series_range)
    events_to_annotate_filled = reports._fill_missing_dates_with_zeros(
                                           events_to_annotate, aggregation[:-2],
                                                             series_range, True) 
    if not dropdown_option_key:
        dropdown_option_key = "apprentice_activations"

    if dropdown_option_key == "apprentice_activations":
        apprentice_activations = reports.apprentice_activations_over_time(
                                                      series_range, aggregation)
        
        apprentice_downloads = reports.get_apprentice_downloads(series_range, 
                                                                   aggregation)
        
        series['apprentice_lic_over_time'] = reports._merge_time_series(
            [apprentice_downloads, events_to_annotate_filled,
             apprentice_activations])
        
        series['apprentice_act_percentages'] = reports.get_percentage_of_total(
            apprentice_downloads, apprentice_activations)

    if dropdown_option_key == "apprentice_hd":
        apprentice_hd_licenses = reports.get_apprentice_hd_licenses_over_time(
            series_range, aggregation)
        
        series['apprentice_hd_lic'] = reports._merge_time_series(
            [apprentice_hd_licenses, events_to_annotate_filled]) 
        series['apprentice_hd_lic_cumu'] = (
            reports.get_apprentice_hd_licenses_cumulative(
                apprentice_hd_licenses, series_range[0]))
    
    return render_response(
        "apprentice_reports.html",
        _add_common_context_params(
            request,
            series_range,
            aggregation,
            {
                'series': series,
                'events': events_to_annotate,
                'active_licenses': True,
                'url': reverse(
                    "hou_apprentice",
                    kwargs={"dropdown_option_key": dropdown_option_key}),
                'show_date_picker': True,
                'active_menu': top_menu_options['apprentice']['menu_name'],
                'active_menu_option_info': _get_active_menu_option_info(
                'apprentice', dropdown_option_key),
                'plot_three': True
            }),
            request)    

#------------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
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

        series['user_answers_maya_unity_count'] = (
            hou_engine_reports_data["user_answers_count"])
        series['user_answers_maya_unity_over_time'] = (
            hou_engine_reports_data["user_answers_over_time"])

    if dropdown_option_key == "apprentice_followup":
        # For apprentice activations and vs count of users who replied survey
        user_counts = reports.apprentice_replied_survey_counts(
            series_range, aggregation)

        apprentice_activations = reports.apprentice_activations_over_time(
            series_range, aggregation)
        series['survey_counts_percentages'] = reports.get_percentage_of_total(
            apprentice_activations, user_counts)

        reports._merge_time_series([user_counts, apprentice_activations])

        # For apprentice survey pie charts
        questions_tuples, questions_and_total_counts, user_answers = (
            reports.apprentice_followup_survey(series_range, aggregation))

        # This contains the questions text and total count
        series["questions_and_total_counts"] = questions_and_total_counts
        # Passing the questions tuples in the series dictionary too
        series["questions_tuples"] = questions_tuples

        # Each set of answers will be passed as a serie key from range
        # (answer_1 to answer_5) because of the way google charts process the
        # data passed.
        for k, v in user_answers.items():
            series["answer_" + str(k)] = v

    return render_response(
        "surveys_reports.html",
        _add_common_context_params(
            request,
            series_range,
            aggregation,
            {
                'series': series,
                'active_surveys': True,
                'url': reverse(
                    "hou_surveys",
                    kwargs={"dropdown_option_key": dropdown_option_key}),
                'count_total': count_total,
                'dropdown_option_key': dropdown_option_key,
                'show_date_picker': show_date_picker,
                'active_menu': top_menu_options['surveys']['menu_name'],
                'active_menu_option_info': _get_active_menu_option_info(
                    'surveys', dropdown_option_key),
                     'plot_three': False
            }),
            request)

#-----------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
def hou_forum_view(request, dropdown_option_key):
    """
    Houdini forum reports.
    """
    series = {}
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    events_to_annotate = reports.get_events_in_range(series_range)

    if not dropdown_option_key:
        dropdown_option_key = "login_registration"

    total_forum = 0
    total_openid = 0

    if dropdown_option_key == "login_registration":
        series["users_forum_openid"] = (
            reports.get_active_users_forum_and_openid(
                series_range, aggregation, events_to_annotate))

        breakdown, total_forum, total_openid = (
            reports.openid_providers_breakdown(
                series_range, aggregation))
        series['open_id_breakdown'] = breakdown

    return render_response(
        "forum_reports.html",
        _add_common_context_params(
            request, series_range, aggregation,
            {
                'series': series,
                'events': events_to_annotate,
                'total_forum': total_forum,
                'total_openid': total_openid,
                'active_forum': True,
                'url': reverse(
                    "hou_forum",
                    kwargs={"dropdown_option_key": dropdown_option_key}),
                'show_date_picker': True,
                'active_menu': top_menu_options['sidefx.com']['menu_name'],
                'active_menu_option_info': _get_active_menu_option_info(
                    'sidefx.com', dropdown_option_key),
                'plot_three': True
            }),
            request)

#-----------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
def hou_heatmap_view(request, option):
    """
    View to visualize Heatmaps.
    """
    series = {}
    series_range, aggregation = reports.get_common_vars_for_charts(request)
    
    lat_longs = []
    
    if option == "apprentice_heatmap":
        lat_longs = reports.get_apprentice_activations_by_geo(series_range)
    return render_response(
        "heatmap.html", {
            "lat_longs": lat_longs,
        },
        request)    
