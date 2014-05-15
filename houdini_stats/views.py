from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError 
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
from django.template.loader import get_template
from django.template import Context, Template

import datetime
import urllib
import functools
import sys

from time_series import fill_missing_dates_with_zeros, merge_time_series
from houdini_stats.models import *
from utils import *
# TODO: Rename static_data to report_organization
import static_data
import settings
import reports
import reportclasses

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
# This is the format needed when producing JavaScript dates.
DATE_FORMAT = "M j, Y"

def _add_common_context_params(request, series_range, agg=None, params = None):
    """
    Given a dictionary of template context parameters, add entries to it that
    are common to all the pages where the user can log in and return a new
    dictionary.
    """
    
    new_params = {
            'get_request_string': (
                "?" + urllib.urlencode(request.GET, False)
                if len(request.GET)
                else ""),     
            'is_logged_in' : request.user.is_authenticated(),
            'user':request.user,
            'top_menu_options': _build_permitted_top_menu_options(request.user),
            "range": series_range,
            "aggregation": agg,
            "date_format": DATE_FORMAT,
        }
    new_params.update(params)
    
    return new_params

#-------------------------------------------------------------------------------
def _build_permitted_top_menu_options(user):
    """
    Build the top menu options depending on the groups the user belongs too.
    The groups will determine which permission accesses the user has. 
    """
    return [
        top_menu_info
        for top_menu_info in static_data.top_menu_options.values()
        if _user_in_groups(user, top_menu_info.get("groups", []))]

#-------------------------------------------------------------------------------
def _get_active_menu_option_info(menu, selected_option):
    """Return a dict with all the information we need from an active menu
    option.  For example, for crashes,
        menu might be "houdini"
        selected_option might be "crashes"
    and the result might be
        {
            'name': 'uptime',
            'title': 'Session Information',
            'menu_url': 'houdini/uptime',
            'prev_option': {'name': 'overview', title: "Overview" },
            'next_option': {'name': 'crashes', title: "Crashes" }
        }
    """
    menu_info = static_data.top_menu_options[menu]
    menu_option_infos = menu_info['menu_options']

    menu_selected_option = static_data.find_menu_option_info(
        menu_option_infos, selected_option)

    menu_option_names_to_titles = static_data.menu_option_names_to_titles(
        menu_option_infos)

    if not selected_option in static_data.build_top_menu_options_next_prevs():
        raise Http404

    next_prev_options = static_data.build_top_menu_options_next_prevs()[
        selected_option]

    prev_option_name = next_prev_options['prev']
    prev_option_title = ("" if prev_option_name == ""
        else menu_option_names_to_titles[prev_option_name])
    prev_option_url = ("" if prev_option_name == ""
        else _get_url_for_menu_option(menu, prev_option_name))

    next_option_name = next_prev_options['next']
    next_option_title = ("" if next_option_name == ""
        else menu_option_names_to_titles[next_option_name])
    next_option_url = ("" if next_option_name == ""
        else _get_url_for_menu_option(menu, next_option_name))

    return {
        'name': selected_option,
        'title': menu_option_names_to_titles[selected_option],
        'menu_url': _get_url_for_menu_option(menu, selected_option),
        'prev_option': {
            'url': prev_option_url,
            'title': prev_option_title,
        },
        'next_option': {
            'url': next_option_url,
            'title': next_option_title,
        }
    }

#-------------------------------------------------------------------------------
def _get_url_for_menu_option(menu, option_name):
    return reverse("generic_report", args=[menu, option_name])

#-------------------------------------------------------------------------------
def _user_in_groups(user, group_names):
    """
    Function to verify if a user belongs to any of the groups given.
    """
    # If the use is staff (admin, root) we dont need to verify the groups
    if user.is_staff:
        return True
    
    return set(group.name
        for group in user.groups.all()).intersection(group_names)

#-------------------------------------------------------------------------------
def validate_user_is_in_group(request, group_names):
    if not request.user.is_active or not _user_in_groups(
            request.user, group_names):
        raise PermissionDenied()

def user_access(group_names=['staff', 'r&d']):
    """
    Decorator for views that checks if the user has access to the reports
    in Stats, depending on which groups they belong too.
    """
    def wrapper(view_function):
        @functools.wraps(view_function)
        def _checklogin(request, *args, **kwargs):
            validate_user_is_in_group(request, group_names)
            return view_function(request, *args, **kwargs)

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
		'show_agg_widget' : False
            }),
        request)

