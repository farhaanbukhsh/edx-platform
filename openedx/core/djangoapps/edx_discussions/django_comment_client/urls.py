"""
Urls for the django_comment_client.
"""


from django.conf.urls import include, url
from .base import urls as base_urls

urlpatterns = [
    url(r'', include(base_urls)),
]
