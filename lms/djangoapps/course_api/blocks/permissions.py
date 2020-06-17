"""
Encapsulates permissions checks for Course Blocks API
"""
from courseware.access_utils import ACCESS_DENIED, is_course_public
from courseware.courses import get_course
from lms.djangoapps.courseware.access import has_access
from student.models import CourseEnrollment
from student.roles import CourseStaffRole


def can_access_all_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access all the blocks
    in the course.
    """
    return has_access(requesting_user, CourseStaffRole.ROLE, course_key)


def can_access_others_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access the blocks for
    other users in the given course.
    """
    return has_access(requesting_user, CourseStaffRole.ROLE, course_key)


def can_access_self_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access own blocks.
    """
    user_is_enrolled_or_staff = (  # pylint: disable=consider-using-ternary
        (requesting_user.id and CourseEnrollment.is_enrolled(requesting_user, course_key)) or
        has_access(requesting_user, CourseStaffRole.ROLE, course_key)
    )
    if user_is_enrolled_or_staff:
        return user_is_enrolled_or_staff
    else:
        try:
            return is_course_public(get_course(course_key, depth=0))
        except ValueError:
            return ACCESS_DENIED