#-------------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
@login_required
def generic_report_view(request, menu_name, dropdown_option):
    series_range, aggregation = get_common_vars_for_charts(
        request, minimum_start_date=settings.HOUDINI_REPORTS_START_DATE)

    # TODO: Determine the proper group names for the intersection of the
    #       reports.
    validate_user_is_in_group(request, ['staff', 'r&d'])

    # Find the report classes for this dropdown and create an instance of each
    # report.
    report_class_names = static_data.report_classes_for_menu_option(
        menu_name, dropdown_option)
    report_classes = [
        getattr(reportclasses, report_class_name)
        for report_class_name in report_class_names]
    reports = [report_class() for report_class in report_classes]

    # Run the queries for each report.
    report_data = {}
    for report in reports:
        report_data[report.name()] = report.get_data(series_range, aggregation)

    # Generate the html for the charts.
    charts = render_chart_template(reports, report_data)

    return render_response(
        "generic_chart.html",
        _add_common_context_params(request, series_range, aggregation, {
            'report_data': report_data,
            'url': reverse(
                "generic_report",
                kwargs=dict(
                    menu_name=menu_name, dropdown_option=dropdown_option)),
            'dropdown_option_key': dropdown_option,
            'show_date_picker':
                any(report.show_date_picker() for report in reports),
            'show_agg_widget':
                any(report.supports_aggregation() for report in reports),
            'active_menu': menu_name,
            'active_menu_option_info':
                _get_active_menu_option_info(menu_name, dropdown_option),
            'charts': charts,
        }),
        request)

def find_template_path(template_file_name):
    for template_dir in settings.TEMPLATE_DIRS:
        template_path = os.path.join(template_dir, template_file_name)
        if os.path.exists(template_path):
            return template_path

    return None

def render_chart_template(reports, report_data):
    chart_placeholders = ""
    for report in reports:
        chart_placeholders += report.generate_template_placeholder_code()

    chart_drawing = ""
    for report_number, report in enumerate(reports):
        chart_drawing += report.generate_template_graph_drawing(report_number)

    return render_template_from_string(
        """
        {% load googlecharts %}

        """ + chart_placeholders + """
        {% googlecharts %}
            {% include 'googlecharts_options.html' %}
            """ + chart_drawing + """
        {% endgooglecharts %}
        """,
        dict(
            chart_placeholders=chart_placeholders,
            chart_drawing=chart_drawing,
            report_data=report_data,
            date_format=DATE_FORMAT,
        ))

def render_template_from_string(string, context_vars):
    return Template(string).render(Context(context_vars))

@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
def hou_reports_view(request, dropdown_option_key):
    """
    Analytics from data we collect from inside Houdini.
    """
    
    # Max number of rows we are going to get by query
    limit = 20

    series = {}
    series_range, aggregation = get_common_vars_for_charts(request)
    pies = {}
    url_to_reverse = {}
    show_date_picker = True
    show_agg_widget = True

    # Events serie 
    events_to_annotate = reports.get_events_in_range(series_range, aggregation)
    
    if not dropdown_option_key:
        dropdown_option_key = "downloads"
        
    if dropdown_option_key == "downloads":
        
        all_downloads = reports.get_all_houdini_downloads(series_range, 
                                                                    aggregation)
        apprentice_downloads = reports.get_houdini_apprentice_downloads(
                                                      series_range, aggregation)
        commercial_downloads = reports.get_houdini_commercial_downloads(
                                                      series_range, aggregation) 
        
        series["software_downloads"] = reports.get_merge_houdini_downloads(
                                all_downloads, apprentice_downloads, 
                                commercial_downloads, events_to_annotate) 
        
        series["percentages"] = reports.get_percentage_two_series_one_total(
                      all_downloads, apprentice_downloads, commercial_downloads)
       
    if not dropdown_option_key == "downloads":
        # We started collecting meaningful data from Houdini at a different
        # date thats why we pass an additional param to the function.
        series_range, aggregation = get_common_vars_for_charts(
            request, minimum_start_date=settings.HOUDINI_REPORTS_START_DATE)
    if dropdown_option_key == "usage":
        series['new_machines_over_time'] = reports.get_new_machines_over_time(
            series_range, aggregation)
        series['machines_sending_stats_per_day'] = \
            reports.get_num_of_machines_sending_stats_per_day(
                series_range, aggregation)
        series['avg_of_individual_successful_conn_per_day'] = \
            reports.get_avg_num_of_individual_successful_conn_per_day(
                series_range, aggregation)
            
    if dropdown_option_key == "uptime":
        series['hou_average_session_length'] = (
            reports.average_session_length(series_range, aggregation))
        series['hou_average_usage_by_machine'] = (
            reports.average_usage_by_machine(series_range, aggregation))
    
    if dropdown_option_key == "crashes":
        series['hou_crashes_over_time'] = (
            reports.get_orm_data_for_report(HoudiniCrash.objects.all(), 'date', 
                                            series_range, aggregation))
        
        series['hou_avg_crashes_by_same_machine']=\
                        reports.get_avg_num_of_crashes_by_same_machine_per_day(
                                                      series_range, aggregation)
        pies['hou_crashes_by_os'], pies['hou_crashes_by_os_detailed']=\
                      reports.get_hou_crashes_by_os(series_range, aggregation)
                      
        pies['hou_crashes_by_product']= reports.get_hou_crashes_by_product(
                                                      series_range, aggregation)
         
    if dropdown_option_key == "tools_usage":
        show_date_picker = True
        show_agg_widget = False
        series['hou_most_popular_tools'] = (
            reports.most_popular_tools(series_range, aggregation))
        series['hou_most_popular_tools_shelf'] = (
            reports.most_popular_tools(series_range, aggregation, "(1)"))
        series['hou_most_popular_tools_viewer'] = (
            reports.most_popular_tools(series_range, aggregation, "(2)"))
        series['hou_most_popular_tools_network'] = (
            reports.most_popular_tools(series_range, aggregation, "(3)"))
        
    if dropdown_option_key == "versions_and_builds":
        show_date_picker = False
        show_agg_widget = False

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
            'show_agg_widget': show_agg_widget,
            'active_menu': static_data.top_menu_options['houdini']['menu_name'],
            'active_menu_option_info':
                _get_active_menu_option_info('houdini', dropdown_option_key),
        }),
        request)

