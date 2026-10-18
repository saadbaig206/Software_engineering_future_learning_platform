import uuid
from django.db import models
from apps.common.models import BaseTimeStampedModel
from apps.users.models import User


class Notification(BaseTimeStampedModel):
    """
    In-app asynchronous notification record.
    Fulfills FR-NOT-01 and FR-NOT-02.
    """
    class NotificationType(models.TextChoices):
        FORUM_REPLY = "FORUM_REPLY", "Reply to Discussion Thread"
        ANSWER_ENDORSED = "ANSWER_ENDORSED", "Answer Endorsed by Instructor"
        ASSESSMENT_GRADED = "ASSESSMENT_GRADED", "Quiz Attempt Graded"
        COURSE_ANNOUNCEMENT = "COURSE_ANNOUNCEMENT", "Course Announcement"
        REPORT_RESOLVED = "REPORT_RESOLVED", "Moderation Report Resolved"
        SIMULATION_MILESTONE = "SIMULATION_MILESTONE", "Simulation Milestone Reached"

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(
        max_length=50, choices=NotificationType.choices, default=NotificationType.FORUM_REPLY, db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient.email}: {self.title} ({self.notification_type})"
