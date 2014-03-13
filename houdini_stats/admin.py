
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from houdini_stats.models import *

#-------------------------------------------------------------------------------

def admin_site_register(managed_class):
    """
    Decorator for simplifying registration.
    """
    def func(admin_class):
        admin.site.register(managed_class, admin_class)
    return func

##==============================================================================

@admin_site_register(Machine)
class MachineAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays hardware ids.
    """
    list_filter = ("hardware_id",)
    list_display = list_filter 
    list_display_links =("hardware_id",)
    list_per_page = 20

#-------------------------------------------------------------------------------

@admin_site_register(MachineConfig)
class MachineConfigAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays machine configurations.
    """
    list_filter = ("config_hash", "machine", "creation_date", 
                   "houdini_major_version", "houdini_minor_version", 
                   "product", "is_apprentice", "operating_system", 
                   "graphics_card")
    list_display = list_filter 
    list_display_links =("config_hash", "machine", "creation_date", 
                         "product")
    list_per_page = 20
    ordering = ["-creation_date"]

#-------------------------------------------------------------------------------

@admin_site_register(HoudiniCrash)
class HoudiniCrashAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays Houdini crashes.
    """
    list_filter = ("machine_config", "date")
    list_display = list_filter 
    list_display_links = list_filter
    list_per_page = 20
    ordering = ["-date"]
                        
#-------------------------------------------------------------------------------

@admin_site_register(HoudiniToolUsage)
class HoudiniToolUsageAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays tool usages in Houdini.
    """
    list_filter = ("machine_config", "date", "tool_name", "tool_creation_location",
                   "tool_creation_mode", "is_builtin", "is_asset", "count")
    
    list_display = list_filter    
    list_display_links = list_filter
    list_per_page = 20
    ordering = ["-date"]

#-------------------------------------------------------------------------------

@admin_site_register(Uptime)
class UptimeAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays uptimes for Houdini usage.
    """
    list_filter = ("machine_config", "number_of_seconds", "date")
    
    list_display = list_filter 
    
    list_display_links = list_filter
    list_per_page = 20
    ordering = ["-date"]

  
#-------------------------------------------------------------------------------

@admin_site_register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays events.
    """
    list_filter = ("title", "date", "show")
    
    list_display = list_filter 
    
    list_display_links = list_filter
    list_per_page = 20
    ordering = ["-date"]    

