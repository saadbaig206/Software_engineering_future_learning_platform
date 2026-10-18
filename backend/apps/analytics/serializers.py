from rest_framework import serializers
from apps.analytics.models import AuditLog, CourseAnalyticsSnapshot, DailyActiveUserMetric


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_email",
            "action",
            "target_model",
            "target_id",
            "ip_hash",
            "changes",
            "timestamp",
        ]


class DailyActiveUserMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActiveUserMetric
        fields = "__all__"


class CourseAnalyticsSnapshotSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = CourseAnalyticsSnapshot
        fields = "__all__"
