from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import AuditLog, DailyActiveUserMetric
from apps.analytics.serializers import AuditLogSerializer, DailyActiveUserMetricSerializer
from apps.analytics.services import AnalyticsRollupService
from apps.courses.models import Course
from apps.users.permissions import IsAdminUserOnly, IsInstructor


class InstructorCourseAnalyticsView(APIView):
    """
    Detailed course engagement & pedagogical analytics for course authors (FR-ANL-02).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_slug, *args, **kwargs):
        course = Course.objects.filter(slug=course_slug).first()
        if not course:
            raise NotFound(detail="Course not found.")

        # Ensure user is the instructor of this course or an admin
        is_owner = course.instructor_id == request.user.id
        is_admin = request.user.role == "ADMIN"
        if not (is_owner or is_admin):
            raise PermissionDenied(detail="You do not have permission to view analytics for this course.")

        analytics_data = AnalyticsRollupService.get_instructor_course_analytics(course)
        return Response(analytics_data, status=status.HTTP_200_OK)


class AdminPlatformOverviewView(APIView):
    """
    Executive platform overview & real-time operational telemetry (FR-ANL-03, FR-ADM-03).
    """
    permission_classes = [IsAdminUserOnly]

    def get(self, request, *args, **kwargs):
        overview_data = AnalyticsRollupService.get_admin_platform_overview()
        return Response(overview_data, status=status.HTTP_200_OK)


class LearnerEngagementView(APIView):
    """
    Personal learning statistics, streak metrics, and course completions (FR-ANL-01).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        summary = AnalyticsRollupService.get_learner_engagement_summary(request.user)
        return Response(summary, status=status.HTTP_200_OK)


class AuditLogListView(generics.ListAPIView):
    """
    Governance and compliance audit trail for administrators (FR-ADM-04, FR-PRV-01).
    """
    permission_classes = [IsAdminUserOnly]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor").all()
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        return qs.order_by("-timestamp")[:100]


class DailyActiveMetricsView(generics.ListAPIView):
    """
    Historical daily active users and registration trends (FR-ANL-03).
    """
    permission_classes = [IsAdminUserOnly]
    serializer_class = DailyActiveUserMetricSerializer

    def get_queryset(self):
        return DailyActiveUserMetric.objects.all().order_by("-date")[:60]
