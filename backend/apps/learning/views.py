from django.core.cache import cache
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, Enrollment
from apps.learning.engine import get_adaptive_engine
from apps.learning.models import LearningPath, Skill, StudentSkill
from apps.learning.serializers import (
    EvaluateSkillInputSerializer,
    LearningPathSerializer,
    SkillDetailSerializer,
    StudentSkillSerializer,
)
from apps.learning.tasks import recompute_student_mastery_task


class LearningPathAPIView(APIView):
    """
    FR-PER-04: Dynamic Learning Path Assembly.
    Returns the learner's explainable personalized learning path for a course.
    If no active path exists, generates one immediately using the Adaptive Engine.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: LearningPathSerializer})
    def get(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        enrollment = get_object_or_404(
            Enrollment, learner=request.user, course=course
        )

        engine = get_adaptive_engine()
        path = LearningPath.objects.filter(
            learner=request.user,
            course=course,
            status=LearningPath.Status.ACTIVE,
        ).first()

        if not path or not path.items.exists():
            path = engine.generate_path(request.user, course)

        serializer = LearningPathSerializer(path)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LearningPathRegenerateAPIView(APIView):
    """
    FR-PER-04: Rate-limited On-Demand Path Regeneration.
    Re-calibrates the learning path based on latest skill mastery updates.
    Enforces a strict 1-minute rate limit per user per course.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: LearningPathSerializer, 429: OpenApiResponse(description="Rate limit exceeded")})
    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        enrollment = get_object_or_404(
            Enrollment, learner=request.user, course=course
        )

        cache_key = f"rate_limit:path_regen:{request.user.id}:{course.id}"
        if cache.get(cache_key):
            return Response(
                {
                    "detail": "Path regeneration is rate-limited to once per minute. Please try again shortly.",
                    "retry_after_seconds": 60,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Set 60-second cooldown in Redis
        cache.set(cache_key, True, timeout=60)

        engine = get_adaptive_engine()
        path = engine.generate_path(request.user, course)
        serializer = LearningPathSerializer(path)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SkillListAPIView(APIView):
    """
    Lists all pedagogical skills and the current user's mastery scores.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        skills = Skill.objects.all().prefetch_related("prerequisites__prerequisite")
        masteries = {
            ss.skill_id: ss.mastery_score
            for ss in StudentSkill.objects.filter(learner=request.user)
        }

        results = []
        for s in skills:
            results.append({
                "id": str(s.id),
                "name": s.name,
                "slug": s.slug,
                "description": s.description,
                "mastery_score": masteries.get(s.id, 0),
                "prerequisites": [
                    {"id": str(p.prerequisite.id), "name": p.prerequisite.name}
                    for p in s.prerequisites.all()
                ],
            })

        return Response(results, status=status.HTTP_200_OK)


class EvaluateSkillAPIView(APIView):
    """
    FR-PER-02 & FR-PER-05: Update or recompute learner skill mastery score.
    Supports asynchronous execution via Celery or synchronous response.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EvaluateSkillInputSerializer,
        responses={200: OpenApiResponse(description="Mastery score updated")},
    )
    def post(self, request, skill_slug):
        skill = get_object_or_404(Skill, slug=skill_slug)
        serializer = EvaluateSkillInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get("async_mode", False):
            # Asynchronous Celery dispatch
            task = recompute_student_mastery_task.delay(
                str(request.user.id),
                str(skill.id),
                data["score"],
                data["max_score"],
            )
            return Response(
                {
                    "status": "queued",
                    "task_id": task.id,
                    "message": "Mastery recomputation dispatched to background adaptive worker.",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # Synchronous execution
        engine = get_adaptive_engine()
        student_skill = engine.update_mastery(
            request.user, skill, data["score"], data["max_score"]
        )

        return Response(
            {
                "status": "success",
                "skill": skill.name,
                "mastery_score": student_skill.mastery_score,
                "updated_at": student_skill.updated_at,
            },
            status=status.HTTP_200_OK,
        )
