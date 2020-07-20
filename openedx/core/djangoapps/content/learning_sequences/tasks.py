"""
This module is here as a placeholder, but knowledge of the modulestore should
eventually be moved out of the learning_sequence app entirely.

Also note that right now we're not hooked into the publish flow. This task code
is only invoked by the "update_course_outline" management command.
"""
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from django.conf import settings
from .api import replace_course_outline
from .api.data import (
    CourseOutlineData,
    CourseSectionData,
    CourseLearningSequenceData,
    ExamData,
    VisibilityData
)

import logging
log = logging.getLogger(__name__)


def update_from_modulestore(course_key):
    """
    Update the CourseOutlineData for course_key with ModuleStore data (i.e. what
    was most recently published in Studio).

    We should move this out so that learning_sequences does not depend on
    ModuleStore.
    """
    def _make_section_data(section):
        sequences_data = []
        for sequence in section.get_children():
            sequences_data.append(
                CourseLearningSequenceData(
                    usage_key=sequence.location,
                    title=sequence.display_name,
                    inaccessible_after_due=sequence.hide_after_due,
                    exam=ExamData(
                        is_practice=sequence.is_practice_exam,
                        is_proctored=sequence.is_proctored_enabled,
                        is_timed=sequence.is_timed_exam
                    ),
                    visibility=VisibilityData(
                        hide_from_toc=sequence.hide_from_toc,
                        visible_to_staff_only=sequence.visible_to_staff_only
                    ),
                )
            )

        section_data = CourseSectionData(
            usage_key=section.location,
            title=section.display_name,
            sequences=sequences_data,
            visibility=VisibilityData(
                hide_from_toc=section.hide_from_toc,
                visible_to_staff_only=section.visible_to_staff_only
            ),
        )
        return section_data

    store = modulestore()
    sections = []
    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key, depth=2)
        sections_data = []
        for section in course.get_children():
            section_data = _make_section_data(section)
            sections_data.append(section_data)

        course_outline_data = CourseOutlineData(
            course_key=course_key,
            title=course.display_name,
            published_at=course.subtree_edited_on,
            published_version=str(course.course_version),  # .course_version is a BSON obj
            entrance_exam_id=course.entrance_exam_id,
            sections=sections_data,
        )

    replace_course_outline(course_outline_data)
