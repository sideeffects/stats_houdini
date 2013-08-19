from django.conf.urls.defaults import *

urlpatterns = patterns('houdini_stats.views',
    # Home page.
    url(r'^$', 'index_view', name='index'),
    url(r'^index$', 'index_view', name='index2'),
    
    url(r'^index/crashes$', 'hou_crashes_view', name='hou_crashes'),
    url(r'^index/nodes_usage$', 'hou_nodes_usage_view', name='hou_nodes_usage'),
    url(r'^index/versions_and_builds$', 'hou_versions_and_builds_view', name='hou_versions_and_builds'),
    
    # API for non-browser-based interaction.
    url(r'^api$', 'api_view', name='api'),
    
)