import logging

import six
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from util import milestones_helpers

from .base import OutlineProcessor

User = get_user_model()
log = logging.getLogger(__name__)


class MilestonesOutlineProcessor(OutlineProcessor):
    """
    Responsible for applying all milestones outline processing.
    """
    def inaccessible_sequences(self, full_course_outline):
        """
        Returns the set of sequence usage keys for which the
        user has pending milestones
        """
        inaccessible = set()
        for section in full_course_outline.sections:
            inaccessible |= {
                seq.usage_key
                for seq in section.sequences
                if self.has_pending_milestones(seq.usage_key)
            }

        return inaccessible

    def has_pending_milestones(self, usage_key):
        return bool(milestones_helpers.get_course_content_milestones(
            six.text_type(self.course_key),
            six.text_type(usage_key),
            'requires',
            self.user.id
        ))
