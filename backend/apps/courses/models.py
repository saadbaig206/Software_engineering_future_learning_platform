import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from apps.users.models import User


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Lucide or Heroicon identifier")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"
        ALL_LEVELS = "ALL_LEVELS", "All Levels"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        IN_REVIEW = "IN_REVIEW", "In Review"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="instructed_courses"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField()
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    difficulty = models.CharField(
        max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    estimated_duration_minutes = models.PositiveIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "difficulty"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.title} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "course"
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def publish(self):
        """
        Enforces FR-CRS-06: Course cannot be published if it has 0 modules
        or if any module contains 0 published lessons.
        """
        modules = self.modules.all()
        if not modules.exists():
            raise ValidationError("Cannot publish a course with zero modules.")
        for mod in modules:
            if not mod.lessons.filter(is_published=True).exists():
                raise ValidationError(f"Module '{mod.title}' has no published lessons.")
        
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.save(update_fields=["status", "updated_at"])


class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]
        unique_together = [("course", "position")]

    def __str__(self):
        return f"{self.course.title} - M{self.position}: {self.title}"


class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    position = models.PositiveIntegerField(default=0)
    estimated_duration_minutes = models.PositiveIntegerField(default=10)
    is_required = models.BooleanField(default=True)
    is_preview = models.BooleanField(
        default=False,
        help_text="If True, accessible to unauthenticated guests and non-enrolled learners (FR-CRS-02)"
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]
        unique_together = [("module", "position")]

    def __str__(self):
        return f"{self.module.title} - L{self.position}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) or "lesson"
        super().save(*args, **kwargs)


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        DROPPED = "DROPPED", "Dropped"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-enrolled_at"]
        unique_together = [("learner", "course")]

    def __str__(self):
        return f"{self.learner.email} enrolled in {self.course.title} [{self.status}]"

    def calculate_progress(self) -> float:
        """
        Enforces FR-TRK-02: Deterministic Course Completion Evaluation.
        Computes overall course progress percentage based on completed required lessons.
        Transitions status to COMPLETED if all required units are finished.
        """
        from apps.progress.models import LessonProgress
        required_lessons = Lesson.objects.filter(
            module__course=self.course,
            is_published=True,
            is_required=True
        )
        total_required = required_lessons.count()
        if total_required == 0:
            return 0.0

        completed_count = LessonProgress.objects.filter(
            enrollment=self,
            lesson__in=required_lessons,
            status=LessonProgress.Status.COMPLETED
        ).count()

        percent = round((completed_count / total_required) * 100, 1)
        if completed_count >= total_required and self.status != self.Status.COMPLETED:
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at"])
        elif completed_count < total_required and self.status == self.Status.COMPLETED:
            self.status = self.Status.ACTIVE
            self.completed_at = None
            self.save(update_fields=["status", "completed_at"])
        return percent

    def get_progress_summary(self) -> dict:
        from apps.progress.models import LessonProgress
        required_lessons = Lesson.objects.filter(
            module__course=self.course,
            is_published=True,
            is_required=True
        )
        total_required = required_lessons.count()
        completed_count = LessonProgress.objects.filter(
            enrollment=self,
            lesson__in=required_lessons,
            status=LessonProgress.Status.COMPLETED
        ).count() if total_required > 0 else 0
        percent = round((completed_count / total_required) * 100, 1) if total_required > 0 else 0.0
        return {
            "total_lessons": total_required,
            "completed_lessons": completed_count,
            "completion_percent": percent,
            "is_completed": self.status == self.Status.COMPLETED,
            "completed_at": self.completed_at,
        }

