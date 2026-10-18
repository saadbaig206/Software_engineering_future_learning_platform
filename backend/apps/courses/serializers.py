from rest_framework import serializers
from apps.courses.models import Category, Course, Enrollment, Lesson, Module
from apps.users.serializers import UserProfileSerializer


class CategorySerializer(serializers.ModelSerializer):
    course_count = serializers.IntegerField(source="courses.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "icon", "course_count"]
        read_only_fields = ["id", "slug", "course_count"]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id", "module", "title", "slug", "position",
            "estimated_duration_minutes", "is_required", "is_preview",
            "is_published", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class ModuleSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ["id", "course", "title", "description", "position", "lessons", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_lessons(self, obj):
        # In public views, show published lessons (or preview lessons)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        is_instructor_or_admin = (
            user and user.is_authenticated and
            (user.role in ["INSTRUCTOR", "ADMIN"] or user.is_superuser)
        )
        lessons = obj.lessons.all()
        if not is_instructor_or_admin:
            lessons = lessons.filter(is_published=True)
        return LessonSerializer(lessons, many=True, context=self.context).data


class CourseListSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    module_count = serializers.IntegerField(source="modules.count", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "instructor", "category", "category_id",
            "title", "slug", "short_description", "description",
            "thumbnail_url", "difficulty", "status",
            "estimated_duration_minutes", "version", "module_count",
            "created_at", "updated_at", "published_at"
        ]
        read_only_fields = [
            "id", "slug", "instructor", "status", "version",
            "module_count", "created_at", "updated_at", "published_at"
        ]

    def get_instructor(self, obj):
        return {
            "id": str(obj.instructor.id),
            "name": f"{obj.instructor.first_name} {obj.instructor.last_name}".strip() or obj.instructor.email,
            "email": obj.instructor.email,
        }


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id", "instructor", "category", "title", "slug",
            "short_description", "description", "thumbnail_url",
            "difficulty", "status", "estimated_duration_minutes",
            "version", "modules", "is_enrolled", "created_at", "published_at"
        ]
        read_only_fields = ["id", "slug", "instructor", "status", "version", "created_at", "published_at"]

    def get_instructor(self, obj):
        return {
            "id": str(obj.instructor.id),
            "name": f"{obj.instructor.first_name} {obj.instructor.last_name}".strip() or obj.instructor.email,
            "email": obj.instructor.email,
            "avatar": obj.instructor.avatar,
            "bio": obj.instructor.bio,
        }

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            return Enrollment.objects.filter(learner=request.user, course=obj, status=Enrollment.Status.ACTIVE).exists()
        return False


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id", "slug", "status", "category", "title", "short_description", "description",
            "thumbnail_url", "difficulty", "estimated_duration_minutes"
        ]
        read_only_fields = ["id", "slug", "status"]

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["instructor"] = request.user
        return super().create(validated_data)


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    course_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "course", "course_id", "status", "enrolled_at", "completed_at"]
        read_only_fields = ["id", "status", "enrolled_at", "completed_at"]

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value)
            if course.status != Course.Status.PUBLISHED:
                raise serializers.ValidationError("Cannot enroll in an unpublished course.")
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found.")

    def create(self, validated_data):
        request = self.context.get("request")
        course_id = validated_data.pop("course_id")
        course = Course.objects.get(id=course_id)
        enrollment, _ = Enrollment.objects.get_or_create(
            learner=request.user,
            course=course,
            defaults={"status": Enrollment.Status.ACTIVE}
        )
        return enrollment
