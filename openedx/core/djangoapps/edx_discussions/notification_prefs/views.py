"""
Views to support notification preferences.
"""


import json

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from six import text_type

from edxmako.shortcuts import render_to_response
from . import NOTIFICATION_PREF_KEY
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.preferences.api import delete_user_preference
from openedx.core.lib.user_utils import UsernameCipher, UsernameDecryptionException


def enable_notifications(user):
    """
    Enable notifications for a user.
    Currently only used for daily forum digests.
    """
    # Calling UserPreference directly because this method is called from a couple of places,
    # and it is not clear that user is always the user initiating the request.
    UserPreference.objects.get_or_create(
        user=user,
        key=NOTIFICATION_PREF_KEY,
        defaults={
            "value": UsernameCipher.encrypt(user.username)
        }
    )


@require_POST
def ajax_enable(request):
    """
    A view that enables notifications for the authenticated user

    This view should be invoked by an AJAX POST call. It returns status 204
    (no content) or an error. If notifications were already enabled for this
    user, this has no effect. Otherwise, a preference is created with the
    unsubscribe token (an encryption of the username) as the value.username
    """
    if not request.user.is_authenticated:
        raise PermissionDenied

    enable_notifications(request.user)

    return HttpResponse(status=204)


@require_POST
def ajax_disable(request):
    """
    A view that disables notifications for the authenticated user

    This view should be invoked by an AJAX POST call. It returns status 204
    (no content) or an error.
    """
    if not request.user.is_authenticated:
        raise PermissionDenied

    delete_user_preference(request.user, NOTIFICATION_PREF_KEY)

    return HttpResponse(status=204)


@require_GET
def ajax_status(request):
    """
    A view that retrieves notifications status for the authenticated user.

    This view should be invoked by an AJAX GET call. It returns status 200,
    with a JSON-formatted payload, or an error.
    """
    if not request.user.is_authenticated:
        raise PermissionDenied

    qs = UserPreference.objects.filter(
        user=request.user,
        key=NOTIFICATION_PREF_KEY
    )

    return HttpResponse(json.dumps({"status": len(qs)}), content_type="application/json")


@require_GET
def set_subscription(request, token, subscribe):
    """
    A view that disables or re-enables notifications for a user who may not be authenticated

    This view is meant to be the target of an unsubscribe link. The request
    must be a GET, and the `token` parameter must decrypt to a valid username.
    The subscribe flag feature controls whether the view subscribes or unsubscribes the user, with subscribe=True
    used to "undo" accidentally clicking on the unsubscribe link

    A 405 will be returned if the request method is not GET. A 404 will be
    returned if the token parameter does not decrypt to a valid username. On
    success, the response will contain a page indicating success.
    """
    try:
        username = UsernameCipher().decrypt(token.encode()).decode()
        user = User.objects.get(username=username)
    except UnicodeDecodeError:
        raise Http404("base64url")
    except UsernameDecryptionException as exn:
        raise Http404(text_type(exn))
    except User.DoesNotExist:
        raise Http404("username")

    # Calling UserPreference directly because the fact that the user is passed in the token implies
    # that it may not match request.user.
    if subscribe:
        UserPreference.objects.get_or_create(user=user,
                                             key=NOTIFICATION_PREF_KEY,
                                             defaults={
                                                 "value": UsernameCipher.encrypt(user.username)
                                             })
        return render_to_response("resubscribe.html", {'token': token})
    else:
        UserPreference.objects.filter(user=user, key=NOTIFICATION_PREF_KEY).delete()
        return render_to_response("unsubscribe.html", {'token': token})
