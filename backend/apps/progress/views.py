from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, Enrollment, Lesson
from apps.progress.models import LearningEvent, LessonProgress
from apps.progress.serializers import (
    CourseProgressDetailSerializer,
    HeartbeatInputSerializer,
    LessonProgressSerializer,
)


class HeartbeatAPIView(APIView):
    """
    FR-TRK-01 & FR-TRK-02: Granular Lesson Progress Heartbeat.
    Receives debounced client telemetry during video/audio playback and reading.
    Updates position resume point, completion percentage, and evaluates course completion.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=HeartbeatInputSerializer,
        responses={
            200: OpenApiResponse(description="Heartbeat processed successfully"),
            400: OpenApiResponse(description="Invalid payload"),
            404: OpenApiResponse(description="Lesson not found"),
        },
    )
    def post(self, request):
        serializer = HeartbeatInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"),
            pk=data["lesson_id"]
        )
        course = lesson.module.course

        # Find or create active enrollment
        enrollment = Enrollment.objects.filter(
            learner=request.user,
            course=course
        ).first()

        if not enrollment:
            # If not enrolled but lesson is preview, allow tracking in session/cache
            if not lesson.is_preview:
                return Response(
                    {"detail": "You must be enrolled in this course to track progress."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            # Auto-enroll if allowed or return preview-only status
            enrollment, _ = Enrollment.objects.get_or_create(
                learner=request.user,
                course=course,
                defaults={"status": Enrollment.Status.ACTIVE}
            )

        # Update or create LessonProgress
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={
                "status": LessonProgress.Status.IN_PROGRESS,
                "last_position_seconds": data["position_seconds"],
                "completion_percent": data["completion_percent"],
            }
        )

        should_complete = data["is_completed"] or data["completion_percent"] >= 90

        if should_complete:
            course_percent = progress.mark_complete()
            event_type = LearningEvent.EventType.LESSON_COMPLETE
        else:
            progress.last_position_seconds = max(
                progress.last_position_seconds, data["position_seconds"]
            )
            progress.completion_percent = max(
                progress.completion_percent, data["completion_percent"]
            )
            if progress.status == LessonProgress.Status.NOT_STARTED:
                progress.status = LessonProgress.Status.IN_PROGRESS
            progress.save(update_fields=["last_position_seconds", "completion_percent", "status", "updated_at"])
            course_percent = enrollment.calculate_progress()
            event_type = LearningEvent.EventType.MEDIA_HEARTBEAT

        # Cache heartbeat state in Redis for low-latency retrieval
        cache_key = f"heartbeat:{request.user.id}:{lesson.id}"
        cache.set(
            cache_key,
            {
                "position_seconds": progress.last_position_seconds,
                "completion_percent": progress.completion_percent,
                "status": progress.status,
            },
            timeout=300
        )

        # Record immutable telemetry event
        LearningEvent.objects.create(
            user=request.user,
            enrollment=enrollment,
            lesson=lesson,
            event_type=event_type,
            payload={
                "position_seconds": data["position_seconds"],
                "completion_percent": data["completion_percent"],
                "is_completed": progress.status == LessonProgress.Status.COMPLETED,
            }
        )

        return Response(
            {
                "status": "success",
                "lesson_id": str(lesson.id),
                "lesson_status": progress.status,
                "lesson_completion_percent": progress.completion_percent,
                "last_position_seconds": progress.last_position_seconds,
                "course_completion_percent": course_percent,
                "is_course_completed": enrollment.status == Enrollment.Status.COMPLETED,
            },
            status=status.HTTP_200_OK
        )


class CourseProgressDetailAPIView(APIView):
    """
    Returns granular progress for all lessons in a course for the current user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CourseProgressDetailSerializer})
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        enrollment = get_object_or_404(
            Enrollment, learner=request.user, course=course
        )

        # All published lessons in course
        required_lessons = Lesson.objects.filter(
            module__course=course,
            is_published=True,
            is_required=True
        )
        total_required = required_lessons.count()

        # Lesson progress records
        progress_records = LessonProgress.objects.filter(
            enrollment=enrollment
        ).select_related("lesson")
        progress_map = {p.lesson_id: p for p in progress_records}

        completed_count = sum(
            1 for p in progress_records if p.status == LessonProgress.Status.COMPLETED
        )
        completion_percent = round((completed_count / total_required) * 100, 1) if total_required > 0 else 0.0

        # Find last active lesson for direct "Resume Learning" button (FR-TRK-03)
        last_active = progress_records.order_by("-updated_at").first()
        last_active_data = None
        if last_active:
            last_active_data = {
                "lesson_id": str(last_active.lesson.id),
                "title": last_active.lesson.title,
                "slug": last_active.lesson.slug,
                "last_position_seconds": last_active.last_position_seconds,
                "status": last_active.status,
            }

        response_data = {
            "course_id": course.id,
            "course_title": course.title,
            "course_slug": course.slug,
            "enrollment_status": enrollment.status,
            "total_required_lessons": total_required,
            "completed_lessons": completed_count,
            "completion_percent": completion_percent,
            "is_completed": enrollment.status == Enrollment.Status.COMPLETED,
            "completed_at": enrollment.completed_at,
            "last_active_lesson": last_active_data,
            "lessons": [
                LessonProgressSerializer(p).data for p in progress_records
            ],
        }

        return Response(response_data, status=status.HTTP_200_OK)


class LessonCompleteAPIView(APIView):
    """
    Direct manual action to mark a lesson completed.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"),
            pk=lesson_id
        )
        course = lesson.module.course
        enrollment = get_object_or_404(
            Enrollment, learner=request.user, course=course
        )

        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )
        course_percent = progress.mark_complete()

        # Record event
        LearningEvent.objects.create(
            user=request.user,
            enrollment=enrollment,
            lesson=lesson,
            event_type=LearningEvent.EventType.LESSON_COMPLETE,
            payload={"manual_override": True}
        )

        return Response(
            {
                "status": "success",
                "lesson_id": str(lesson.id),
                "lesson_status": progress.status,
                "course_completion_percent": course_percent,
                "is_course_completed": enrollment.status == Enrollment.Status.COMPLETED,
            },
            status=status.HTTP_200_OK
        )


class CourseProgressResetAPIView(APIView):
    """
    FR-TRK-04: Course Progress Reset & Re-study.
    Allows learners who have completed a course to reset their progress
    to study the material again while preserving audit history in LearningEvent.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        enrollment = get_object_or_404(
            Enrollment, learner=request.user, course=course
        )

        confirm = request.data.get("confirm", False)
        if not confirm:
            return Response(
                {"detail": "Explicit confirmation required: {'confirm': true}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reset all LessonProgress records for this enrollment
        LessonProgress.objects.filter(enrollment=enrollment).update(
            status=LessonProgress.Status.NOT_STARTED,
            completion_percent=0,
            last_position_seconds=0,
            completed_at=None,
            updated_at=timezone.now(),
        )

        # Reset enrollment
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.completed_at = None
        enrollment.save(update_fields=["status", "completed_at"])

        # Record audit event
        LearningEvent.objects.create(
            user=request.user,
            enrollment=enrollment,
            event_type=LearningEvent.EventType.PROGRESS_RESET,
            payload={"reset_timestamp": timezone.now().isoformat()}
        )

        return Response(
            {
                "status": "success",
                "message": f"Progress for course '{course.title}' has been reset.",
                "course_completion_percent": 0.0,
            },
            status=status.HTTP_200_OK
        )
