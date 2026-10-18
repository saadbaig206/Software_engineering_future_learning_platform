from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.courses.views import (
    CategoryViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    LessonViewSet,
    ModuleViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"modules", ModuleViewSet, basename="module")
router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = [
    path("", include(router.urls)),
]
