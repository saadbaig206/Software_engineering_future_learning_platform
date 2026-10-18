from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny

urlpatterns = [
    # Administration
    path("admin/", admin.site.urls),

    # OpenAPI v3 Documentation
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema", permission_classes=[AllowAny]), name="redoc"),

    # API v1 Health & Diagnostics
    path("api/v1/", include("apps.common.urls", namespace="common")),

    # API v1 Authentication & Users
    path("api/v1/auth/", include("apps.users.urls")),

    # API v1 Courses, Categories & Enrollments
    path("api/v1/", include("apps.courses.urls")),

    # API v1 Content Blocks & Media Pipelines
    path("api/v1/content/", include("apps.content.urls")),

    # API v1 Progress Tracking & Telemetry
    path("api/v1/progress/", include("apps.progress.urls")),

    # API v1 Adaptive Learning Paths & Skills
    path("api/v1/learning/", include("apps.learning.urls")),

    # API v1 Assessments & Quizzes
    path("api/v1/", include("apps.assessments.urls")),

    # API v1 Discussions & Moderation
    path("api/v1/", include("apps.discussions.urls")),

    # API v1 In-App Notifications
    path("api/v1/", include("apps.notifications.urls")),

    # API v1 Analytics & Performance Telemetry
    path("api/v1/analytics/", include("apps.analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
