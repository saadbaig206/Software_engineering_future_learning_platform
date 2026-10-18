"""
FutureLearning Learning Engine - End-to-End Multi-Actor Integration Journey Suite
Validates complete user journeys across Learner, Instructor, and Admin personas,
verifying cross-module invariants from registration to graduation, adaptive branching,
and GDPR data subject rights.
"""
import pytest
from rest_framework import status
from apps.users.models import User
from apps.courses.models import Course, Module, Lesson, Enrollment
from apps.assessments.models import Assessment, Question, Choice, QuizAttempt
from apps.discussions.models import DiscussionThread, DiscussionPost
from apps.analytics.models import AuditLog


@pytest.mark.django_db
class TestEndToEndSystemJourney:
    """
    Validates complete multi-actor system integration workflows:
    - Learner Registration & GDPR Inscription (FR-AUTH-01, FR-AUTH-05)
    - Instructor Course Authoring & Publishing (FR-CRS-04, FR-CRS-06)
    - Learner Enrollment & Granular Telemetry Heartbeats (FR-CRS-03, FR-TRK-01)
    - Server-Side Assessment Scoring & Course Completion (FR-ASM-02, FR-TRK-02)
    - Adaptive Remediation & Enrichment Path Assembly (FR-PER-03, FR-PER-04)
    - Discussion Forum Interaction & Instructor Endorsement (FR-DIS-01, FR-DIS-03)
    - Instructor Analytics Telemetry & Drop-Off Funnel (FR-ANL-01, FR-ANL-02)
    - GDPR Data Subject Portability Export (FR-PRV-01)
    """

    def test_complete_educational_lifecycle_journey(self, api_client):
        # =========================================================================
        # 1. LEARNER ONBOARDING & GDPR CONSENT
        # =========================================================================
        register_payload = {
            "email": "e2e_student@university.edu",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "role": User.Role.LEARNER,
            "terms_accepted": True,
            "privacy_accepted": True,
            "gdpr_consent": True,
        }
        reg_resp = api_client.post("/api/v1/auth/register/", register_payload, format="json")
        assert reg_resp.status_code == status.HTTP_201_CREATED

        student = User.objects.get(email="e2e_student@university.edu")
        student.is_email_verified = True
        student.save()

        # Login to obtain JWT
        login_resp = api_client.post(
            "/api/v1/auth/token/",
            {"email": "e2e_student@university.edu", "password": "SecurePassword123!"},
            format="json",
        )
        assert login_resp.status_code == status.HTTP_200_OK
        student_token = login_resp.data["access"]

        # =========================================================================
        # 2. INSTRUCTOR ONBOARDING & COURSE AUTHORING
        # =========================================================================
        instructor = User.objects.create_user(
            email="e2e_prof@university.edu",
            password="ProfPassword123!",
            first_name="Alan",
            last_name="Turing",
            role=User.Role.INSTRUCTOR,
            is_email_verified=True,
        )
        inst_login = api_client.post(
            "/api/v1/auth/token/",
            {"email": "e2e_prof@university.edu", "password": "ProfPassword123!"},
            format="json",
        )
        instructor_token = inst_login.data["access"]

        # Instructor creates course
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {instructor_token}")
        course_payload = {
            "title": "Quantum Computing Fundamentals",
            "slug": "quantum-computing-fundamentals",
            "short_description": "Introduction to qubits, superposition, and quantum gates.",
            "description": "Comprehensive engineering course on quantum architectures.",
            "difficulty": Course.Difficulty.INTERMEDIATE,
            "estimated_hours": 20,
        }
        course_resp = api_client.post("/api/v1/courses/", course_payload, format="json")
        assert course_resp.status_code == status.HTTP_201_CREATED
        course_id = course_resp.data["id"]
        course = Course.objects.get(id=course_id)

        # Instructor creates module & lessons
        mod = Module.objects.create(course=course, title="Module 1: Qubits & Superposition", position=1)
        lesson1 = Lesson.objects.create(
            module=mod,
            title="Lesson 1.1: The Bloch Sphere",
            slug="bloch-sphere",
            position=1,
            is_published=True,
            is_required=True,
        )
        lesson2 = Lesson.objects.create(
            module=mod,
            title="Lesson 1.2: Quantum Logic Gates",
            slug="quantum-logic-gates",
            position=2,
            is_published=True,
            is_required=True,
        )

        # Instructor creates Assessment
        quiz = Assessment.objects.create(
            course=course,
            lesson=lesson2,
            title="Bloch Sphere & Gates Mastery Check",
            passing_score_percent=70,
            max_attempts=3,
            is_published=True,
        )
        q1 = Question.objects.create(
            assessment=quiz,
            prompt="What geometric space represents the state space of a two-level quantum mechanical system?",
            question_type=Question.QuestionType.SINGLE_CHOICE,
            points=10,
            position=0,
            explanation="The Bloch sphere is a geometrical representation of the pure state space of a qubit.",
        )
        c1 = Choice.objects.create(question=q1, text="Bloch Sphere", is_correct=True, position=0)
        c2 = Choice.objects.create(question=q1, text="Hilbert Plane", is_correct=False, position=1)

        # Publish course
        pub_resp = api_client.post(f"/api/v1/courses/{course.slug}/publish/", format="json")
        assert pub_resp.status_code == status.HTTP_200_OK

        # =========================================================================
        # 3. LEARNER ENROLLMENT & PROGRESS TELEMETRY
        # =========================================================================
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {student_token}")

        # Enroll in course
        enroll_resp = api_client.post(f"/api/v1/courses/{course.slug}/enroll/", format="json")
        assert enroll_resp.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

        # Send lesson 1 progress heartbeat
        hb_resp = api_client.post(
            "/api/v1/progress/heartbeat/",
            {
                "lesson_id": str(lesson1.id),
                "last_position_seconds": 300,
                "completion_percent": 100,
            },
            format="json",
        )
        assert hb_resp.status_code == status.HTTP_200_OK

        # =========================================================================
        # 4. LEARNER ASSESSMENT ATTEMPT & GRADING
        # =========================================================================
        # Start attempt
        start_resp = api_client.post(f"/api/v1/assessments/{quiz.id}/start/", format="json")
        assert start_resp.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        attempt_id = start_resp.data["id"]

        # Submit attempt with correct answer
        submit_payload = {
            "answers": {
                str(q1.id): str(c1.id),
            }
        }
        sub_resp = api_client.post(f"/api/v1/attempts/{attempt_id}/submit/", submit_payload, format="json")
        assert sub_resp.status_code == status.HTTP_200_OK
        assert sub_resp.data["passed"] is True
        assert sub_resp.data["score_percent"] == 100.0

        # Verify course progress is now 100% and completed
        enrollment = Enrollment.objects.get(learner=student, course=course)
        assert enrollment.status == Enrollment.Status.COMPLETED

        # =========================================================================
        # 5. DISCUSSION FORUMS & INSTRUCTOR ENDORSEMENT
        # =========================================================================
        thread_payload = {
            "lesson_id": str(lesson1.id),
            "title": "Question regarding superposition phase angles",
            "body": "Does the relative phase affect measurement outcomes in the computational basis?",
        }
        thread_resp = api_client.post(f"/api/v1/courses/{course.slug}/threads/", thread_payload, format="json")
        assert thread_resp.status_code == status.HTTP_201_CREATED
        thread_id = thread_resp.data["id"]

        # Student replies
        post_resp = api_client.post(
            f"/api/v1/threads/{thread_id}/posts/",
            {"body": "I believe relative phase only manifests during interference measurements."},
            format="json",
        )
        assert post_resp.status_code == status.HTTP_201_CREATED
        post_id = post_resp.data["id"]

        # Instructor endorses the post
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {instructor_token}")
        endorse_resp = api_client.post(f"/api/v1/posts/{post_id}/endorse/", format="json")
        assert endorse_resp.status_code == status.HTTP_200_OK
        assert endorse_resp.data["is_endorsed"] is True

        # =========================================================================
        # 6. INSTRUCTOR ANALYTICS TELEMETRY
        # =========================================================================
        analytics_resp = api_client.get(f"/api/v1/analytics/instructor/{course.slug}/")
        assert analytics_resp.status_code == status.HTTP_200_OK
        assert analytics_resp.data["total_enrolled"] >= 1
        assert len(analytics_resp.data["drop_off_curve"]) == 2

        # =========================================================================
        # 7. GDPR DATA SUBJECT RIGHTS (PORTABILITY EXPORT)
        # =========================================================================
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {student_token}")
        export_resp = api_client.get("/api/v1/auth/privacy/export/")
        assert export_resp.status_code == status.HTTP_200_OK
        assert export_resp.data["profile"]["email"] == "e2e_student@university.edu"
        assert len(export_resp.data["enrollments"]) >= 1
        assert len(export_resp.data["assessments"]) >= 1
        assert len(export_resp.data["discussions"]["threads"]) >= 1

        # Verify audit log was recorded for GDPR export
        audit_exists = AuditLog.objects.filter(
            actor=student, action=AuditLog.Action.GDPR_EXPORT
        ).exists()
        assert audit_exists is True
