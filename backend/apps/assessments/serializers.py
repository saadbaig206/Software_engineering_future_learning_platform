from rest_framework import serializers
from apps.assessments.models import (
    Assessment,
    Question,
    Choice,
    QuizAttempt,
    QuestionResponse,
)


class LearnerChoiceSerializer(serializers.ModelSerializer):
    """Safe choice serializer omitting is_correct (FR-ASM-02)."""
    class Meta:
        model = Choice
        fields = ["id", "text", "position"]


class InstructorChoiceSerializer(serializers.ModelSerializer):
    """Full choice serializer for course authors and instructors."""
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct", "position", "feedback"]


class LearnerQuestionSerializer(serializers.ModelSerializer):
    """Safe question serializer concealing explanation and answer keys."""
    choices = LearnerChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "prompt",
            "points",
            "position",
            "code_language",
            "initial_code",
            "choices",
        ]


class InstructorQuestionSerializer(serializers.ModelSerializer):
    """Full question serializer for course authors and instructors."""
    choices = InstructorChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "prompt",
            "points",
            "position",
            "explanation",
            "target_skill",
            "discrimination_weight",
            "code_language",
            "initial_code",
            "choices",
        ]


class AssessmentSummarySerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(source="questions.count", read_only=True)
    total_points = serializers.IntegerField(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "passing_score_percent",
            "time_limit_minutes",
            "max_attempts",
            "randomize_questions",
            "is_published",
            "question_count",
            "total_points",
        ]


class LearnerAssessmentDetailSerializer(serializers.ModelSerializer):
    """
    Secure learner assessment payload.
    Omits answer keys and explanations until submitted.
    Includes student's attempt statistics.
    """
    questions = LearnerQuestionSerializer(many=True, read_only=True)
    attempts_used = serializers.SerializerMethodField()
    attempts_remaining = serializers.SerializerMethodField()
    highest_score = serializers.SerializerMethodField()
    has_passed = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "passing_score_percent",
            "time_limit_minutes",
            "max_attempts",
            "is_published",
            "questions",
            "attempts_used",
            "attempts_remaining",
            "highest_score",
            "has_passed",
        ]

    def get_attempts_used(self, obj) -> int:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return QuizAttempt.objects.filter(assessment=obj, learner=request.user).count()
        return 0

    def get_attempts_remaining(self, obj) -> int:
        used = self.get_attempts_used(obj)
        return max(0, obj.max_attempts - used)

    def get_highest_score(self, obj) -> float:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            attempts = QuizAttempt.objects.filter(
                assessment=obj, learner=request.user, status=QuizAttempt.Status.SUBMITTED
            )
            if attempts.exists():
                return max(a.score_percent for a in attempts)
        return 0.0

    def get_has_passed(self, obj) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return QuizAttempt.objects.filter(
                assessment=obj, learner=request.user, passed=True
            ).exists()
        return False


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "assessment",
            "attempt_number",
            "status",
            "started_at",
            "submitted_at",
            "score_percent",
            "points_earned",
            "points_possible",
            "passed",
        ]


class SubmitAttemptSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.JSONField(),
        help_text="Keyed by question_id with selected choice IDs or text values",
    )
