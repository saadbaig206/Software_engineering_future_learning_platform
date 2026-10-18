from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.assessments.models import Assessment, QuizAttempt
from apps.assessments.serializers import (
    LearnerAssessmentDetailSerializer,
    AssessmentSummarySerializer,
    QuizAttemptSerializer,
    SubmitAttemptSerializer,
)
from apps.assessments.services import (
    AssessmentGraderService,
    AttemptLimitExceededError,
)


class AssessmentDetailView(RetrieveAPIView):
    """
    Retrieve assessment structure with questions for learners or instructors.
    Conceals answers for students (FR-ASM-02).
    """
    queryset = Assessment.objects.prefetch_related("questions__choices").filter(is_published=True)
    serializer_class = LearnerAssessmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


class AssessmentByLessonView(APIView):
    """
    Fetch the assessment associated with a specific lesson checkpoint.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, lesson_id):
        assessment = get_object_or_404(
            Assessment.objects.prefetch_related("questions__choices").filter(is_published=True),
            lesson_id=lesson_id,
        )
        serializer = LearnerAssessmentDetailSerializer(assessment, context={"request": request})
        return Response(serializer.data)


class StartAttemptView(APIView):
    """
    Start or resume a quiz attempt.
    Enforces max_attempts configured by the instructor (FR-ASM-03).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Resumed existing active attempt"),
            201: OpenApiResponse(description="Started new attempt"),
            400: OpenApiResponse(description="Attempt limit exceeded"),
        }
    )
    def post(self, request, id):
        assessment = get_object_or_404(Assessment, id=id, is_published=True)
        try:
            attempt = AssessmentGraderService.start_or_resume_attempt(
                assessment=assessment, learner=request.user
            )
            serializer = QuizAttemptSerializer(attempt)
            status_code = status.HTTP_200_OK if attempt.status == QuizAttempt.Status.IN_PROGRESS and attempt.attempt_number > 0 else status.HTTP_201_CREATED
            return Response(serializer.data, status=status_code)
        except AttemptLimitExceededError as e:
            return Response(
                {"detail": str(e), "error_code": "ATTEMPT_LIMIT_EXCEEDED"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SubmitAttemptView(APIView):
    """
    Submit answers for grading.
    Executes server-side secure scoring, evaluates partial credit,
    records results, and triggers adaptive KST skill calibrations (FR-ASM-02, FR-ASM-04).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=SubmitAttemptSerializer)
    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            QuizAttempt, id=attempt_id, learner=request.user
        )
        serializer = SubmitAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = serializer.validated_data["answers"]
        result = AssessmentGraderService.grade_attempt(
            attempt=attempt, answers=answers
        )
        return Response(result, status=status.HTTP_200_OK)


class AssessmentAttemptsListView(ListAPIView):
    """
    List historical attempts for an assessment by the current learner.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizAttemptSerializer

    def get_queryset(self):
        assessment_id = self.kwargs["id"]
        return QuizAttempt.objects.filter(
            assessment_id=assessment_id, learner=self.request.user
        ).order_by("-started_at")
