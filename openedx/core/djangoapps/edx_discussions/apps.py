"""
Discussion Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig

from openedx.core.constants import COURSE_ID_PATTERN
from openedx.core.djangoapps.plugins.constants import PluginSettings, PluginURLs, ProjectType, SettingsType


class DiscussionConfig(AppConfig):
    """
    Application Configuration for Discussion.
    """

    name = u'openedx.core.djangoapps.edx_discussions'
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: '',
                PluginURLs.RELATIVE_PATH: u'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.CMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
            },
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
            },
        }
    }

    def ready(self):
        """
        Connect handlers to send notifications about discussions.
        """
        from .signals import handlers  # pylint: disable=unused-import
