import uuid
from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.courses.models import Course, Enrollment, Lesson


class LessonProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not Started"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="lesson_progresses"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="progress_records"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED, db_index=True
    )
    completion_percent = models.PositiveSmallIntegerField(
        default=0, help_text="0-100 percentage of lesson completion"
    )
    last_position_seconds = models.PositiveIntegerField(
        default=0, help_text="Video/Audio playback or reading position resume point"
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = [("enrollment", "lesson")]
        indexes = [
            models.Index(fields=["enrollment", "status"]),
            models.Index(fields=["lesson", "status"]),
        ]

    def __str__(self):
        return f"{self.enrollment.learner.email} - {self.lesson.title}: {self.status} ({self.completion_percent}%)"

    def mark_complete(self):
        """
        Marks lesson complete (FR-TRK-01 / FR-TRK-02) and triggers
        atomic recalculation of the parent course enrollment progress.
        """
        self.status = self.Status.COMPLETED
        self.completion_percent = 100
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completion_percent", "completed_at", "updated_at"])
        
        # Atomically re-evaluate overall course completion
        return self.enrollment.calculate_progress()


class LearningEvent(models.Model):
    class EventType(models.TextChoices):
        LESSON_START = "LESSON_START", "Lesson Started"
        MEDIA_HEARTBEAT = "MEDIA_HEARTBEAT", "Media Heartbeat Resume Update"
        SIM_INTERACTION = "SIM_INTERACTION", "Simulation Interaction"
        QUIZ_SUBMIT = "QUIZ_SUBMIT", "Quiz Attempt Submitted"
        LESSON_COMPLETE = "LESSON_COMPLETE", "Lesson Completed"
        PATH_REGENERATE = "PATH_REGENERATE", "Learning Path Regenerated"
        PROGRESS_RESET = "PROGRESS_RESET", "Course Progress Reset"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="learning_events"
    )
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.SET_NULL, null=True, blank=True, related_name="learning_events"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="learning_events"
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    payload = models.JSONField(
        default=dict,
        help_text="Immutable structured telemetry payload (duration, coordinates, answers, scores)"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "event_type", "-timestamp"]),
            models.Index(fields=["lesson", "event_type"]),
        ]

    def __str__(self):
        ts = self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else 'pending'
        return f"[{ts}] {self.user.email} -> {self.event_type}"
