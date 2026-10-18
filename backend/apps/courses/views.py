from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from apps.courses.models import Category, Course, Enrollment, Lesson, Module
from apps.courses.serializers import (
    CategorySerializer,
    CourseCreateUpdateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    EnrollmentSerializer,
    LessonSerializer,
    ModuleSerializer,
)
from apps.users.permissions import IsAdminUserOnly, IsCourseOwnerOrAdmin, IsInstructorOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminUserOnly()]


class CourseViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ["list", "retrieve", "syllabus"]:
            return [permissions.AllowAny()]
        if self.action == "enroll":
            return [permissions.IsAuthenticated()]
        return [IsInstructorOrReadOnly(), IsCourseOwnerOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.select_related("instructor", "category").prefetch_related(
            "modules__lessons"
        )

        # For mutating actions, let the full queryset be evaluated so IsCourseOwnerOrAdmin raises 403 Forbidden
        if self.action in ["update", "partial_update", "destroy", "publish", "archive"]:
            return queryset

        # Instructors can request their own drafts via query param `my_courses=true`
        if user.is_authenticated and self.request.query_params.get("my_courses") == "true":
            return queryset.filter(instructor=user)

        # Public users and standard learners only see PUBLISHED courses
        if not user.is_authenticated or user.role == "LEARNER":
            queryset = queryset.filter(status=Course.Status.PUBLISHED)
        elif user.role in ["INSTRUCTOR", "MODERATOR"]:
            # Instructors see published courses + their own drafts
            queryset = queryset.filter(Q(status=Course.Status.PUBLISHED) | Q(instructor=user))

        # Filtering parameters (FR-CRS-01)
        category_slug = self.request.query_params.get("category")
        difficulty = self.request.query_params.get("difficulty")
        search = self.request.query_params.get("search")

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )

        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        if self.action in ["retrieve", "syllabus"]:
            return CourseDetailSerializer
        return CourseListSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsCourseOwnerOrAdmin])
    def publish(self, request, slug=None):
        """
        FR-CRS-06: Transition course from DRAFT to PUBLISHED with structural validation.
        """
        course = self.get_object()
        try:
            course.publish()
            return Response(
                {"message": f"Course '{course.title}' has been successfully published.", "status": course.status},
                status=status.HTTP_200_OK,
            )
        except DjangoValidationError as e:
            raise DRFValidationError({"detail": e.messages if hasattr(e, "messages") else str(e)})

    @action(detail=True, methods=["post"], permission_classes=[IsCourseOwnerOrAdmin])
    def archive(self, request, slug=None):
        course = self.get_object()
        course.archive()
        return Response(
            {"message": f"Course '{course.title}' has been archived.", "status": course.status},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def syllabus(self, request, slug=None):
        """
        FR-CRS-02: Public course hierarchical outline detailing modules and lessons.
        """
        course = self.get_object()
        serializer = CourseDetailSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, slug=None):
        """
        FR-CRS-03: Idempotent course enrollment.
        """
        course = self.get_object()
        if course.status != Course.Status.PUBLISHED:
            return Response(
                {"detail": "Cannot enroll in an unpublished course."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        enrollment, created = Enrollment.objects.get_or_create(
            learner=request.user,
            course=course,
            defaults={"status": Enrollment.Status.ACTIVE},
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                "message": "Successfully enrolled in course." if created else "Already enrolled.",
                "enrollment_id": str(enrollment.id),
                "status": enrollment.status,
            },
            status=status_code,
        )


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsInstructorOrReadOnly, IsCourseOwnerOrAdmin]

    def get_queryset(self):
        course_id = self.request.query_params.get("course_id")
        if course_id:
            return self.queryset.filter(course_id=course_id)
        return self.queryset


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsInstructorOrReadOnly, IsCourseOwnerOrAdmin]

    def get_queryset(self):
        module_id = self.request.query_params.get("module_id")
        if module_id:
            return self.queryset.filter(module_id=module_id)
        return self.queryset


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(learner=self.request.user).select_related("course__instructor")
