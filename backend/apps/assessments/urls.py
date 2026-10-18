from django.urls import path
from apps.assessments.views import (
    AssessmentDetailView,
    AssessmentByLessonView,
    StartAttemptView,
    SubmitAttemptView,
    AssessmentAttemptsListView,
)

app_name = "assessments"

urlpatterns = [
    path("assessments/<uuid:id>/", AssessmentDetailView.as_view(), name="assessment-detail"),
    path("assessments/<uuid:id>/start/", StartAttemptView.as_view(), name="assessment-start"),
    path("assessments/<uuid:id>/attempts/", AssessmentAttemptsListView.as_view(), name="assessment-attempts"),
    path("attempts/<uuid:attempt_id>/submit/", SubmitAttemptView.as_view(), name="attempt-submit"),
    path("lessons/<uuid:lesson_id>/assessment/", AssessmentByLessonView.as_view(), name="lesson-assessment"),
]
