import uuid
from django.db import models
from apps.courses.models import Course, Lesson
from apps.users.models import User


class MediaAsset(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Upload"
        PROCESSING = "PROCESSING", "Processing (Validation/Thumbnail)"
        READY = "READY", "Ready for Playback"
        REJECTED = "REJECTED", "Rejected (Validation Failed)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="uploaded_media"
    )
    storage_key = models.CharField(max_length=500, unique=True, db_index=True)
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField()
    duration_seconds = models.PositiveIntegerField(
        default=0, help_text="Duration in seconds for video/audio"
    )
    thumbnail_key = models.CharField(max_length=500, blank=True)
    transcript_url = models.URLField(max_length=500, blank=True)
    captions_url = models.URLField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


class ContentBlock(models.Model):
    class BlockType(models.TextChoices):
        TEXT = "TEXT", "Rich Text / Markdown"
        VIDEO = "VIDEO", "Streaming Video"
        AUDIO = "AUDIO", "Audio Track"
        PDF = "PDF", "Document / PDF"
        SIMULATION = "SIMULATION", "Interactive Simulation"
        QUIZ_REF = "QUIZ_REF", "Quiz Reference"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="content_blocks"
    )
    block_type = models.CharField(max_length=20, choices=BlockType.choices, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)
    content_payload = models.JSONField(
        default=dict,
        help_text="Polymorphic structured JSON payload (markdown, parameters, embed urls, etc.)"
    )
    media_asset = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True, related_name="content_blocks"
    )
    is_draft = models.BooleanField(
        default=False,
        help_text="If True, this is an unreleased draft working copy (FR-CRS-07)"
    )
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.lesson.title} - B{self.position} [{self.block_type}]"


class CourseVersionSnapshot(models.Model):
    """
    FR-CRS-07: Course content versioning snapshot capturing course, module, lesson,
    and block definitions when an instructor commits or publishes a version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="version_snapshots"
    )
    version_number = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    snapshot_payload = models.JSONField(
        help_text="Complete JSON serialisation of course structure and content blocks at release time"
    )
    changelog = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        unique_together = [("course", "version_number")]

    def __str__(self):
        return f"{self.course.title} v{self.version_number}"
