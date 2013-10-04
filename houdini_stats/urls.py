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
        
        url(r'^index/uptime$', 'hou_uptime_view', name='hou_uptime'),
        url(r'^index/crashes$', 'hou_crashes_view', name='hou_crashes'),
        url(r'^index/nodes_usage$', 'hou_nodes_usage_view', name='hou_nodes_usage'),
        url(r'^index/versions_and_builds$', 'hou_versions_and_builds_view', name='hou_versions_and_builds'),
        url(r'^index/licenses$', 'hou_licenses_view', name='hou_licenses'),
        url(r'^index/surveys/(?P<survey_name>.*)$', 'hou_surveys_view', name='hou_surveys'),
        url(r'^index/forum$', 'hou_forum_view', name='hou_forum'),
    )
