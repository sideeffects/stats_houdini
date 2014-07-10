import settings
try:
    from django.conf.urls import patterns, include, url
except ImportError:
    from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('')
# 
# if settings.IS_LOGGING_SERVER:
#     urlpatterns += patterns('houdini_stats.api',
#         # API for non-browser-based interaction.
#         url(r'^api$', 'api_view', name='api'),
#     )