#------------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
def hou_apprentice_view(request, dropdown_option_key):
    """Houdini Apprentice."""
    
    series = {}
    series_range, aggregation = get_common_vars_for_charts(request)
    
    show_agg_widget = True
    
    # Events serie 
    events_to_annotate = reports.get_events_in_range(series_range, aggregation)

    if not dropdown_option_key:
        dropdown_option_key = "apprentice_activations"

    if dropdown_option_key == "apprentice_activations":
        apprentice_downloads = reports.get_houdini_apprentice_downloads(
            series_range, aggregation)
        
        apprentice_activations_new = (
            reports.apprentice_new_activations_over_time(
                series_range, aggregation))
        
        apprentice_activations_total = (
            reports.apprentice_total_activations_over_time(
                series_range, aggregation))
        
        # Difference between apprentice activations total and the new
        # new activations
        apprentice_reactivations = reports.get_difference_between_series(
            apprentice_activations_total, 
            apprentice_activations_new)
        
        series['apprentice_lic_over_time'] = merge_time_series([
            apprentice_activations_total, 
            events_to_annotate,
            apprentice_activations_new,
            apprentice_reactivations,
            apprentice_downloads,
        ])
        
        series['apprentice_percentages_new_from_downloads'] = (
            reports.get_percentage_of_total(
                apprentice_downloads, apprentice_activations_new))
        
        series["apprentice_act_percentages"] = (
            reports.get_percentage_two_series_one_total(
                apprentice_activations_total,
                apprentice_activations_new, 
                apprentice_reactivations))
    
    if dropdown_option_key == "apprentice_hd":
        apprentice_hd_licenses = reports.get_apprentice_hd_licenses_over_time(
            series_range, aggregation)
        
        series['apprentice_hd_lic'] = merge_time_series(
            [apprentice_hd_licenses, events_to_annotate]) 
        series['apprentice_hd_lic_cumu'] = (
            reports.get_apprentice_hd_licenses_cumulative(
                apprentice_hd_licenses, series_range[0]))
    
    if dropdown_option_key == "apprentice_heatmap":
        show_agg_widget = False
            
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
                'show_agg_widget': show_agg_widget,
                'active_menu':
                    static_data.top_menu_options['apprentice']['menu_name'],
                'active_menu_option_info': _get_active_menu_option_info(
                'apprentice', dropdown_option_key),
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

    series_range, aggregation = get_common_vars_for_charts(request)
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

        apprentice_activations = reports.apprentice_total_activations_over_time(
            series_range, aggregation)
        series['survey_counts_percentages'] = reports.get_percentage_of_total(
            apprentice_activations, user_counts)

        merge_time_series([user_counts, apprentice_activations])

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
                'show_date_picker': True,
                'show_agg_widget': True,
                'active_menu':
                    static_data.top_menu_options['surveys']['menu_name'],
                'active_menu_option_info': _get_active_menu_option_info(
                    'surveys', dropdown_option_key),
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
    series_range, aggregation = get_common_vars_for_charts(request)
    events_to_annotate = reports.get_events_in_range(series_range, aggregation,
                                                     fill_empty_string = False)

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
                'show_agg_widget': True,
                'active_menu':
                    static_data.top_menu_options['sidefx.com']['menu_name'],
                'active_menu_option_info': _get_active_menu_option_info(
                    'sidefx.com', dropdown_option_key),
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
    series_range, aggregation = get_common_vars_for_charts(request)
    
    lat_longs = []
    
    if option == "apprentice_heatmap":
        lat_longs = reports.get_apprentice_activations_by_geo(series_range, 
                                                              aggregation)
    return render_response(
        "heatmap.html", {
            "lat_longs": lat_longs,
        },
        request)    
    
#-------------------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
@login_required
def custom_500(request):
    t = get_template('500.html')
    type, value, tb = sys.exc_info()
    
    return HttpResponseServerError(t.render(Context({
    'exception_value': value,
})))    
    
    
