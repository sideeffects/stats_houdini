import json
from django.http import HttpResponse
from houdini_stats.models import *
from datetime import datetime, timedelta
from django.contrib.gis.geoip import GeoIP

#-------------------------------------------------------------------------------

def text_http_response(content, status=200):
    """
    Translate a response into HTML text.
    """
    # FIXME (LM): Why doesn't Django set the Content-Length header?
    response = HttpResponse(content, status=status)
    response["Content-Length"] = str(len(response.content))
    return response

#-------------------------------------------------------------------------------

class ApiError(Exception):
    """
    Parent class for all api exceptions.  Requires an HTTP status
    code, an error message template, and optionally some formatting
    arguments for that template.
    """
    def __init__(self, status_code, msg_template, **kwargs):
        Exception.__init__(self, msg_template % kwargs)
        self.status_code = status_code
        
#-------------------------------------------------------------------------------

class ServerError(ApiError):
    """
    Internal error.
    """
    def __init__(self, msg_template, **kwargs):
        ApiError.__init__(self, 500, msg_template, **kwargs)       

#---------------------------from datetime import datetime, timedelta-------------------------------------------------

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

def get_time(secs):
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

def get_or_save_machine_config(user_info, ip_address):
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
    # Get config_hash
    config_hash = user_info['config_hash']
    
    try:
        machine_config = MachineConfig.objects.get(
                                                config_hash__exact=config_hash)
    except MachineConfig.DoesNotExist:
        
        sys_memory = user_info.get('system_memory', "0")
        product = user_info.get('application_name',"") + " " + user_info.get('license_category',"")
        
        # Create new machine config 
        machine_config = MachineConfig(config_hash = config_hash, 
             ip_address = ip_address,  
             hardware_id = user_info.get('mac_address_hash',''),                       
             last_active_date = datetime.now(),
             houdini_major_version = user_info.get('houdini_major_version',0),
             houdini_minor_version = user_info.get('houdini_minor_version',0),
             houdini_build_number = user_info.get('houdini_build_number',0),
             product = user_info.get('application_name',"").title(),
             is_apprentice = user_info.get('license_category',"") == 'Apprentice',
             graphics_card = user_info.get('graphics_card',''),
             graphics_card_version = user_info.get('graphics_card_version',''),
             operating_system = user_info.get('operating_system', ""),             
             system_memory = parse_byte_size_string(sys_memory),
             number_of_processors = user_info.get('number_of_processors',0),
        )
        # Save the asset version status
        machine_config.save()
        
    return machine_config

#-------------------------------------------------------------------------------
    
def save_uptime(machine_config, num_seconds):
    """
    Create Uptime record and save it in DB.
    """
    uptime = Uptime(machine_config = machine_config,
                    date = datetime.now(),
                    number_of_seconds = num_seconds)                    
    uptime.save()        
    
#-------------------------------------------------------------------------------
    
def save_nodetypes(machine_config, counts_dict):
    """
    Create NodeTypeUsage object and save it in DB.
    """
    for key, count in counts_dict.iteritems():
        for mode, name in NodeTypeUsage.NODE_CREATION_MODES:
            prefix = "tools/"+ name + '/'
            if key.startswith(prefix):
                node_type_usage = NodeTypeUsage(machine_config = machine_config,
                                                date = datetime.now(),
                                                node_type = key[len(prefix):],
                                                node_creation_mode= mode,
                                                count = count
                                                #TODO: pass is_built_in (true by
                                                #default) and 
                                                #is asset
                                              )
                node_type_usage.save()
                break          

#-------------------------------------------------------------------------------    
      
def save_crash(machine_config, crash_log):
    """
    Create a HoudiniCrash object and save it in DB..
    
    crash_log: { 
                 u'log_data': u'Caught signal 11\\n\\nAP_Interface::
                              createCrashLog(UTsignalHandlerArg....' 
                 u'log_type': u'crash',
                 u'logged_date_and_time': u'2013-08-20 16:25:43'
    }
    """
    crash = HoudiniCrash(machine_config = machine_config,
                  date = crash_log.get('logged_date_and_time',
                                       datetime.now()),
                  stack_trace = crash_log.get('log_data',""),
                  type = crash_log.get('log_type',"")
                  )                    
    crash.save()     
    
#-------------------------------------------------------------------------------   

def get_ip_address(request):
    """
    Get the ip address from the machine doing the request.
    """
    return request.META.get("REMOTE_ADDR", "0.0.0.0")
    