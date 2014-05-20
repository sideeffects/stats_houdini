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
        url(r'^houdini/(?P<dropdown_option_key>downloads)$',
            'hou_reports_view'),
        #url(r'^houdini/(?P<dropdown_option_key>crashes)$',
        #    'hou_reports_view'),
        url(r'^houdini/(?P<dropdown_option_key>tools_usage)$',
            'hou_reports_view'),
        url(r'^houdini/(?P<dropdown_option_key>versions_and_builds)$',
            'hou_reports_view'),
        url(r'^apprentice/(?P<dropdown_option_key>apprentice_activations)$',
            'hou_apprentice_view'),
        url(r'^apprentice/(?P<dropdown_option_key>apprentice_view)$',
            'hou_apprentice_view'),
        url(r'^apprentice/(?P<dropdown_option_key>apprentice_heatmap)$',
            'hou_apprentice_view'),
        url(r'^surveys/(?P<dropdown_option_key>sidefx_labs)$',
            'hou_surveys_view'),
        url(r'^surveys/(?P<dropdown_option_key>apprentice_followup)$',
            'hou_surveys_view'),
        url(r'^forum/(?P<dropdown_option_key>login_registration)$',
            'hou_forum_view'),

        # This is the generic view for new-style reports.
        url(r'^(?P<menu_name>.*)/(?P<dropdown_option>.*)$',
            'generic_report_view', name='generic_report'),

        # Custom views:
        url(r'^heatmap/(?P<option>.*)$',
            'hou_heatmap_view', name='heatmap'),

        # Remove this once all of the above "houdini/" URLs are removed.
        url(r'^houdini/(?P<dropdown_option_key>.*)$',
            'hou_reports_view', name='hou_reports'),
        # Remove this once all of the above "apprentice/" URLs are removed.
        url(r'^apprentice/(?P<dropdown_option_key>.*)$',
            'hou_apprentice_view', name='hou_apprentice'),                    
        # Remove this once all of the above "surveys/" URLs are removed.
        url(r'^surveys/(?P<dropdown_option_key>.*)$',
            'hou_surveys_view', name='hou_surveys'),
        # Remove this once all of the above "forum/" URLs are removed.
        url(r'^forum/(?P<dropdown_option_key>.*)$',
            'hou_forum_view', name='hou_forum'),
    )

