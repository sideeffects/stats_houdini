
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from houdini_stats.models import *
from stats_main.models import *

#-------------------------------------------------------------------------------

def admin_site_register(managed_class):
    """
    Decorator for simplifying registration.
    """
    def func(admin_class):
        admin.site.register(managed_class, admin_class)
    return func

##==============================================================================

class HoudiniMachineConfigInline(admin.StackedInline):
     """
     Houdini Machine Config extension.
     """
     model = HoudiniMachineConfig
      
class HoudiniMachineConfigAdmin(admin.ModelAdmin):
    inlines = [HoudiniMachineConfigInline]
 
admin.site.unregister(MachineConfig)     
admin.site.register(MachineConfig, HoudiniMachineConfigAdmin)

#-------------------------------------------------------------------------------

@admin_site_register(HoudiniCrash)
class HoudiniCrashAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays Houdini crashes.
    """
    list_filter = ("stats_machine_config", "date")
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
    list_filter = ("stats_machine_config", "date", "tool_name", "tool_creation_location",
                   "tool_creation_mode", "is_builtin", "is_asset", "count")
    
    list_display = list_filter    
    list_display_links = list_filter
    list_per_page = 20
    ordering = ["-date"]

#-------------------------------------------------------------------------------

@admin_site_register(HoudiniUsageCount)
class HoudiniUsageCountAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays usage counts.
    """
    list_filter = ("key", "stats_machine_config", "date", "count")
    list_display = list_filter 
    list_display_links =list_filter
    
    list_per_page = 20
    ordering = ["-date"]

#-------------------------------------------------------------------------------
@admin_site_register(Uptime)
class UptimeAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays uptimes for Houdini usage.
    """
    list_filter = ("stats_machine_config", "number_of_seconds", "date")
    
    list_display = list_filter 
    
    list_display_links = list_filter
    list_per_page = 20
    ordering = ["-date"]
