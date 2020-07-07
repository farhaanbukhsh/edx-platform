import six
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_with_access
from openedx.core.djangoapps.edx_discussions.django_comment_client import utils
from openedx.core.djangoapps.edx_discussions.django_comment_client.constants import TYPE_ENTRY
from openedx.core.djangoapps.edx_discussions.django_comment_client.utils import available_division_schemes
from openedx.core.djangoapps.django_comment_common.utils import (
    get_course_discussion_settings,
    set_course_discussion_settings,
)
from util.json_request import JsonResponse, expect_json


@require_http_methods(("GET", "PATCH"))
@ensure_csrf_cookie
@expect_json
@login_required
def course_discussions_settings_handler(request, course_key_string):
    """
    The restful handler for divided discussion setting requests. Requires JSON.
    This will raise 404 if user is not staff.
    GET
        Returns the JSON representation of divided discussion settings for the course.
    PATCH
        Updates the divided discussion settings for the course. Returns the JSON representation of updated settings.
    """
    course_key = CourseKey.from_string(course_key_string)
    course = get_course_with_access(request.user, 'staff', course_key)
    discussion_settings = get_course_discussion_settings(course_key)

    if request.method == 'PATCH':
        divided_course_wide_discussions, divided_inline_discussions = get_divided_discussions(
            course, discussion_settings
        )

        settings_to_change = {}

        if 'divided_course_wide_discussions' in request.json or 'divided_inline_discussions' in request.json:
            divided_course_wide_discussions = request.json.get(
                'divided_course_wide_discussions', divided_course_wide_discussions
            )
            divided_inline_discussions = request.json.get(
                'divided_inline_discussions', divided_inline_discussions
            )
            settings_to_change['divided_discussions'] = divided_course_wide_discussions + divided_inline_discussions

        if 'always_divide_inline_discussions' in request.json:
            settings_to_change['always_divide_inline_discussions'] = request.json.get(
                'always_divide_inline_discussions'
            )
        if 'division_scheme' in request.json:
            settings_to_change['division_scheme'] = request.json.get(
                'division_scheme'
            )

        if not settings_to_change:
            return JsonResponse({"error": six.text_type("Bad Request")}, 400)

        try:
            if settings_to_change:
                discussion_settings = set_course_discussion_settings(course_key, **settings_to_change)

        except ValueError as err:
            # Note: error message not translated because it is not exposed to the user (UI prevents this state).
            return JsonResponse({"error": six.text_type(err)}, 400)

    divided_course_wide_discussions, divided_inline_discussions = get_divided_discussions(
        course, discussion_settings
    )

    return JsonResponse({
        'id': discussion_settings.id,
        'divided_inline_discussions': divided_inline_discussions,
        'divided_course_wide_discussions': divided_course_wide_discussions,
        'always_divide_inline_discussions': discussion_settings.always_divide_inline_discussions,
        'division_scheme': discussion_settings.division_scheme,
        'available_division_schemes': available_division_schemes(course_key)
    })


@expect_json
@login_required
def discussion_topics(request, course_key_string):
    """
    The handler for divided discussion categories requests.
    This will raise 404 if user is not staff.

    Returns the JSON representation of discussion topics w.r.t categories for the course.

    Example:
        >>> example = {
        >>>               "course_wide_discussions": {
        >>>                   "entries": {
        >>>                       "General": {
        >>>                           "sort_key": "General",
        >>>                           "is_divided": True,
        >>>                           "id": "i4x-edx-eiorguegnru-course-foobarbaz"
        >>>                       }
        >>>                   }
        >>>                   "children": ["General", "entry"]
        >>>               },
        >>>               "inline_discussions" : {
        >>>                   "subcategories": {
        >>>                       "Getting Started": {
        >>>                           "subcategories": {},
        >>>                           "children": [
        >>>                               ["Working with Videos", "entry"],
        >>>                               ["Videos on edX", "entry"]
        >>>                           ],
        >>>                           "entries": {
        >>>                               "Working with Videos": {
        >>>                                   "sort_key": None,
        >>>                                   "is_divided": False,
        >>>                                   "id": "d9f970a42067413cbb633f81cfb12604"
        >>>                               },
        >>>                               "Videos on edX": {
        >>>                                   "sort_key": None,
        >>>                                   "is_divided": False,
        >>>                                   "id": "98d8feb5971041a085512ae22b398613"
        >>>                               }
        >>>                           }
        >>>                       },
        >>>                       "children": ["Getting Started", "subcategory"]
        >>>                   },
        >>>               }
        >>>          }
    """
    course_key = CourseKey.from_string(course_key_string)
    course = get_course_with_access(request.user, 'staff', course_key)

    discussion_topics = {}
    discussion_category_map = utils.get_discussion_category_map(
        course, request.user, divided_only_if_explicit=True, exclude_unstarted=False
    )

    # We extract the data for the course wide discussions from the category map.
    course_wide_entries = discussion_category_map.pop('entries')

    course_wide_children = []
    inline_children = []

    for name, c_type in discussion_category_map['children']:
        if name in course_wide_entries and c_type == TYPE_ENTRY:
            course_wide_children.append([name, c_type])
        else:
            inline_children.append([name, c_type])

    discussion_topics['course_wide_discussions'] = {
        'entries': course_wide_entries,
        'children': course_wide_children
    }

    discussion_category_map['children'] = inline_children
    discussion_topics['inline_discussions'] = discussion_category_map

    return JsonResponse(discussion_topics)


def get_divided_discussions(course, discussion_settings):
    """
    Returns the course-wide and inline divided discussion ids separately.
    """
    divided_course_wide_discussions = []
    divided_inline_discussions = []

    course_wide_discussions = [topic['id'] for __, topic in course.discussion_topics.items()]
    all_discussions = utils.get_discussion_categories_ids(course, None, include_all=True)

    for divided_discussion_id in discussion_settings.divided_discussions:
        if divided_discussion_id in course_wide_discussions:
            divided_course_wide_discussions.append(divided_discussion_id)
        elif divided_discussion_id in all_discussions:
            divided_inline_discussions.append(divided_discussion_id)

    return divided_course_wide_discussions, divided_inline_discussions
