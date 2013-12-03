
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

##===============================================================================

@admin_site_register(MachineConfig)
class MachineConfigAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays machine configurations.
    """
    list_filter = ("config_hash", "last_active_date", "houdini_major_version", 
                   "houdini_minor_version", "houdini_build_number", "product",
                   "is_apprentice", "operating_system",)
    list_display = list_filter 
    list_display_links =("config_hash", "last_active_date", "product")
    list_per_page = 20
    ordering = ["last_active_date"]

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
    ordering = ["date"]
                        
#-------------------------------------------------------------------------------

@admin_site_register(NodeTypeUsage)
class NodeTypeUsageAdmin(admin.ModelAdmin):
    """
    Control how the admin site displays node types usages in Houdini.
    """
    list_filter = ("machine_config", "date", "node_type", "is_builtin",
                   "is_asset", "count")
    
    list_display = list_filter    
    list_display_links = list_filter
    list_per_page = 20
    ordering = ["date"]

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
    ordering = ["date"]

  
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
    ordering = ["date"]    
    
