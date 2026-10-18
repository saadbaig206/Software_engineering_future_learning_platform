import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.courses.models import Category, Course, Enrollment, Lesson, Module
from apps.progress.models import LearningEvent, LessonProgress
from apps.users.models import User


@pytest.fixture
def learner_user(db):
    return User.objects.create_user(
        email="student.test@example.com",
        password="TestPassword123!",
        role=User.Role.LEARNER,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def instructor_user(db):
    return User.objects.create_user(
        email="instructor.test@example.com",
        password="TestPassword123!",
        role=User.Role.INSTRUCTOR,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def sample_course(db, instructor_user):
    cat = Category.objects.create(name="CS", slug="cs-prog")
    course = Course.objects.create(
        title="Software Design",
        slug="software-design-test",
        instructor=instructor_user,
        category=cat,
        status=Course.Status.DRAFT,
    )
    mod1 = Module.objects.create(course=course, title="M1", position=1)
    les1 = Lesson.objects.create(
        module=mod1,
        title="L1 Requirements",
        slug="l1-requirements",
        position=1,
        is_required=True,
        is_published=True,
    )
    les2 = Lesson.objects.create(
        module=mod1,
        title="L2 Architecture",
        slug="l2-architecture",
        position=2,
        is_required=True,
        is_published=True,
    )
    course.publish()
    return course, les1, les2


@pytest.fixture
def auth_client(learner_user):
    client = APIClient()
    client.force_authenticate(user=learner_user)
    return client


@pytest.mark.django_db
class TestProgressTracking:
    def test_heartbeat_creates_progress_and_telemetry(self, auth_client, learner_user, sample_course):
        course, les1, les2 = sample_course
        Enrollment.objects.create(learner=learner_user, course=course)

        url = reverse("progress:heartbeat")
        payload = {
            "lesson_id": str(les1.id),
            "position_seconds": 120,
            "completion_percent": 45,
            "is_completed": False,
        }
        res = auth_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["lesson_status"] == LessonProgress.Status.IN_PROGRESS
        assert res.data["last_position_seconds"] == 120
        assert res.data["lesson_completion_percent"] == 45
        assert res.data["course_completion_percent"] == 0.0

        # Verify DB records
        prog = LessonProgress.objects.get(lesson=les1, enrollment__learner=learner_user)
        assert prog.last_position_seconds == 120
        assert prog.completion_percent == 45
        assert prog.status == LessonProgress.Status.IN_PROGRESS

        # Verify LearningEvent
        event = LearningEvent.objects.filter(user=learner_user, lesson=les1).first()
        assert event is not None
        assert event.event_type == LearningEvent.EventType.MEDIA_HEARTBEAT

    def test_deterministic_course_completion(self, auth_client, learner_user, sample_course):
        course, les1, les2 = sample_course
        enrollment = Enrollment.objects.create(learner=learner_user, course=course)

        url = reverse("progress:heartbeat")

        # Complete lesson 1
        res1 = auth_client.post(
            url,
            {"lesson_id": str(les1.id), "position_seconds": 300, "completion_percent": 100, "is_completed": True},
            format="json",
        )
        assert res1.status_code == status.HTTP_200_OK
        assert res1.data["course_completion_percent"] == 50.0
        assert not res1.data["is_course_completed"]

        # Complete lesson 2 (final required lesson)
        res2 = auth_client.post(
            url,
            {"lesson_id": str(les2.id), "position_seconds": 450, "completion_percent": 95, "is_completed": True},
            format="json",
        )
        assert res2.status_code == status.HTTP_200_OK
        assert res2.data["course_completion_percent"] == 100.0
        assert res2.data["is_course_completed"]

        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.Status.COMPLETED
        assert enrollment.completed_at is not None

    def test_course_progress_detail_view(self, auth_client, learner_user, sample_course):
        course, les1, les2 = sample_course
        Enrollment.objects.create(learner=learner_user, course=course)

        # Send heartbeat for lesson 1
        auth_client.post(
            reverse("progress:heartbeat"),
            {"lesson_id": str(les1.id), "position_seconds": 150, "completion_percent": 60},
            format="json",
        )

        url = reverse("progress:course-progress", kwargs={"slug": course.slug})
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["course_slug"] == course.slug
        assert res.data["total_required_lessons"] == 2
        assert res.data["last_active_lesson"]["lesson_id"] == str(les1.id)
        assert res.data["last_active_lesson"]["last_position_seconds"] == 150

    def test_course_progress_reset(self, auth_client, learner_user, sample_course):
        course, les1, les2 = sample_course
        enrollment = Enrollment.objects.create(learner=learner_user, course=course, status=Enrollment.Status.COMPLETED)
        LessonProgress.objects.create(enrollment=enrollment, lesson=les1, status=LessonProgress.Status.COMPLETED, completion_percent=100)

        url = reverse("progress:course-progress-reset", kwargs={"slug": course.slug})
        
        # Test missing confirm
        res_fail = auth_client.post(url, {}, format="json")
        assert res_fail.status_code == status.HTTP_400_BAD_REQUEST

        # Test valid reset
        res_ok = auth_client.post(url, {"confirm": True}, format="json")
        assert res_ok.status_code == status.HTTP_200_OK

        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.Status.ACTIVE
        assert enrollment.completed_at is None

        prog = LessonProgress.objects.get(enrollment=enrollment, lesson=les1)
        assert prog.status == LessonProgress.Status.NOT_STARTED
        assert prog.completion_percent == 0
