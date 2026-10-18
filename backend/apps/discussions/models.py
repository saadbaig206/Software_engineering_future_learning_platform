import uuid
from django.db import models
from apps.courses.models import Course, Lesson
from apps.users.models import User


class DiscussionThread(models.Model):
    """
    Contextual course or lesson discussion thread.
    Fulfills FR-DIS-01 and FR-DIS-05.
    """
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PINNED = "PINNED", "Pinned by Staff"
        LOCKED = "LOCKED", "Locked (No New Replies)"
        HIDDEN = "HIDDEN", "Hidden by Moderator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="discussion_threads"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discussion_threads",
        help_text="Optional link to specific lesson for in-context lesson queries.",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="discussion_threads"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    is_pinned = models.BooleanField(default=False)
    upvotes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return f"[{self.course.slug}] {self.title} ({self.status})"

    @property
    def replies_count(self):
        return self.posts.filter(status=DiscussionPost.Status.ACTIVE).count()


class DiscussionPost(models.Model):
    """
    Thread reply or nested comment.
    Supports 2-level/recursive replies and Instructor Answer Endorsement.
    Fulfills FR-DIS-02 and FR-DIS-03.
    """
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        HIDDEN = "HIDDEN", "Hidden by Moderator"
        FLAGGED = "FLAGGED", "Flagged for Review"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        DiscussionThread, on_delete=models.CASCADE, related_name="posts"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="discussion_posts"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        help_text="Parent reply if nested (FR-DIS-02)",
    )
    body = models.TextField()
    is_endorsed = models.BooleanField(
        default=False,
        help_text="Instructor Answer Endorsement badge (FR-DIS-03)",
    )
    endorsed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="endorsed_posts",
    )
    endorsed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    upvotes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_endorsed", "created_at"]

    def __str__(self):
        return f"Post by {self.author.email} in {self.thread.title}"


class ThreadVote(models.Model):
    """Tracks learner thread upvotes to prevent duplicate voting."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        DiscussionThread, on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("thread", "user")


class PostVote(models.Model):
    """Tracks learner post upvotes to prevent duplicate voting."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        DiscussionPost, on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")


class ContentReport(models.Model):
    """
    Moderation queue report item for abusive or off-topic posts.
    Fulfills FR-DIS-04 and FR-DIS-05.
    """
    class Reason(models.TextChoices):
        SPAM = "SPAM", "Spam or Advertising"
        HARASSMENT = "HARASSMENT", "Harassment or Hate Speech"
        ACADEMIC_DISHONESTY = "ACADEMIC_DISHONESTY", "Academic Dishonesty / Sharing Answers"
        INAPPROPRIATE = "INAPPROPRIATE", "Inappropriate or Offensive Material"
        OFF_TOPIC = "OFF_TOPIC", "Off Topic"
        OTHER = "OTHER", "Other Violation"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        RESOLVED = "RESOLVED", "Action Taken (Content Hidden/Removed)"
        DISMISSED = "DISMISSED", "Dismissed (No Violation)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="filed_reports"
    )
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    post = models.ForeignKey(
        DiscussionPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    reason = models.CharField(max_length=30, choices=Reason.choices, default=Reason.OTHER)
    details = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_reports",
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.id}: {self.reason} ({self.status})"
