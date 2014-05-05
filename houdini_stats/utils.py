from django.http import HttpResponse
from houdini_stats.models import *
from django.contrib.gis.geoip import GeoIP
from settings import REPORTS_START_DATE, HOUDINI_REPORTS_START_DATE, _this_dir
from dateutil.relativedelta import relativedelta

import json
import re
import datetime
import time
import hashlib

#===============================================================================

def text_http_response(content, status=200):
    """
    Translate a response into HTML text.
    """
    # FIXME (LM): Why doesn't Django set the Content-Length header?
    response = HttpResponse(content, status=status)
    response["Content-Length"] = str(len(response.content))
    return response

#-------------------------------------------------------------------------------

class StatsError(Exception):
    """
    Parent class for all stats exceptions.  Requires an HTTP status
    code, an error message template, and optionally some formatting
    arguments for that template.
    """
    def __init__(self, status_code, msg_template, **kwargs):
        Exception.__init__(self, msg_template % kwargs)
        self.status_code = status_code
        
#-------------------------------------------------------------------------------
class ServerError(StatsError):
    """
    Internal error.
    """
    def __init__(self, msg_template, **kwargs):
        StatsError.__init__(self, 500, msg_template, **kwargs)       

#-------------------------------------------------------------------------------
class UnauthorizedError(StatsError):
    """
    Access control (as opposed to permission).
    """
    def __init__(self, msg_template, **kwargs):
        StatsError.__init__(self, 401, msg_template, **kwargs)

#----------------------------------------------------------------------------

def json_http_response(content, status=200):
    """
    Translate a response JSON and return.
    """
    return text_http_response(json.dumps(content), status=status)

#-------------------------------------------------------------------------------

