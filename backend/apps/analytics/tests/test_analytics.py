import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from apps.users.models import User
from apps.courses.models import Course, Module, Lesson, Enrollment
from apps.analytics.models import AuditLog, DailyActiveUserMetric
from apps.analytics.tasks import rollup_daily_analytics_task
from apps.progress.models import LessonProgress, LearningEvent


@pytest.fixture
def test_setup(db):
    # Create users
    admin = User.objects.create_superuser(
        email="admin_analytics@test.com", password="Password123!", role=User.Role.ADMIN
    )
    instructor = User.objects.create_user(
        email="instructor_analytics@test.com", password="Password123!", role=User.Role.INSTRUCTOR
    )
    other_instructor = User.objects.create_user(
        email="other_instructor@test.com", password="Password123!", role=User.Role.INSTRUCTOR
    )
    learner = User.objects.create_user(
        email="learner_analytics@test.com", password="Password123!", role=User.Role.LEARNER
    )

    # Create Course, Module, Lesson
    course = Course.objects.create(
        title="Distributed Algorithms",
        slug="distributed-algorithms-101",
        instructor=instructor,
        status=Course.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    mod = Module.objects.create(course=course, title="Module 1: Consensus", position=1)
    l1 = Lesson.objects.create(module=mod, title="Paxos Basics", slug="paxos-basics", position=1, is_published=True)
    l2 = Lesson.objects.create(module=mod, title="Raft Protocol", slug="raft-protocol", position=2, is_published=True)

    # Enroll learner
    enrollment = Enrollment.objects.create(learner=learner, course=course, status=Enrollment.Status.ACTIVE)
    lp1 = LessonProgress.objects.create(
        enrollment=enrollment, lesson=l1, status=LessonProgress.Status.COMPLETED, completion_percent=100
    )

    # Telemetry
    LearningEvent.objects.create(
        user=learner,
        enrollment=enrollment,
        lesson=l1,
        event_type=LearningEvent.EventType.MEDIA_HEARTBEAT,
        payload={"pos": 120, "pct": 100},
    )

    return {
        "admin": admin,
        "instructor": instructor,
        "other_instructor": other_instructor,
        "learner": learner,
        "course": course,
        "enrollment": enrollment,
        "l1": l1,
        "l2": l2,
    }


@pytest.mark.django_db
class TestAnalyticsEngine:
    def test_instructor_course_analytics_access_and_funnel(self, api_client, test_setup):
        course = test_setup["course"]
        instructor = test_setup["instructor"]
        other_instructor = test_setup["other_instructor"]
        learner = test_setup["learner"]

        # 1. Instructor who owns the course can view analytics
        api_client.force_authenticate(user=instructor)
        resp = api_client.get(f"/api/v1/analytics/instructor/{course.slug}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["course_slug"] == course.slug
        assert data["total_enrolled"] == 1
        assert len(data["drop_off_curve"]) == 2
        assert data["drop_off_curve"][0]["completed_count"] == 1

        # 2. Other instructor is forbidden
        api_client.force_authenticate(user=other_instructor)
        resp2 = api_client.get(f"/api/v1/analytics/instructor/{course.slug}/")
        assert resp2.status_code == status.HTTP_403_FORBIDDEN

        # 3. Learner is forbidden
        api_client.force_authenticate(user=learner)
        resp3 = api_client.get(f"/api/v1/analytics/instructor/{course.slug}/")
        assert resp3.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_platform_overview_and_audit_trail(self, api_client, test_setup):
        admin = test_setup["admin"]
        learner = test_setup["learner"]

        # 1. Non-admin is forbidden
        api_client.force_authenticate(user=learner)
        resp_denied = api_client.get("/api/v1/analytics/admin/overview/")
        assert resp_denied.status_code == status.HTTP_403_FORBIDDEN

        # 2. Admin can access overview
        api_client.force_authenticate(user=admin)
        resp = api_client.get("/api/v1/analytics/admin/overview/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["total_users"] >= 4
        assert data["published_courses"] >= 1
        assert "recent_audit_logs" in data

    def test_learner_engagement_summary(self, api_client, test_setup):
        learner = test_setup["learner"]
        api_client.force_authenticate(user=learner)

        resp = api_client.get("/api/v1/analytics/learner/engagement/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["total_enrolled_courses"] == 1
        assert data["completed_lessons_count"] == 1
        assert data["total_learning_minutes"] >= 0.1

    def test_gdpr_data_export_flow(self, api_client, test_setup):
        learner = test_setup["learner"]
        api_client.force_authenticate(user=learner)

        resp = api_client.get("/api/v1/auth/privacy/export/")
        assert resp.status_code == status.HTTP_200_OK
        assert "attachment" in resp.headers.get("Content-Disposition", "")
        data = resp.data
        assert data["profile"]["email"] == learner.email
        assert len(data["enrollments"]) == 1
        assert data["enrollments"][0]["course_slug"] == "distributed-algorithms-101"

        # Check audit log recorded
        audit = AuditLog.objects.filter(actor=learner, action=AuditLog.Action.GDPR_EXPORT).first()
        assert audit is not None
        assert audit.target_model == "User"

    def test_gdpr_erasure_requires_password_and_anonymizes_pii(self, api_client, test_setup):
        learner = test_setup["learner"]
        api_client.force_authenticate(user=learner)

        # 1. Wrong password rejected
        resp_bad = api_client.post("/api/v1/auth/privacy/erase/", {"password": "WrongPassword!", "confirm": True})
        assert resp_bad.status_code == status.HTTP_400_BAD_REQUEST

        # 2. Missing confirm rejected
        resp_no_confirm = api_client.post("/api/v1/auth/privacy/erase/", {"password": "Password123!", "confirm": False})
        assert resp_no_confirm.status_code == status.HTTP_400_BAD_REQUEST

        # 3. Successful erasure
        resp_ok = api_client.post("/api/v1/auth/privacy/erase/", {"password": "Password123!", "confirm": True})
        assert resp_ok.status_code == status.HTTP_200_OK
        assert resp_ok.data["status"] == "ANONYMIZED"

        # Inspect refreshed user in database
        learner.refresh_from_db()
        assert learner.email.startswith("anonymized_")
        assert learner.first_name == "Anonymized"
        assert learner.is_active is False

        # Verify audit log
        audit = AuditLog.objects.filter(action=AuditLog.Action.GDPR_ERASURE).first()
        assert audit is not None

    def test_daily_analytics_celery_task(self, test_setup):
        result = rollup_daily_analytics_task()
        assert result["status"] == "SUCCESS"
        metric = DailyActiveUserMetric.objects.first()
        assert metric is not None
        assert metric.daily_active_users >= 0
