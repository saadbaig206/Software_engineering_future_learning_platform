import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from apps.users.models import User
from apps.courses.models import Category, Course, Lesson


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="skills"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SkillPrerequisite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name="prerequisites"
    )
    prerequisite = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name="dependent_skills"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("skill", "prerequisite")]
        ordering = ["skill__name", "prerequisite__name"]

    def __str__(self):
        return f"{self.prerequisite.name} -> {self.skill.name}"

    def clean(self):
        """
        Enforces Knowledge-Space Theory Directed Acyclic Graph (DAG) invariants (FR-PER-01).
        Prevents self-dependencies and circular prerequisite cycles.
        """
        if self.skill_id and self.prerequisite_id and self.skill_id == self.prerequisite_id:
            raise ValidationError("A skill cannot be a prerequisite of itself.")

        # Cycle detection via depth-first search
        visited = set()
        queue = [self.prerequisite_id]
        while queue:
            current_id = queue.pop(0)
            if current_id == self.skill_id:
                raise ValidationError(
                    f"Circular prerequisite dependency detected in skill DAG: "
                    f"'{self.prerequisite.name}' already transitively depends on '{self.skill.name}'."
                )
            if current_id not in visited:
                visited.add(current_id)
                # Find all prerequisites of current_id
                prereq_ids = SkillPrerequisite.objects.filter(
                    skill_id=current_id
                ).values_list("prerequisite_id", flat=True)
                queue.extend(prereq_ids)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class LessonSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="lesson_skills"
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name="skill_lessons"
    )
    contribution_weight = models.FloatField(
        default=1.0,
        help_text="Weight of this lesson towards mastering the skill (0.0 to 1.0)"
    )

    class Meta:
        unique_together = [("lesson", "skill")]
        ordering = ["lesson", "skill"]

    def __str__(self):
        return f"{self.lesson.title} - {self.skill.name} ({self.contribution_weight})"


class StudentSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="skill_masteries"
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name="student_masteries"
    )
    mastery_score = models.PositiveSmallIntegerField(
        default=0,
        help_text="Continuous mastery score 0-100% (FR-PER-02)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("learner", "skill")]
        indexes = [
            models.Index(fields=["learner", "mastery_score"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.learner.email} - {self.skill.name}: {self.mastery_score}%"

    def update_mastery(self, new_score: int):
        self.mastery_score = max(0, min(100, int(new_score)))
        self.save(update_fields=["mastery_score", "updated_at"])


class LearningPath(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="learning_paths"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="learning_paths"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["learner", "course", "status"]),
        ]

    def __str__(self):
        return f"Path for {self.learner.email} in {self.course.title} [{self.status}]"


class LearningPathItem(models.Model):
    class PathType(models.TextChoices):
        STANDARD = "STANDARD", "Standard Linear Sequence"
        REMEDIATION = "REMEDIATION", "Remedial Prerequisite Review"
        ENRICHMENT = "ENRICHMENT", "Advanced Enrichment Challenge"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learning_path = models.ForeignKey(
        LearningPath, on_delete=models.CASCADE, related_name="items"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="path_items"
    )
    position = models.PositiveIntegerField(default=0)
    path_type = models.CharField(
        max_length=20, choices=PathType.choices, default=PathType.STANDARD
    )
    reason = models.CharField(
        max_length=500,
        help_text="Explainable pedagogical justification (FR-PER-03 / D-004)"
    )
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["position"]
        unique_together = [("learning_path", "lesson")]

    def __str__(self):
        return f"Item {self.position}: {self.lesson.title} ({self.path_type})"
