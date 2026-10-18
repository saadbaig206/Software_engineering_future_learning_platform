import uuid
from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.courses.models import Course


class DailyActiveUserMetric(models.Model):
    """
    Daily aggregated platform-wide engagement metrics (FR-ANL-03).
    """
    date = models.DateField(unique=True, db_index=True)
    daily_active_users = models.PositiveIntegerField(default=0)
    new_registrations = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    course_completions = models.PositiveIntegerField(default=0)
    total_learning_minutes = models.PositiveIntegerField(default=0)
    quiz_attempts_submitted = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["-date"]),
        ]

    def __str__(self):
        return f"Metrics [{self.date}]: {self.daily_active_users} DAU, {self.new_registrations} new users"


class CourseAnalyticsSnapshot(models.Model):
    """
    Daily/Weekly aggregate snapshot per course for instructors (FR-ANL-02).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="analytics_snapshots"
    )
    date = models.DateField(db_index=True)
    enrolled_students_count = models.PositiveIntegerField(default=0)
    active_students_count = models.PositiveIntegerField(default=0)
    completion_rate_percent = models.FloatField(default=0.0)
    avg_assessment_score = models.FloatField(default=0.0)
    drop_off_rate_percent = models.FloatField(default=0.0)
    forum_threads_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed breakdowns: difficult questions, lesson drop-off curve, score distribution"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        unique_together = [("course", "date")]
        indexes = [
            models.Index(fields=["course", "-date"]),
        ]

    def __str__(self):
        return f"{self.course.title} [{self.date}]: {self.enrolled_students_count} enrolled, {self.completion_rate_percent}% completion"


class AuditLog(models.Model):
    """
    Immutable compliance & governance audit trail (FR-ADM-04, FR-PRV-01, FR-PRV-02).
    """
    class Action(models.TextChoices):
        USER_LOGIN = "USER_LOGIN", "User Login"
        USER_REGISTER = "USER_REGISTER", "User Registration"
        ROLE_CHANGE = "ROLE_CHANGE", "User Role Changed"
        COURSE_PUBLISH = "COURSE_PUBLISH", "Course Published"
        CONTENT_MODERATION = "CONTENT_MODERATION", "Content Moderated"
        GDPR_EXPORT = "GDPR_EXPORT", "GDPR Data Exported"
        GDPR_ERASURE = "GDPR_ERASURE", "GDPR Data Erased"
        CONFIG_CHANGE = "CONFIG_CHANGE", "System Config Changed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=40, choices=Action.choices, db_index=True)
    target_model = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 hashed IP for privacy")
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action", "-timestamp"]),
            models.Index(fields=["actor", "-timestamp"]),
        ]

    def __str__(self):
        actor_name = self.actor.email if self.actor else "System/Anonymous"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {actor_name} -> {self.action} on {self.target_model}:{self.target_id}"
