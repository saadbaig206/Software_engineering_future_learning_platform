from rest_framework import serializers
from apps.courses.models import Course, Lesson
from apps.learning.models import (
    LearningPath,
    LearningPathItem,
    LessonSkill,
    Skill,
    SkillPrerequisite,
    StudentSkill,
)
from apps.progress.serializers import LessonSummarySerializer


class SkillSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "slug", "description"]


class SkillPrerequisiteSerializer(serializers.ModelSerializer):
    prerequisite = SkillSummarySerializer(read_only=True)

    class Meta:
        model = SkillPrerequisite
        fields = ["id", "prerequisite"]


class SkillDetailSerializer(serializers.ModelSerializer):
    prerequisites = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = ["id", "name", "slug", "description", "prerequisites"]

    def get_prerequisites(self, obj):
        return [
            {"id": str(p.prerequisite.id), "name": p.prerequisite.name, "slug": p.prerequisite.slug}
            for p in obj.prerequisites.select_related("prerequisite")
        ]


class StudentSkillSerializer(serializers.ModelSerializer):
    skill = SkillDetailSerializer(read_only=True)

    class Meta:
        model = StudentSkill
        fields = ["id", "skill", "mastery_score", "updated_at"]


class LearningPathItemSerializer(serializers.ModelSerializer):
    lesson = LessonSummarySerializer(read_only=True)

    class Meta:
        model = LearningPathItem
        fields = [
            "id",
            "position",
            "path_type",
            "reason",
            "is_completed",
            "lesson",
        ]


class LearningPathSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source="course.id", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)
    items = LearningPathItemSerializer(many=True, read_only=True)

    class Meta:
        model = LearningPath
        fields = [
            "id",
            "course_id",
            "course_title",
            "course_slug",
            "status",
            "generated_at",
            "items",
        ]


class EvaluateSkillInputSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=1000, required=True)
    max_score = serializers.IntegerField(min_value=1, max_value=1000, default=100)
    async_mode = serializers.BooleanField(default=False)
