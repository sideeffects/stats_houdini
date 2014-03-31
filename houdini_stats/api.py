
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from utils import *

import json
import datetime
import traceback
import settings

#-------------------------------------------------------------------------------

class API(object):
    """
    Handle web API requests.
    """

    # API methods can be flagged as either requiring a login or not.  All other
    # methods, including those provided by the object class, will not be
    # visible in the API.
    def login_required(method):
        method._login_required = True
        return method

    def login_not_required(method):
        method._login_required = False
        return method

    def dispatch(self, request):
        """
        Dispatch requests for '/api' URLds by:
           1. Unpacking the handler and post data from the JSON in the request.
           2. Looking up the handler method.
           3. Dispatching to it.
           4. Wrapping its response as JSON.
        The handler method must take the user name as its first argument, as
        well as optional extra arguments.  It normally returns a valid
        HttpResponse or raises an StoreError exception when it wants to give the
        user helpful error messages.  However, buggy or malicious callers can
        make a handler raise other exceptions, in which case the production
        server will return a non-descriptive error message.
        """
        try:
            return self._dispatch_without_catching_api_errors(request)
        except ApiError as e:
            return text_http_response(
                (traceback.format_exc() if settings.DEBUG else str(e)))#,
                #status=e.status_code)

    def _dispatch_without_catching_api_errors(self, request):
        """
        As the name suggests, this help method dispatches without
        looking for or handling errors.
        """
        try:
            # request.POST is a magic variable that loads the data on demand
            # when you access it.
            json_data = request.POST.get("json")
        except IOError as e:
            # For whatever reason, django's engine could not read the post
            # data.  Don't bother to generate an error trigger an email to
            # be sent to the site administrators.
            return text_http_response(
                "Error reading POST data:\n" + traceback.format_exc(), 500)

        if "json" not in request.POST:
            return text_http_response(
                "'json' not given in the POST data", 500)
            
        
        handler_name, args, kwargs = json.loads(json_data)
        
        handler = getattr(self, handler_name, None)
        
        if handler is None:
            raise ServerError("Invalid API handler name %(name)s.",
                              name=handler_name)
            
        return handler(request, *args, **kwargs)

    @login_not_required
    def send_stats(self, request, user_info, stats):
        """
        Save user stats
        """
        
        # Get json content. Contains start_time and end_time and counts for the 
        # Houdini tools usage
        json_data = json.loads(stats['json_content'])
        
        # Get total seconds
        data_log_date =  datetime.datetime.fromtimestamp(json_data["start_time"])
        
        total_sec = json_data["end_time"] - json_data["start_time"]
        
        # Get or save machine config
        machine_config = get_or_save_machine_config(user_info,
            get_ip_address(request), data_log_date)
        
        is_new_log = True
        if "log_id" in json_data.keys():
            # Save log id if it hasnt been saved in the db yet
            is_new_log = is_new_log_or_existing(machine_config, 
                                    json_data["log_id"], data_log_date)
        
        # Just save the stats data if  the log id was new
        if is_new_log:
            # Save uptime
            save_uptime(machine_config, total_sec, data_log_date)
            # Save counts 
            save_counts(machine_config, json_data["counts"], data_log_date)
        
            # Save
            save_data_log_to_file(data_log_date, user_info['config_hash'],
                                  json_data)
            # TODO(YB): Implement save flags and save logs  
        
        return json_http_response(True)

    @login_not_required
    def send_crash(self, request, user_info, crashlog):
        """
        Save houdini crashes
        """
        # Get or save machine config
        machine_config = get_or_save_machine_config(user_info,
                                                    get_ip_address(request),
                                                    datetime.datetime.now())
        # Save the crash
        save_crash(machine_config, crashlog, datetime.datetime.now())
        
        return json_http_response(True)

    @login_not_required
    def send_license_failure(self, request, user_info, failure_info):
        print "user info (fail): ", user_info
        print "failure info: ", failure_info
        return json_http_response(True) 
                
#-------------------------------------------------------------------------------

@require_http_methods(["POST"])
@csrf_exempt
def api_view(request):
    """
    Dispatch requests for API URLs.
    """
    return API().dispatch(request)

