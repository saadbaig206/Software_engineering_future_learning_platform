from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.content.views import (
    ContentBlockViewSet,
    CourseVersionSnapshotViewSet,
    LocalMediaUploadView,
    MediaAssetViewSet,
    MediaConfirmView,
    MediaUploadUrlView,
    SimulationScoreReportView,
)

router = DefaultRouter()
router.register(r"blocks", ContentBlockViewSet, basename="content-block")
router.register(r"assets", MediaAssetViewSet, basename="media-asset")
router.register(r"versions", CourseVersionSnapshotViewSet, basename="course-version")

urlpatterns = [
    path("media/upload-url/", MediaUploadUrlView.as_view(), name="media-upload-url-generic"),
    path("lessons/<uuid:lesson_id>/media-upload-url/", MediaUploadUrlView.as_view(), name="media-upload-url-lesson"),
    path("media-assets/confirm/", MediaConfirmView.as_view(), name="media-confirm"),
    path("media/local-upload/", LocalMediaUploadView.as_view(), name="media-local-upload"),
    path("simulations/report/", SimulationScoreReportView.as_view(), name="simulation-report"),
    path("", include(router.urls)),
]
