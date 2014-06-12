from django.http import HttpResponse
from houdini_stats.models import *
from django.contrib.gis.geoip import GeoIP
from settings import REPORTS_START_DATE, _this_dir
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
    # FIXME: Why doesn't Django set the Content-Length header?
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
                'cpu_info': 
                'system_resolution:
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
             cpu_info =  user_info.get('cpu_info', ""), 
             system_resolution =  user_info.get('system_resolution', ""), 
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
    
def save_uptime(machine_config, num_seconds, idle_time, data_log_date):
    """
    Create Uptime record and save it in DB.
    """
    uptime = Uptime(machine_config = machine_config,
                    date = data_log_date,
                    number_of_seconds = num_seconds,
                    idle_time = idle_time)                    
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

