import settings
try:
    from django.conf.urls import patterns, include, url
except ImportError:
    from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('')

if settings.IS_LOGGING_SERVER:
    urlpatterns += patterns('houdini_stats.api',
        # API for non-browser-based interaction.
        url(r'^api$', 'api_view', name='api'),
    )

if settings.IS_QUERY_SERVER:
    urlpatterns += patterns('houdini_stats.views',
        url(r'^$', 'index_view', name='index'),
        url(r'^index$', 'index_view', name='index2'),
        url(r'^login$', 'login_view', name='login'),
        url(r'^logout/$', 'logout_view', name='logout'),

        # Remove these URLs as reports get switched over to the new style.
        url(r'^apprentice/(?P<dropdown_option_key>apprentice_heatmap)$',
            'hou_apprentice_view'),
       
        # Url for heatmaps
        url(r'^heatmap/(?P<option>.*)$',
            'hou_heatmap_view', name='heatmap'),
   
        # This is the generic view for new-style reports.
        url(r'^(?P<menu_name>.*)/(?P<dropdown_option>.*)$',
            'generic_report_view', name='generic_report'),

        # Custom views:
        # Remove this once all of the above "apprentice/" URLs are removed.
        url(r'^apprentice/(?P<dropdown_option_key>.*)$',
            'hou_apprentice_view', name='hou_apprentice'),                    

    )

