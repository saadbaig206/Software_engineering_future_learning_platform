from django.urls import path
from apps.analytics.views import (
    InstructorCourseAnalyticsView,
    AdminPlatformOverviewView,
    LearnerEngagementView,
    AuditLogListView,
    DailyActiveMetricsView,
)

app_name = "analytics"

urlpatterns = [
    path("instructor/<slug:course_slug>/", InstructorCourseAnalyticsView.as_view(), name="instructor-course-analytics"),
    path("admin/overview/", AdminPlatformOverviewView.as_view(), name="admin-overview"),
    path("admin/audit-logs/", AuditLogListView.as_view(), name="admin-audit-logs"),
    path("admin/metrics/daily/", DailyActiveMetricsView.as_view(), name="admin-daily-metrics"),
    path("learner/engagement/", LearnerEngagementView.as_view(), name="learner-engagement"),
]
