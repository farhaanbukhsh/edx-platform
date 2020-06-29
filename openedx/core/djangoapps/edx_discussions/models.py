import logging

from django.conf import settings

from .comment_client import User


def create_comments_service_user(user):
    if not settings.FEATURES['ENABLE_DISCUSSION_SERVICE']:
        # Don't try--it won't work, and it will fill the logs with lots of errors
        return
    try:
        cc_user = User.from_django_user(user)
        cc_user.save()
    except Exception:  # pylint: disable=broad-except
        log = logging.getLogger("edx.discussion")  # pylint: disable=redefined-outer-name
        log.error(
            "Could not create comments service user with id {}".format(user.id),
            exc_info=True
        )