def parse_byte_size_string(string):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.

      >>> parse_byte_size_string('1 KB')
      1024
      >>> parse_byte_size_string('2.2 GB')
      2362232012
    """
    
    if not string:
        return
    # Find out the numerical part.
    initial_string = string
    num_string = ""
    while string and string[0:1].isdigit() or string[0:1] == '.':
        num_string += string[0]
        string = string[1:]

    num = float(num_string)

    # Look for the suffix.
    suffix = string.strip() or "B"
    suffix_set = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')

    prefix = {suffix_set[0]: 1}
    for i, string in enumerate(suffix_set[1:]):
        prefix[string] = 1 << (i+1)*10

    return int(num * prefix[suffix])

#-------------------------------------------------------------------------------

def str_to_datetime(str_date):
    """
    Converts a string into a datetime object
    """ 
    return datetime.strptime(str_date.strip(), "%a %b  %d %H:%M:%S %Y")

#-------------------------------------------------------------------------------
    
def date_range_to_seconds(datetime1, datetime2):
    """
    Computes the number of seconds between two datetime
    """
    return (datetime2 - datetime1).total_seconds() 

#-------------------------------------------------------------------------------

def seconds_to_multiple_time_units(secs):
    """
    This function receives a number of seconds and return how many min, hours,
    days those seconds represent.
    """
    return {
        "seconds": int(secs),
        "minutes": round(int(secs) / 60.0),
        "hours": round(int(secs) / (60.0 * 60.0)),
        "days": round(int(secs) / (60.0 * 60.0 * 24.0)),
    }

#-------------------------------------------------------------------------------

def get_percent(part, whole):
    """
    Get which percentage is a from b, and round it to 2 decimal numbers.
    """
    return round(100 * float(part)/float(whole)  if whole !=0 else 0.0, 2)

#-------------------------------------------------------------------------------

def get_lat_and_long(ip):
    """
    Get the values of the latitude and long by ip address
    """
    g = GeoIP(cache=GeoIP.GEOIP_MEMORY_CACHE)
    
    return  g.lat_lon(str(ip))#lat, long 

#-------------------------------------------------------------------------------
def is_valid_machine_config_hash(user_info):
    """
    Compute the hash of the data, ignoring the hash value stored in the data,
    and validate that the computed hash matches the one in the data.
    We want to make sure that the same user configs always create the
    same hash, so the data needs to be ordered.
    """
    string_to_hash = ''.join([
        key + ": " + user_info[key]
        for key in sorted(user_info.keys())
        if key != "config_hash"])
 
    print  "The hash passed to server: ", user_info["config_hash"]
    print  "The hash created by server: ", hashlib.md5(string_to_hash).hexdigest()
 
    return (user_info["config_hash"] ==
        hashlib.md5(string_to_hash).hexdigest()) 


#-------------------------------------------------------------------------------

def get_or_save_machine_config(user_info, ip_address, data_log_date):
    """
    Get or save if not already in db the machine config
        
    User Info:{ 'config_hash': '7ef9c42fe4d3748dc9aad755e02852d8',
                'houdini_build_version': '146',
                'houdini_major_version': '13',
                'houdini_minor_version': '0',
                'application_name': 'houdini',
                'operating_system': 'linux-x86_64-gcc4.7',
                'system_memory': '23.55 GB',                 
                'license_category': 'Commercial',
                'number_of_processors': '12',
                'graphics_card': 'Quadro 600/PCIe/SSE2',
                'graphics_card_version': '4.2.0 NVIDIA 304.88'
                'mac_address_hash'      : '05e8458a3e60776298ece4af002dcef7',
                ""
              }
    """
        
    # 1. Validate machine config
    config_hash = user_info['config_hash']
     
    #if not is_valid_machine_config_hash(user_info):
    #    print "Different"
        #raise ServerError("Invalid config hash %(name)s.",
        #                      name=config_hash)
   
    # 2. Get or save Machine by hardware_id
    hardware_id = user_info.get('mac_address_hash','')   
    
    try:
        machine = Machine.objects.get(hardware_id=hardware_id)
    
    except Machine.DoesNotExist:
        machine = Machine(hardware_id=hardware_id)
        machine.save()
    
    # 3. Get or save Machine Config 
    try:
        machine_config = MachineConfig.objects.get(machine = machine, 
                                                config_hash__exact=config_hash)
    except MachineConfig.DoesNotExist:
        
        sys_memory = user_info.get('system_memory', "0")
        product = user_info.get('application_name',"") + " " + user_info.get(
                                                         'license_category',"")
        
        # Create new machine config 
        machine_config = MachineConfig(config_hash = config_hash, 
             ip_address = ip_address,  
             machine = machine,                       
             creation_date = data_log_date,
             houdini_major_version = user_info.get('houdini_major_version',0),
             houdini_minor_version = user_info.get('houdini_minor_version',0),
             houdini_build_number = user_info.get('houdini_build_version',0),
             product = user_info.get('application_name',"").title(),
             is_apprentice = user_info.get('license_category',"") == 'Apprentice',
             graphics_card = user_info.get('graphics_card',''),
             graphics_card_version = user_info.get('graphics_card_version',''),
             operating_system = user_info.get('operating_system', ""),             
             system_memory = parse_byte_size_string(sys_memory),
             number_of_processors = user_info.get('number_of_processors',0),
             raw_user_info = str(user_info)
        )
        # Save the asset version status
        machine_config.save()
        
    return machine_config

#-------------------------------------------------------------------------------
def is_new_log_or_existing(machine_config, log_id, data_log_date):
    """
    Verify if a log already exists and if not save it.
    Returns true if the log is new, and false otherwise.
    """
    try:
        log = LogId.objects.get(machine_config=machine_config, 
                                log_id = log_id)
        return False
        
    except LogId.DoesNotExist:
        log = LogId(machine_config=machine_config, log_id = log_id, 
                                logging_date = data_log_date )
        log.save()
        return True

#-------------------------------------------------------------------------------
    
def save_uptime(machine_config, num_seconds, data_log_date):
    """
    Create Uptime record and save it in DB.
    """
    uptime = Uptime(machine_config = machine_config,
                    date = data_log_date,
                    number_of_seconds = num_seconds)                    
    uptime.save()        

#-------------------------------------------------------------------------------
    
def save_counts(machine_config, counts_dict, data_log_date):
    """
    Save the data that comes in "counts" 
    """
    
    # Prefix for the houdini tools
    tools_prefix = "tools/"
    
    for key, count in counts_dict.iteritems():
        if key.startswith(tools_prefix):
            save_tool_usage(machine_config, tools_prefix, key, count, 
                            data_log_date)
        else:
            save_key_usage(machine_config, key, count, 
                            data_log_date)    
            
#-------------------------------------------------------------------------------

def save_tool_usage(machine_config, tools_prefix, key, count, data_log_date):
    """
    Create HoudiniToolUsage object and save it in DB.
    
    Schema: tools|location|tool_name
    - location can be "shelf", "viewer/Object", "viewer/Sop", 
      "network/Object", "network/Sop", etc.
    - tool_name can be "sop_box", or "SideFX::spaceship" or 
      blank if it's a custom tool
    - the tool name can be followed by "(orbolt)" (if it's an orbolt tool) or 
      "(custom_tool)" if it's a nameless custom tool.
    """
    
    is_asset = False
    is_custom = False
    
    for mode, name in HoudiniToolUsage.TOOL_CREATION_MODES:
        prefix = tools_prefix + name
        if key.startswith(prefix):
            # Find "|" to get tool creation mode
            pipe_pos = key.index("|")
            tool_creation_location = key[len(prefix)+1: pipe_pos]
            tool_name = key[pipe_pos +1:]
                
            # Verify if tool type is a custom_tool
            if "(custom_tool)" in tool_name:
                tool_name = re.sub('[\(\)]', "", tool_name)
                is_custom = True
            # Verify if tool type is an Orbolt asset
            elif "(orbolt)" in tool_name:
                tool_name = tool_name.replace("(orbolt)","")
                is_asset = True
                                
            tools_usage = HoudiniToolUsage(machine_config = machine_config,
                          date = data_log_date, tool_name = tool_name,
                          tool_creation_location = tool_creation_location,
                          tool_creation_mode= mode, count = count,
                          is_builtin = (not is_asset and not is_custom), 
                          is_asset = is_asset)
            tools_usage.save()
            break          

#------------------------------------------------------------------------------- 

def save_key_usage(machine_config, key, count, data_log_date):
    """
    Create HoudiniUsageCount object and save it in DB.
    """
     
    key_usage = HoudiniUsageCount(machine_config = machine_config,
                                 date = data_log_date, key = key, count = count)
    key_usage.save()
        
#------------------------------------------------------------------------------- 
      
def save_crash(machine_config, crash_log, data_log_date):
    """
    Create a HoudiniCrash object and save it in DB..
    
    crash_log: { 
                 u'traceback': u'Caught signal 11\\n\\nAP_Interface::
                              createCrashLog(UTsignalHandlerArg....' 
    }
    """
    crash = HoudiniCrash(
        machine_config=machine_config,
        date=data_log_date,
        stack_trace=crash_log['traceback'],
        type="crash",
    )
    crash.save()

#-------------------------------------------------------------------------------
def save_data_log_to_file(date, config_hash, json_data):
    """
    Save the received data log to a text file
    """
    
    with open(_this_dir + "/houdini_logs.txt", "a") as log_file:
        log_file.write("""\n Date: {0}, Config Hash: {1} \n {2}
            """.format(date, config_hash, str(json_data)))
        
#-------------------------------------------------------------------------------   

def get_ip_address(request):
    """
    Get the ip address from the machine doing the request.
    """
    return request.META.get("REMOTE_ADDR", "0.0.0.0")
 
#-------------------------------------------------------------------------------
def _validate_date_format(date):
        
    try:
        datetime.strptime(date, '%d/%m/%Y')
        return True
    except:
        raise ServerError("Invalid date format.")
        
#-------------------------------------------------------------------------------
def series_range(start_request, end_request):
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
def _reset_time_for_date(date):
    """
    Set time on a datetime to 00:00:00
    """
    return date.replace(hour=0, minute=0, second=0, microsecond=0 )      
    
#-------------------------------------------------------------------------------
def _get_yesterdays_date():
    """
    Get yesterday's date    
    """  
    return datetime.datetime.now() - datetime.timedelta(hours=24)  

#-------------------------------------------------------------------------------
def _get_months_ago_date(months = 3):
    """
    Get n-months ago date. Starting from yesterday's date. 
    """
    return _reset_time_for_date(_get_yesterdays_date() + relativedelta(
                                                             months = -months))  
    
#-------------------------------------------------------------------------------
def _get_start_request(request, aggregation, for_hou_rep = False):
    """
    Get start date from the request.
    """
    start_request = request.GET.get("start", None)
    
    if start_request is not None:
        t = time.strptime(start_request, "%d/%m/%Y")
        start = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    elif for_hou_rep:
        # Date when we started collecting good data for houdini reports
        start = HOUDINI_REPORTS_START_DATE
    else:
        # The start date will be three months from yesterday's date
        start = _get_months_ago_date()
        
    
    return _adjust_start_date(start, aggregation)
    
#------------------------------------------------------------------------------- 
def _adjust_start_date(start_date, aggregation):
    """
    Adjust the start date depending on the aggregation
    """            
    
    if aggregation == "weekly":
        # Return the Monday of the starting date week    
        return start_date - datetime.timedelta(days = start_date.weekday())
    if aggregation == "monthly":
       # Return the fist day of the starting date's month   
       return datetime.datetime(start_date.year, start_date.month, 1) 
    
    if aggregation == "yearly":
       # Return the first day of the first month of the current year    
       return datetime.datetime(start_date.year, 1, 1)      
    
    # Daily aggregation        
    return start_date
        
#------------------------------------------------------------------------------- 
def _get_end_request(request):
    """
    Get end date from the request.
    """
    end_request = request.GET.get("end", None)
    
    if end_request is not None:
        t = time.strptime(end_request, "%d/%m/%Y")
        end = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
    else:
        # We get yesterday's date    
        end = _reset_time_for_date(_get_yesterdays_date())

    return end

#------------------------------------------------------------------------------- 
def _get_aggregation(get_vars):
    """
    Get aggregation from the request.GET.
    If there is not aggregation we set it to daily by default.
    """
    # For aggregation 
    valid_agg = ["monthly", "weekly", "yearly", "daily"]
    if "ag" not in get_vars:
        return "daily"
    
    aggregation = get_vars["ag"].lower()
    
    if aggregation not in valid_agg and aggregation !="inherit":
        raise NotFoundError("Not valid aggregation")
    elif aggregation=="inherit":
        return "daily"  
    
    return aggregation 

#-------------------------------------------------------------------------------
def get_common_vars_for_charts(request, for_hou_rep=False):
    """
    Get all variables that will be used for the reports.
    """
    
    aggregation = _get_aggregation(request.GET)
    
    return [_get_start_request(request, aggregation, for_hou_rep), \
            _get_end_request(request)], aggregation

#-------------------------------------------------------------------------------
def get_list_of_tuples_from_list(list):
    """
    Get a list of tuples from a list.
    
    For example given:    
    
    [1,2,3,4,5,6]
    
    Return [(1,2),(3,4)(5,6)]
    
    """
    output = []
    item = []
    
    for i in list:
        item.append(i)
        if len(item) == 2:
            output.append(item)
            item = []
    if item:
        output.append(item) 
    
    return output