# TODO Have the discussions code subscribe to the REGISTER_USER signal instead.
from django.conf import settings
from django.dispatch import receiver

from .views import enable_notifications
from openedx.core.djangoapps.user_authn.views.register import REGISTER_USER


@receiver(REGISTER_USER)
def email_marketing_register_user(sender, user, registration,
                                  **kwargs):  # pylint: disable=unused-argument

    if settings.FEATURES.get('ENABLE_DISCUSSION_EMAIL_DIGEST'):
        try:
            enable_notifications(user)
        except Exception:  # pylint: disable=broad-except
            log.exception(u"Enable discussion notifications failed for user {id}.".format(id=user.id))
