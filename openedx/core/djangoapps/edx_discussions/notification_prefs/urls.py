from django.conf import settings
from django.conf.urls import url

from . import views

urlpatterns = []

notification_prefs_urls = [
    url(r'^notification_prefs/enable/', views.ajax_enable),
    url(r'^notification_prefs/disable/', views.ajax_disable),
    url(r'^notification_prefs/status/', views.ajax_status),

    url(
        r'^notification_prefs/unsubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
        views.set_subscription,
        {'subscribe': False},
        name='unsubscribe_forum_update',
    ),
    url(
        r'^notification_prefs/resubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
        views.set_subscription,
        {'subscribe': True},
        name='resubscribe_forum_update',
    ),
]

if settings.FEATURES.get('ENABLE_FORUM_DAILY_DIGEST'):
    urlpatterns += notification_prefs_urls
