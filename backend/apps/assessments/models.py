import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.courses.models import Course, Lesson
from apps.users.models import User
from apps.learning.models import Skill


class Assessment(models.Model):
    """
    Assessment metadata and configuration.
    Supports formative quizzes, summative exams, and standalone checkpoints.
    Fulfills FR-ASM-01, FR-ASM-03, FR-ASM-05, and D-004.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="assessments"
    )
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessment",
        help_text="Optional 1-to-1 link if this assessment is a lesson checkpoint.",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    passing_score_percent = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Percentage required to pass and complete checkpoint.",
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=0,
        help_text="0 indicates untimed assessment. Positive value enforces countdown.",
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Configured by instructor. Server enforces limit (FR-ASM-03).",
    )
    randomize_questions = models.BooleanField(
        default=False,
        help_text="If True, shuffle question order for each attempt (FR-ASM-06).",
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.title} ({self.course.title})"

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    """
    Polymorphic assessment question item.
    Supports single choice, multiple choice, true/false, short answer, and code snippet.
    Fulfills FR-ASM-01 and FR-ASM-04.
    """
    class QuestionType(models.TextChoices):
        SINGLE_CHOICE = "SINGLE_CHOICE", "Single Choice Radio"
        MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple Choice Checkbox"
        TRUE_FALSE = "TRUE_FALSE", "True / False"
        SHORT_ANSWER = "SHORT_ANSWER", "Short Text Response"
        CODE_SNIPPET = "CODE_SNIPPET", "Code Analysis / Execution"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="questions"
    )
    question_type = models.CharField(
        max_length=20, choices=QuestionType.choices, default=QuestionType.SINGLE_CHOICE
    )
    prompt = models.TextField(help_text="Markdown-supported question prompt")
    points = models.PositiveIntegerField(default=1)
    position = models.PositiveIntegerField(default=0)
    explanation = models.TextField(
        blank=True,
        help_text="Pedagogical feedback revealed AFTER attempt grading (FR-ASM-04).",
    )
    target_skill = models.ForeignKey(
        Skill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessment_questions",
        help_text="Target skill node in KST DAG for adaptive calibration.",
    )
    discrimination_weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(2.0)],
        help_text="Item discrimination weight for adaptive mastery computation.",
    )
    code_language = models.CharField(
        max_length=50, default="python", blank=True, help_text="Language for syntax display"
    )
    initial_code = models.TextField(
        blank=True, help_text="Starter code template for code snippet questions"
    )

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Q{self.position + 1}: {self.prompt[:40]}... ({self.question_type})"


class Choice(models.Model):
    """
    Selectable option for single choice, multiple choice, and true/false questions.
    Server conceals is_correct from learners until attempt submission.
    Fulfills FR-ASM-02.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    feedback = models.CharField(
        max_length=500, blank=True, help_text="Specific feedback if this option is chosen"
    )

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Choice: {self.text[:30]} (Correct: {self.is_correct})"


class QuizAttempt(models.Model):
    """
    Immutable learner assessment attempt record.
    Enforces attempt limits, time boundaries, and server-side grade calculation.
    Fulfills FR-ASM-02, FR-ASM-03, FR-ASM-05.
    """
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SUBMITTED = "SUBMITTED", "Submitted & Graded"
        TIMED_OUT = "TIMED_OUT", "Timed Out"
        ABANDONED = "ABANDONED", "Abandoned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="attempts"
    )
    learner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS, db_index=True
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score_percent = models.FloatField(default=0.0)
    points_earned = models.FloatField(default=0.0)
    points_possible = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    answers_payload = models.JSONField(
        default=dict,
        help_text="Learner submitted answers keyed by question_id",
    )

    class Meta:
        ordering = ["-started_at"]
        unique_together = ("assessment", "learner", "attempt_number")

    def __str__(self):
        return f"{self.learner.email} - {self.assessment.title} (Attempt #{self.attempt_number}: {self.score_percent}%)"


class QuestionResponse(models.Model):
    """
    Granular per-question grading breakdown for an attempt.
    Enables explainable pedagogical feedback (FR-ASM-04).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="responses"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="responses"
    )
    selected_choices = models.ManyToManyField(Choice, blank=True)
    text_response = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    awarded_points = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"Response for Q-{self.question_id}: {self.awarded_points}/{self.question.points} pts"
