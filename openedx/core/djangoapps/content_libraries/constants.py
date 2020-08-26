""" Constants used for the content libraries. """
from django.utils.translation import ugettext_lazy as _

# This API is only used in Studio, so we always work with this draft of any
# content library bundle:
DRAFT_NAME = 'studio_draft'

LEGACY = 'legacy'
VIDEO = 'video'
COMPLEX = 'complex'
PROBLEM = 'problem'

LIBRARY_TYPES = (
    (LEGACY, _('Legacy')),
    (VIDEO, _('Video')),
    (COMPLEX, _('Complex')),
    (PROBLEM, _('Problem')),
)
