"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""


from django.conf import settings
from django.utils.translation import ugettext_noop

from lms.djangoapps.discussion.django_comment_client import utils
from lms.djangoapps.courseware.tabs import EnrolledTab
from openedx.core.djangoapps.edx_discussions.config.waffle import use_bootstrap_flag_enabled
from xmodule.tabs import TabFragmentViewMixin


class DiscussionTab(TabFragmentViewMixin, EnrolledTab):
    """
    A tab for the cs_comments_service forums.
    """

    type = 'discussion'
    title = ugettext_noop('Discussion')
    priority = None
    view_name = 'forum_form_discussion'
    fragment_view_name = 'openedx.core.djangoapps.edx_discussions.views.DiscussionBoardFragmentView'
    is_hideable = settings.FEATURES.get('ALLOW_HIDING_DISCUSSION_TAB', False)
    is_default = False
    body_class = 'discussion'
    online_help_token = 'discussions'

    @classmethod
    def is_enabled(cls, course, user=None):
        if not super(DiscussionTab, cls).is_enabled(course, user):
            return False
        return utils.is_discussion_enabled(course.id)

    @property
    def uses_bootstrap(self):
        """
        Returns true if this tab is rendered with Bootstrap.
        """
        return use_bootstrap_flag_enabled()
