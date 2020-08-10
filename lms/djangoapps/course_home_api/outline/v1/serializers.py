"""
Outline Tab Serializers.
"""

from rest_framework import serializers
from lms.djangoapps.course_home_api.dates.v1.serializers import DateSummarySerializer
from rest_framework.reverse import reverse


class CourseToolSerializer(serializers.Serializer):
    """
    Serializer for Course Tool Objects
    """
    analytics_id = serializers.CharField()
    title = serializers.CharField()
    url = serializers.SerializerMethodField()

    def get_url(self, tool):
        course_key = self.context.get('course_key')
        url = tool.url(course_key)
        request = self.context.get('request')
        return request.build_absolute_uri(url)


class CourseBlockSerializer(serializers.Serializer):
    """
    Serializer for Course Block Objects
    """
    blocks = serializers.SerializerMethodField()

    def get_blocks(self, blocks):
        return {
            str(block_key): {
                'id': str(block_key),
                'type': block_key.category,
                'display_name': blocks.get_xblock_field(block_key, 'display_name', block_key.category),
                'lms_web_url': reverse(
                    'jump_to',
                    kwargs={'course_id': str(block_key.course_key), 'location': str(block_key)},
                    request=self.context['request'],
                ),
                'children': [str(child_key) for child_key in blocks.get_children(block_key)],
            }
            for block_key in blocks
        }


class DatesWidgetSerializer(serializers.Serializer):
    """
    Serializer for Dates Widget data
    """
    course_date_blocks = DateSummarySerializer(many=True)
    dates_tab_link = serializers.CharField()
    user_timezone = serializers.CharField()


class EnrollAlertSerializer(serializers.Serializer):
    """
    Serializer for enroll alert information
    """
    can_enroll = serializers.BooleanField()
    extra_text = serializers.CharField()


class OutlineTabSerializer(serializers.Serializer):
    """
    Serializer for the Outline Tab
    """
    course_blocks = CourseBlockSerializer()
    course_expired_html = serializers.CharField()
    course_tools = CourseToolSerializer(many=True)
    dates_widget = DatesWidgetSerializer()
    enroll_alert = EnrollAlertSerializer()
    handouts_html = serializers.CharField()
    offer_html = serializers.CharField()
    welcome_message_html = serializers.CharField()
