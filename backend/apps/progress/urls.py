from django.urls import path
from apps.progress.views import (
    CourseProgressDetailAPIView,
    CourseProgressResetAPIView,
    HeartbeatAPIView,
    LessonCompleteAPIView,
)

app_name = "progress"

urlpatterns = [
    path("heartbeat/", HeartbeatAPIView.as_view(), name="heartbeat"),
    path("courses/<slug:slug>/", CourseProgressDetailAPIView.as_view(), name="course-progress"),
    path("courses/<slug:slug>/reset/", CourseProgressResetAPIView.as_view(), name="course-progress-reset"),
    path("lessons/<uuid:lesson_id>/complete/", LessonCompleteAPIView.as_view(), name="lesson-complete"),
]
