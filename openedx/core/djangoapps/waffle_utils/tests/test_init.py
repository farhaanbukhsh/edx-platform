"""
Tests for waffle utils features.
"""

import crum
import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edx_django_utils.cache import RequestCache
from mock import call, patch
from opaque_keys.edx.keys import CourseKey
from waffle.testutils import override_flag

from .. import (
    _get_waffle_flag_custom_metrics_set,
    CourseWaffleFlag,
    WaffleFlagNamespace,
    WaffleSwitchNamespace,
    WaffleSwitch,
)
from ..models import WaffleFlagCourseOverrideModel


@ddt.ddt
class TestCourseWaffleFlag(TestCase):
    """
    Tests the CourseWaffleFlag.
    """

    NAMESPACE_NAME = "test_namespace"
    FLAG_NAME = "test_flag"
    NAMESPACED_FLAG_NAME = NAMESPACE_NAME + "." + FLAG_NAME
    FLAG_2_NAME = "test_flag_2"
    NAMESPACED_FLAG_2_NAME = NAMESPACE_NAME + "." + FLAG_2_NAME

    TEST_COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    TEST_COURSE_2_KEY = CourseKey.from_string("edX/DemoX/Demo_Course_2")
    TEST_NAMESPACE = WaffleFlagNamespace(NAMESPACE_NAME)
    TEST_COURSE_FLAG = CourseWaffleFlag(TEST_NAMESPACE, FLAG_NAME)

    def setUp(self):
        super(TestCourseWaffleFlag, self).setUp()
        request = RequestFactory().request()
        self.addCleanup(crum.set_current_request, None)
        crum.set_current_request(request)
        RequestCache.clear_all_namespaces()

    @override_settings(WAFFLE_FLAG_CUSTOM_METRICS=[NAMESPACED_FLAG_NAME])
    @patch('openedx.core.djangoapps.waffle_utils.set_custom_metric')
    @ddt.data(
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.on, 'waffle_enabled': False, 'result': True},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.off, 'waffle_enabled': True, 'result': False},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.unset, 'waffle_enabled': True, 'result': True},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.unset, 'waffle_enabled': False, 'result': False},
    )
    def test_course_waffle_flag(self, data, mock_set_custom_metric):
        """
        Tests various combinations of a flag being set in waffle and overridden
        for a course.
        """
        with patch(
            'openedx.core.djangoapps.waffle_utils._WAFFLE_FLAG_CUSTOM_METRIC_SET',
            _get_waffle_flag_custom_metrics_set(),
        ):
            with patch.object(WaffleFlagCourseOverrideModel, 'override_value', return_value=data['course_override']):
                with override_flag(self.NAMESPACED_FLAG_NAME, active=data['waffle_enabled']):
                    # check twice to test that the result is properly cached
                    self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY), data['result'])
                    self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY), data['result'])
                    # result is cached, so override check should happen once
                    WaffleFlagCourseOverrideModel.override_value.assert_called_once_with(
                        self.NAMESPACED_FLAG_NAME,
                        self.TEST_COURSE_KEY
                    )

            self._assert_waffle_flag_metric(mock_set_custom_metric, expected_flag_value=str(data['result']))
            mock_set_custom_metric.reset_mock()

            # check flag for a second course
            if data['course_override'] == WaffleFlagCourseOverrideModel.ALL_CHOICES.unset:
                # When course override wasn't set for the first course, the second course will get the same
                # cached value from waffle.
                second_value = data['waffle_enabled']
                self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_2_KEY), second_value)
            else:
                # When course override was set for the first course, it should not apply to the second
                # course which should get the default value of False.
                second_value = False
                self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_2_KEY), second_value)

        expected_flag_value = None if second_value == data['result'] else 'Both'
        self._assert_waffle_flag_metric(mock_set_custom_metric, expected_flag_value=expected_flag_value)

    @override_settings(WAFFLE_FLAG_CUSTOM_METRICS=[NAMESPACED_FLAG_NAME])
    @patch('openedx.core.djangoapps.waffle_utils.set_custom_metric')
    @ddt.data(
        {'flag_undefined_default': None, 'result': False},
        {'flag_undefined_default': False, 'result': False},
        {'flag_undefined_default': True, 'result': True},
    )
    def test_undefined_waffle_flag(self, data, mock_set_custom_metric):
        """
        Test flag with various defaults provided for undefined waffle flags.
        """
        test_course_flag = CourseWaffleFlag(
            self.TEST_NAMESPACE,
            self.FLAG_NAME,
            flag_undefined_default=data['flag_undefined_default']
        )

        with patch(
            'openedx.core.djangoapps.waffle_utils._WAFFLE_FLAG_CUSTOM_METRIC_SET',
            _get_waffle_flag_custom_metrics_set(),
        ):
            with patch.object(
                WaffleFlagCourseOverrideModel,
                'override_value',
                return_value=WaffleFlagCourseOverrideModel.ALL_CHOICES.unset
            ):
                # check twice to test that the result is properly cached
                self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), data['result'])
                self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), data['result'])
                # result is cached, so override check should happen once
                WaffleFlagCourseOverrideModel.override_value.assert_called_once_with(
                    self.NAMESPACED_FLAG_NAME,
                    self.TEST_COURSE_KEY
                )

        self._assert_waffle_flag_metric(
            mock_set_custom_metric,
            expected_flag_value=str(data['result']),
            flag_undefined_default=data['flag_undefined_default'],
        )

    @ddt.data(
        {'flag_undefined_default': None, 'result': False},
        {'flag_undefined_default': False, 'result': False},
        {'flag_undefined_default': True, 'result': True},
    )
    def test_without_request(self, data):
        """
        Test the flag behavior when outside a request context.
        """
        crum.set_current_request(None)
        test_course_flag = CourseWaffleFlag(
            self.TEST_NAMESPACE,
            self.FLAG_NAME,
            flag_undefined_default=data['flag_undefined_default']
        )
        self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), data['result'])

    @ddt.data(
        {'expected_count': 0, 'waffle_flag_metric_setting': None},
        {'expected_count': 1, 'waffle_flag_metric_setting': [NAMESPACED_FLAG_NAME]},
        {'expected_count': 2, 'waffle_flag_metric_setting': [NAMESPACED_FLAG_NAME, NAMESPACED_FLAG_2_NAME]},
    )
    @patch('openedx.core.djangoapps.waffle_utils.set_custom_metric')
    def test_waffle_flag_metric_for_various_settings(self, data, mock_set_custom_metric):
        with override_settings(WAFFLE_FLAG_CUSTOM_METRICS=data['waffle_flag_metric_setting']):
            with patch(
                'openedx.core.djangoapps.waffle_utils._WAFFLE_FLAG_CUSTOM_METRIC_SET',
                _get_waffle_flag_custom_metrics_set(),
            ):
                test_course_flag = CourseWaffleFlag(self.TEST_NAMESPACE, self.FLAG_NAME)
                test_course_flag.is_enabled(self.TEST_COURSE_KEY)
                test_course_flag_2 = CourseWaffleFlag(self.TEST_NAMESPACE, self.FLAG_2_NAME)
                test_course_flag_2.is_enabled(self.TEST_COURSE_KEY)

        self.assertEqual(mock_set_custom_metric.call_count, data['expected_count'])

    def _assert_waffle_flag_metric(self, mock_set_custom_metric, expected_flag_value=None, flag_undefined_default=None):
        if expected_flag_value:
            expected_flag_name = 'flag_{}'.format(self.NAMESPACED_FLAG_NAME)
            expected_calls = [call(expected_flag_name, expected_flag_value)]
            mock_set_custom_metric.assert_has_calls(expected_calls)
            expected_call_count = 2 if flag_undefined_default else 1
            self.assertEqual(mock_set_custom_metric.call_count, expected_call_count)
        else:
            self.assertEqual(mock_set_custom_metric.call_count, 0)


class TestWaffleSwitch(TestCase):
    """
    Tests the WaffleSwitch.
    """

    NAMESPACE_NAME = "test_namespace"
    WAFFLE_SWITCH_NAME = "test_switch_name"
    TEST_NAMESPACE = WaffleSwitchNamespace(NAMESPACE_NAME)
    WAFFLE_SWITCH = WaffleSwitch(TEST_NAMESPACE, WAFFLE_SWITCH_NAME)

    def test_namespaced_switch_name(self):
        """
        Verify namespaced_switch_name returns the correct namespace switch name
        """
        expected = self.NAMESPACE_NAME + "." + self.WAFFLE_SWITCH_NAME
        actual = self.WAFFLE_SWITCH.namespaced_switch_name
        self.assertEqual(actual, expected)
