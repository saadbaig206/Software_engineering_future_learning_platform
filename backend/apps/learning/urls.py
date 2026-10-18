from django.urls import path
from apps.learning.views import (
    EvaluateSkillAPIView,
    LearningPathAPIView,
    LearningPathRegenerateAPIView,
    SkillListAPIView,
)

app_name = "learning"

urlpatterns = [
    path("paths/<slug:course_slug>/", LearningPathAPIView.as_view(), name="learning-path"),
    path("paths/<slug:course_slug>/regenerate/", LearningPathRegenerateAPIView.as_view(), name="learning-path-regenerate"),
    path("skills/", SkillListAPIView.as_view(), name="skill-list"),
    path("skills/<slug:skill_slug>/evaluate/", EvaluateSkillAPIView.as_view(), name="skill-evaluate"),
]
