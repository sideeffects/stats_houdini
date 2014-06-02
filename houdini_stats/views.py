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
import time_series
from houdini_stats.models import *
from utils import *
# TODO: Rename static_data to report_organization
import static_data
import settings
import genericreportclasses
import reports.houdini
import reports.downloads
import reports.apprentice
import reports.surveys
import reports.sidefx_website


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
    series_range, aggregation = get_common_vars_for_charts(request)

    # Making sure at least the first option will always be selected
    if dropdown_option=='':
        dropdown_option = static_data.top_menu_options[menu_name]\
                                                         ["menu_options"][0][0]
        
    # TODO: Determine the proper group names for the intersection of the
    # reports
    validate_user_is_in_group(request, ['staff', 'r&d'])

    # Find the report classes for this dropdown and create an instance of each
    # report.
    report_class_names = static_data.report_classes_for_menu_option(
        menu_name, dropdown_option)
    
    report_classes = [
        genericreportclasses.find_report_class(report_class_name)
        for report_class_name in report_class_names]
    reports = [report_class() for report_class in report_classes]

    # Run the queries for each report.
    report_data = {}
    for report in reports:
        # If report is heatmap we dont get that data her but later on
        # when the heatmap view is called
        if not report.is_heatmap():
            report_data[report.name()] = report.get_data(series_range, aggregation)

    # Generate the html for the charts.
    charts = render_chart_template(reports, report_data)

    return render_response(
        "generic_chart.html",
        _add_common_context_params(request, series_range, aggregation, {
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
#-------------------------------------------------------------------------------

def find_template_path(template_file_name):
    for template_dir in settings.TEMPLATE_DIRS:
        template_path = os.path.join(template_dir, template_file_name)
        if os.path.exists(template_path):
            return template_path

    return None
#-------------------------------------------------------------------------------

def render_chart_template(reports, report_data):
    """
    Render the template for the charts
    """
    chart_placeholders = ""
    chart_drawing = ""
    for report in reports:
        chart_placeholders += report.generate_template_placeholder_code()
        chart_drawing += report.generate_template_graph_drawing()
    
    template_string = """
                        {% load reports_tags %}
                        {% load googlecharts %}
                
                        """ + chart_placeholders + """
                        {% googlecharts %}
                            {% include 'googlecharts_options.html' %}
                            """ + chart_drawing + """
                        {% endgooglecharts %}
                        """
    # Check of there is a heatmap in the set of reports
    is_heatmap =  any(report.is_heatmap() for report in reports)
    
    if is_heatmap:
        # If the report is a heatmap we dont need to include googlecharts
        template_string = chart_placeholders + chart_drawing
    
    return render_template_from_string(
        template_string,
        dict(
            chart_placeholders=chart_placeholders,
            chart_drawing=chart_drawing,
            report_data=report_data,
            date_format=DATE_FORMAT,
        ))
#-------------------------------------------------------------------------------

def render_template_from_string(string, context_vars):
    return Template(string).render(Context(context_vars))

#-------------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
@login_required
@user_access(['staff','r&d'])
def generic_heatmap_report_view(request, report_class_name):
    """
    View to visualize Heatmaps.
    """
    series_range, aggregation = get_common_vars_for_charts(request)
    report_class = genericreportclasses.find_report_class(report_class_name)()
    
    return render_response(
         "heatmap.html", {
         "lat_longs": report_class.get_data(series_range, aggregation),
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
    
    
