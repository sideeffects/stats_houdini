
import json
import datetime
from django.http import HttpResponse
from houdini_stats.models import *

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
    suffix = string.strip()
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
    return datetime.datetime.strptime(str_date.strip(), "%a %b  %d %H:%M:%S %Y")

#-------------------------------------------------------------------------------
    
def date_range_to_seconds(datetime1, datetime2):
    """
    Computes the number of seconds between two datetime
    """
    return (datetime2 - datetime1).total_seconds() 

#-------------------------------------------------------------------------------

def get_or_save_machine_config(user_info):
    """
    Get or save if not already in db the machine config
        
    User Info:{ u'operating_system': u'linux-x86_64-gcc4.4', 
                u'system_memory': u'31.44 GB', 
                u'osname': u'Linux', 
                u'houdini_build_version': u'129', 
                u'houdini_major_version': u'13',
                u'number_of_processors': u'12', 
                u'houdini_minor_version': u'0', 
                u'config_hash': u'571b5d3e7addd7746d0efbd15833384f'
              }
    """
    # Get config_hash
    config_hash = user_info['config_hash']
    
    try:
        machine_config = MachineConfig.objects.get(
                                                config_hash__exact=config_hash)
    except MachineConfig.DoesNotExist:
        
        houd_major_ver = user_info['houdini_major_version'] if 'houdini_major_version' in user_info else 0 
        houd_minor_ver = user_info['houdini_minor_version'] if 'houdini_minor_version' in user_info else 0 
        houd_build_num = user_info['houdini_build_number'] if 'houdini_build_number' in user_info else 0
        operating_system = user_info['osname'] if 'osname' in user_info else ""
        
        sys_memory = parse_byte_size_string(user_info['system_memory']) if 'system_memory' in user_info else 0
        
        # Create new machine config 
        machine_config = MachineConfig(config_hash = config_hash, 
             last_active_date = datetime.datetime.now(),
             system_memory = sys_memory,
             operating_system = operating_system,
             houdini_major_version = houd_major_ver,
             houdini_minor_version = houd_minor_ver,
             houdini_build_number = houd_build_num
        )
        # Save the asset version status
        machine_config.save()
        
    return machine_config

#-------------------------------------------------------------------------------
    
def save_uptime(machine_config, num_seconds):
    """
    Create Uptime record and save it
    """
    uptime = Uptime(machine_config = machine_config,
                    date = datetime.datetime.now(),
                    number_of_seconds = num_seconds)                    
    uptime.save()        
    
#-------------------------------------------------------------------------------
    
def save_nodetypes(machine_config, counts_dict):
    """
    Create NodeTypeUsage record and save it
    """
    for key, count in counts_dict.iteritems():
        for mode, name in NodeTypeUsage.NODE_CREATION_MODES:
            prefix = "tools/"+ name + '/'
            if key.startswith(prefix):
                node_type_usage = NodeTypeUsage(machine_config = machine_config,
                                                date = datetime.datetime.now(),
                                                node_type = key[len(prefix):],
                                                node_creation_mode= mode,
                                                count = count
                                                #TODO: pass is_built_in (true by
                                                #default) and 
                                                #is asset
                                              )
                node_type_usage.save()
                break          
    
      
        

