import settings
#from django.conf.urls.defaults import *
from django.conf.urls import *

urlpatterns = patterns('')

if settings.IS_LOGGING_SERVER:
    urlpatterns += patterns('houdini_stats.api',
        # API for non-browser-based interaction.
        url(r'^api$', 'api_view', name='api'),
    )

if settings.IS_QUERY_SERVER:
    urlpatterns += patterns('houdini_stats.views',
        # Home page.
        url(r'^$', 'index_view', name='index'),
        url(r'^index$', 'index_view', name='index2'),

        # Log in.
        url(r'^login$', 'login_view', name='login'),
        # Log out.
        url(r'^logout/$', 'logout_view', name='logout'),
        
        url(r'^houdini/(?P<dropdown_option_key>.*)$', 'hou_reports_view', 
                                                            name='hou_reports'),
        url(r'^licenses/(?P<dropdown_option_key>.*)$', 'hou_licenses_view', 
                                                           name='hou_licenses'),
        url(r'^surveys/(?P<dropdown_option_key>.*)$', 'hou_surveys_view', 
                                                            name='hou_surveys'),
        url(r'^forum/(?P<dropdown_option_key>.*)$', 'hou_forum_view', 
                                                              name='hou_forum'),
        
    )
