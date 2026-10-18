from rest_framework import serializers
from apps.courses.models import Course, Enrollment, Lesson
from apps.progress.models import LearningEvent, LessonProgress


class LessonSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "position",
            "estimated_duration_minutes",
            "is_required",
            "is_preview",
        ]


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson = LessonSummarySerializer(read_only=True)
    lesson_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "lesson",
            "lesson_id",
            "status",
            "completion_percent",
            "last_position_seconds",
            "completed_at",
            "updated_at",
        ]
        read_only_fields = ["id", "completed_at", "updated_at"]


class HeartbeatInputSerializer(serializers.Serializer):
    lesson_id = serializers.UUIDField(required=True)
    position_seconds = serializers.IntegerField(min_value=0, default=0)
    completion_percent = serializers.IntegerField(min_value=0, max_value=100, default=0)
    is_completed = serializers.BooleanField(default=False)
    client_timestamp = serializers.FloatField(required=False)


class CourseProgressDetailSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    course_title = serializers.CharField()
    course_slug = serializers.CharField()
    enrollment_status = serializers.CharField()
    total_required_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()
    completion_percent = serializers.FloatField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    last_active_lesson = serializers.DictField(allow_null=True)
    lessons = LessonProgressSerializer(many=True)


class LearningEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningEvent
        fields = [
            "id",
            "event_type",
            "payload",
            "timestamp",
            "lesson",
        ]
        read_only_fields = ["id", "timestamp"]
