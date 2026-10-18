import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.courses.models import Category, Course, Enrollment, Lesson, Module
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category(db):
    return Category.objects.create(name="Computer Science", description="Programming and algorithms")


@pytest.fixture
def instructor_a(db):
    return User.objects.create_user(
        email="prof.a@futurelearning.test",
        password="ValidPassword123!",
        role=User.Role.INSTRUCTOR,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def instructor_b(db):
    return User.objects.create_user(
        email="prof.b@futurelearning.test",
        password="ValidPassword123!",
        role=User.Role.INSTRUCTOR,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def learner(db):
    return User.objects.create_user(
        email="student@futurelearning.test",
        password="ValidPassword123!",
        role=User.Role.LEARNER,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def published_course(db, instructor_a, category):
    course = Course.objects.create(
        instructor=instructor_a,
        category=category,
        title="Distributed Systems Engineering",
        description="Deep dive into consensus algorithms and distributed storage.",
        short_description="Learn distributed systems.",
        difficulty=Course.Difficulty.ADVANCED,
        status=Course.Status.DRAFT,
    )
    mod = Module.objects.create(course=course, title="Module 1: Consensus", position=1)
    Lesson.objects.create(
        module=mod,
        title="Lesson 1.1: Raft Overview",
        position=1,
        is_published=True,
        is_preview=True,
    )
    course.publish()
    return course


@pytest.mark.django_db
class TestCourseCatalogAndAuthoring:
    """
    Test suite for Module 2 requirements: FR-CRS-01 through FR-CRS-07.
    """

    def test_public_catalog_filters_only_published(self, api_client, published_course, instructor_a):
        """FR-CRS-01: Public catalog strictly returns published courses; excludes drafts."""
        # Create an unreleased draft course
        Course.objects.create(
            instructor=instructor_a,
            title="Secret Draft Course",
            description="Work in progress.",
            status=Course.Status.DRAFT,
        )

        url = reverse("course-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if "results" in response.data else response.data
        slugs = [c["slug"] for c in results]
        assert published_course.slug in slugs
        assert "secret-draft-course" not in slugs

    def test_public_catalog_search_and_filter(self, api_client, published_course):
        """FR-CRS-01: Filters by keyword, category, and difficulty."""
        url = reverse("course-list")
        # Search match
        res_match = api_client.get(url, {"search": "Distributed"})
        results = res_match.data["results"] if "results" in res_match.data else res_match.data
        assert len(results) >= 1

        # Search mismatch
        res_none = api_client.get(url, {"search": "NonExistentKeywordXYZ"})
        results_none = res_none.data["results"] if "results" in res_none.data else res_none.data
        assert len(results_none) == 0

    def test_syllabus_and_preview_inspection(self, api_client, published_course):
        """FR-CRS-02: Public syllabus endpoint returns module/lesson hierarchy and preview flags."""
        url = reverse("course-syllabus", kwargs={"slug": published_course.slug})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["modules"]) == 1
        lesson = response.data["modules"][0]["lessons"][0]
        assert lesson["is_preview"] is True
        assert lesson["title"] == "Lesson 1.1: Raft Overview"

    def test_instructor_course_creation_and_ownership(self, api_client, instructor_a, instructor_b):
        """FR-CRS-04, FR-AUTH-02: Instructors can create courses; other instructors cannot edit them."""
        api_client.force_authenticate(user=instructor_a)
        url = reverse("course-list")
        create_payload = {
            "title": "Quantum Computing 101",
            "description": "Introduction to qubits and superposition.",
            "difficulty": "BEGINNER",
            "estimated_duration_minutes": 120,
        }
        create_res = api_client.post(url, create_payload, format="json")
        assert create_res.status_code == status.HTTP_201_CREATED
        course_slug = create_res.data["slug"]

        # Instructor B attempts to modify Instructor A's course
        api_client.force_authenticate(user=instructor_b)
        patch_url = reverse("course-detail", kwargs={"slug": course_slug})
        patch_res = api_client.patch(patch_url, {"title": "Hacked Title"}, format="json")
        assert patch_res.status_code == status.HTTP_403_FORBIDDEN

    def test_learner_cannot_create_course(self, api_client, learner):
        """FR-AUTH-02: Learners are forbidden from authoring courses."""
        api_client.force_authenticate(user=learner)
        url = reverse("course-list")
        res = api_client.post(url, {"title": "Unauthorized Course"}, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_course_publish_lifecycle_validation(self, api_client, instructor_a):
        """FR-CRS-06: Publishing is rejected if 0 modules or 0 published lessons; succeeds when complete."""
        api_client.force_authenticate(user=instructor_a)
        course = Course.objects.create(
            instructor=instructor_a,
            title="Empty Course",
            description="No modules yet.",
            status=Course.Status.DRAFT,
        )

        publish_url = reverse("course-publish", kwargs={"slug": course.slug})
        # Attempt publish with 0 modules
        res_fail = api_client.post(publish_url)
        assert res_fail.status_code == status.HTTP_400_BAD_REQUEST

        # Add module with published lesson
        mod = Module.objects.create(course=course, title="Module 1", position=1)
        Lesson.objects.create(module=mod, title="Lesson 1", position=1, is_published=True)

        # Re-attempt publish
        res_ok = api_client.post(publish_url)
        assert res_ok.status_code == status.HTTP_200_OK
        course.refresh_from_db()
        assert course.status == Course.Status.PUBLISHED
        assert course.published_at is not None

    def test_idempotent_course_enrollment(self, api_client, learner, published_course):
        """FR-CRS-03: Authenticated learner can enroll; duplicate enrollments are idempotent."""
        api_client.force_authenticate(user=learner)
        enroll_url = reverse("course-enroll", kwargs={"slug": published_course.slug})

        # First enrollment
        res1 = api_client.post(enroll_url)
        assert res1.status_code == status.HTTP_201_CREATED
        assert Enrollment.objects.filter(learner=learner, course=published_course).count() == 1

        # Second enrollment (idempotent)
        res2 = api_client.post(enroll_url)
        assert res2.status_code == status.HTTP_200_OK
        assert Enrollment.objects.filter(learner=learner, course=published_course).count() == 1
