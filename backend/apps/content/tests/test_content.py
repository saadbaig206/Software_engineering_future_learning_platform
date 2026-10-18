import os
import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.content.models import ContentBlock, MediaAsset
from apps.content.services.storage import StorageService
from apps.content.tasks import process_media_asset
from apps.courses.models import Course, Lesson, Module
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def instructor(db):
    return User.objects.create_user(
        email="instructor.media@futurelearning.test",
        password="ValidPassword123!",
        role=User.Role.INSTRUCTOR,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def learner(db):
    return User.objects.create_user(
        email="learner.media@futurelearning.test",
        password="ValidPassword123!",
        role=User.Role.LEARNER,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def course_and_lesson(db, instructor):
    course = Course.objects.create(
        instructor=instructor,
        title="Multimedia Course",
        description="Course with rich media.",
        status=Course.Status.DRAFT,
    )
    mod = Module.objects.create(course=course, title="Module 1", position=1)
    lesson = Lesson.objects.create(module=mod, title="Lesson 1", position=1)
    return course, lesson


@pytest.mark.django_db
class TestMediaPipelineAndContentBlocks:
    """
    Test suite for Module 3 requirements (FR-MED-01, FR-MED-02, FR-MED-03)
    and Content Block authoring (FR-CRS-05).
    """

    def test_presigned_upload_url_generation_success(self, api_client, instructor, course_and_lesson):
        """FR-MED-01: Instructors can request presigned upload tickets; validates file size and MIME."""
        _, lesson = course_and_lesson
        api_client.force_authenticate(user=instructor)
        url = reverse("media-upload-url-lesson", kwargs={"lesson_id": lesson.id})
        payload = {
            "filename": "lecture1_intro.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 52428800,  # 50 MB
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "upload_url" in response.data
        assert "storage_key" in response.data
        assert response.data["storage_key"].endswith(".mp4")

    def test_presigned_upload_rejects_exceeded_size(self, api_client, instructor, course_and_lesson):
        """FR-MED-01: Rejects file sizes exceeding 1 GB limit."""
        _, lesson = course_and_lesson
        api_client.force_authenticate(user=instructor)
        url = reverse("media-upload-url-lesson", kwargs={"lesson_id": lesson.id})
        payload = {
            "filename": "huge_file.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 2 * 1024 * 1024 * 1024,  # 2 GB
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_learner_cannot_request_presigned_upload(self, api_client, learner, course_and_lesson):
        """FR-AUTH-02: Learners cannot generate upload tickets."""
        _, lesson = course_and_lesson
        api_client.force_authenticate(user=learner)
        url = reverse("media-upload-url-lesson", kwargs={"lesson_id": lesson.id})
        response = api_client.post(url, {"filename": "video.mp4", "mime_type": "video/mp4", "size_bytes": 1024}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_media_confirm_dispatches_processing_task(self, api_client, instructor):
        """FR-MED-02: Upload confirmation creates MediaAsset and triggers async validation."""
        api_client.force_authenticate(user=instructor)
        url = reverse("media-confirm")
        payload = {
            "storage_key": "media/test/lecture1.mp4",
            "original_filename": "lecture1.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 10485760,  # 10 MB
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["status"] in ["PROCESSING", "READY"]
        asset_id = response.data["media_asset_id"]

        asset = MediaAsset.objects.get(id=asset_id)
        assert asset.original_filename == "lecture1.mp4"
        assert asset.uploaded_by == instructor

    def test_magic_byte_validation_logic(self):
        """FR-MED-02: Unit check for magic byte signatures."""
        assert StorageService.validate_magic_bytes(b"\x89PNG\r\n\x1a\n\x00\x00", "image/png") is True
        assert StorageService.validate_magic_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF", "image/jpeg") is True
        assert StorageService.validate_magic_bytes(b"%PDF-1.4\n%...", "application/pdf") is True
        # Mismatch
        assert StorageService.validate_magic_bytes(b"MALICIOUS_EXEC", "image/png") is False

    def test_content_block_creation_polymorphic(self, api_client, instructor, course_and_lesson):
        """FR-CRS-05: Multi-type content block creation (TEXT, VIDEO, SIMULATION)."""
        _, lesson = course_and_lesson
        api_client.force_authenticate(user=instructor)

        # 1. Text block
        text_url = reverse("content-block-list")
        text_res = api_client.post(
            text_url,
            {
                "lesson": str(lesson.id),
                "block_type": "TEXT",
                "title": "Welcome Text",
                "position": 1,
                "content_payload": {"markdown": "# Welcome\nThis is a lecture."},
            },
            format="json",
        )
        assert text_res.status_code == status.HTTP_201_CREATED

        # 2. Simulation block
        sim_res = api_client.post(
            text_url,
            {
                "lesson": str(lesson.id),
                "block_type": "SIMULATION",
                "title": "Circuit Simulation",
                "position": 2,
                "content_payload": {
                    "sim_url": "https://simulations.futurelearning.test/circuits",
                    "sandbox_flags": "allow-scripts",
                },
            },
            format="json",
        )
        assert sim_res.status_code == status.HTTP_201_CREATED

        blocks = ContentBlock.objects.filter(lesson=lesson)
        assert blocks.count() == 2
