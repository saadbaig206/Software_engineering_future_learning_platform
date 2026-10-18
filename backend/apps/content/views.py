import os
from django.conf import settings
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.content.models import ContentBlock, CourseVersionSnapshot, MediaAsset
from apps.content.serializers import (
    ContentBlockSerializer,
    CourseVersionSnapshotSerializer,
    MediaAssetSerializer,
    MediaConfirmSerializer,
    PresignedUploadRequestSerializer,
)
from apps.content.services.storage import StorageService
from apps.content.tasks import process_media_asset
from apps.courses.models import Course, Lesson
from apps.users.permissions import IsCourseOwnerOrAdmin, IsInstructor, IsInstructorOrReadOnly


class ContentBlockViewSet(viewsets.ModelViewSet):
    queryset = ContentBlock.objects.select_related("lesson", "media_asset").all()
    serializer_class = ContentBlockSerializer
    permission_classes = [IsInstructorOrReadOnly, IsCourseOwnerOrAdmin]

    def get_queryset(self):
        lesson_id = self.request.query_params.get("lesson_id")
        user = self.request.user
        queryset = self.queryset
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        # Learners only see non-draft blocks
        if not user.is_authenticated or user.role == "LEARNER":
            queryset = queryset.filter(is_draft=False)
        return queryset


class MediaUploadUrlView(APIView):
    """
    FR-MED-01: Generates a presigned direct upload URL so media bytes flow directly
    from the content author's browser to the S3 bucket without loading Django web workers.
    """
    permission_classes = [IsInstructor]

    def post(self, request, lesson_id=None):
        serializer = PresignedUploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                # Ensure instructor owns the course
                if request.user.role != "ADMIN" and not request.user.is_superuser:
                    if lesson.module.course.instructor != request.user:
                        return Response(
                            {"detail": "You do not have permission to upload media to this lesson."},
                            status=status.HTTP_403_FORBIDDEN,
                        )
            except Lesson.DoesNotExist:
                return Response({"detail": "Target lesson not found."}, status=status.HTTP_404_NOT_FOUND)

        storage_key = StorageService.generate_storage_key(
            user_id=request.user.id,
            original_filename=data["filename"],
        )

        ticket = StorageService.generate_presigned_upload(
            storage_key=storage_key,
            mime_type=data["mime_type"],
            request=request,
        )

        return Response(ticket, status=status.HTTP_200_OK)


class MediaConfirmView(APIView):
    """
    FR-MED-02: Confirms direct upload completion and initiates asynchronous
    validation, magic-byte inspection, and thumbnail generation via Celery.
    """
    permission_classes = [IsInstructor]

    def post(self, request):
        serializer = MediaConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        media_asset = MediaAsset.objects.create(
            uploaded_by=request.user,
            storage_key=data["storage_key"],
            original_filename=data["original_filename"],
            mime_type=data["mime_type"],
            size_bytes=data["size_bytes"],
            status=MediaAsset.Status.PROCESSING,
        )

        # Dispatch background Celery task
        try:
            process_media_asset.delay(str(media_asset.id))
        except Exception:
            # Fallback for sync execution in test or unbroker environments
            process_media_asset(str(media_asset.id))

        return Response(
            {
                "message": "Media upload confirmed. Processing queued.",
                "media_asset_id": str(media_asset.id),
                "status": media_asset.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class MediaAssetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MediaAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN" or user.is_superuser:
            return MediaAsset.objects.all()
        return MediaAsset.objects.filter(uploaded_by=user)


class LocalMediaUploadView(APIView):
    """
    Local development fallback endpoint handling direct binary upload when S3 is unconfigured.
    """
    permission_classes = [permissions.AllowAny]

    def put(self, request):
        storage_key = request.query_params.get("key")
        if not storage_key:
            return Response({"detail": "Missing key query parameter."}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent directory traversal
        sanitized_key = os.path.normpath(storage_key).lstrip("\\/")
        target_path = os.path.join(settings.MEDIA_ROOT, sanitized_key)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        with open(target_path, "wb") as f:
            f.write(request.body)

        return Response({"status": "uploaded", "storage_key": sanitized_key}, status=status.HTTP_200_OK)


class CourseVersionSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseVersionSnapshotSerializer
    permission_classes = [IsInstructor]

    def get_queryset(self):
        course_id = self.request.query_params.get("course_id")
        if course_id:
            return CourseVersionSnapshot.objects.filter(course_id=course_id)
        return CourseVersionSnapshot.objects.all()


class SimulationScoreReportView(APIView):
    """
    Ingests telemetry and scores reported from sandboxed simulation iframes.
    Fulfills FR-SIM-01, FR-SIM-02, FR-SIM-03, and D-004.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        from apps.courses.models import Enrollment
        from apps.progress.models import LessonProgress, LearningEvent

        block_id = request.data.get("block_id")
        if not block_id:
            return Response({"detail": "block_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        block = get_object_or_404(
            ContentBlock, id=block_id, block_type=ContentBlock.BlockType.SIMULATION
        )
        lesson = block.lesson
        course = lesson.module.course

        score_percent = float(request.data.get("score_percent", 0.0))
        completed = bool(request.data.get("completed", False))
        telemetry = request.data.get("telemetry", {})

        enrollment = Enrollment.objects.filter(learner=request.user, course=course).first()
        if not enrollment and request.user.role == "LEARNER":
            return Response(
                {"detail": "Must be enrolled in the course to report simulation scores."},
                status=status.HTTP_403_FORBIDDEN,
            )

        passing_threshold = block.content_payload.get("passing_score", 70)
        is_passed = score_percent >= passing_threshold

        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={"status": LessonProgress.Status.IN_PROGRESS},
        )
        if is_passed or completed:
            progress.status = LessonProgress.Status.COMPLETED
            progress.completion_percent = 100
            progress.completed_at = timezone.now()
            progress.save()
            if enrollment:
                enrollment.calculate_progress()

        LearningEvent.objects.create(
            user=request.user,
            enrollment=enrollment,
            lesson=lesson,
            event_type=LearningEvent.EventType.QUIZ_SUBMIT,
            payload={
                "action": "SIMULATION_SCORE",
                "block_id": str(block.id),
                "score_percent": score_percent,
                "completed": completed,
                "passed": is_passed,
                "telemetry": telemetry,
            },
        )

        return Response({
            "status": "ingested",
            "block_id": str(block.id),
            "score_percent": score_percent,
            "passed": is_passed,
            "lesson_completed": progress.status == LessonProgress.Status.COMPLETED,
        })
