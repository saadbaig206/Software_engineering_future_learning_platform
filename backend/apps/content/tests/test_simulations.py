import pytest
from django.urls import reverse
from rest_framework import status
from apps.users.models import User
from apps.courses.models import Course, Module, Lesson, Enrollment
from apps.content.models import ContentBlock
from apps.progress.models import LessonProgress, LearningEvent


@pytest.mark.django_db
class TestSimulationScoreReport:

    @pytest.fixture
    def setup_sim_data(self):
        instructor = User.objects.create_user(
            email="sim_inst@example.com",
            password="InstPassword123!",
            role=User.Role.INSTRUCTOR,
            terms_accepted=True,
            privacy_accepted=True,
        )
        learner = User.objects.create_user(
            email="sim_learner@example.com",
            password="LearnerPassword123!",
            role=User.Role.LEARNER,
            terms_accepted=True,
            privacy_accepted=True,
        )
        course = Course.objects.create(
            instructor=instructor,
            title="Cloud Infrastructure",
            slug="cloud-infra",
            status=Course.Status.PUBLISHED,
        )
        module = Module.objects.create(course=course, title="Sim Module", position=1)
        lesson = Lesson.objects.create(
            module=module,
            title="Circuit Breaker Lab",
            slug="circuit-breaker-lab",
            position=1,
            is_published=True,
        )
        Enrollment.objects.create(learner=learner, course=course, status=Enrollment.Status.ACTIVE)

        sim_block = ContentBlock.objects.create(
            lesson=lesson,
            block_type=ContentBlock.BlockType.SIMULATION,
            title="Interactive Circuit Breaker",
            position=1,
            content_payload={
                "simulation_id": "sim-cb-99",
                "passing_score": 70,
            },
        )

        return {
            "instructor": instructor,
            "learner": learner,
            "course": course,
            "lesson": lesson,
            "sim_block": sim_block,
        }

    def test_simulation_score_report_success_marks_lesson_completed(self, api_client, setup_sim_data):
        """FR-SIM-01, FR-SIM-02, FR-SIM-03: Ingesting passing simulation score completes lesson."""
        learner = setup_sim_data["learner"]
        sim_block = setup_sim_data["sim_block"]
        lesson = setup_sim_data["lesson"]
        api_client.force_authenticate(user=learner)

        url = reverse("simulation-report")
        payload = {
            "block_id": str(sim_block.id),
            "score_percent": 85.5,
            "completed": True,
            "telemetry": {
                "nodes_tested": 3,
                "tripped_circuits": 1,
                "recovery_time_sec": 4.2,
            },
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is True
        assert response.data["lesson_completed"] is True
        assert response.data["score_percent"] == 85.5

        # Check DB state
        progress = LessonProgress.objects.get(enrollment__learner=learner, lesson=lesson)
        assert progress.status == LessonProgress.Status.COMPLETED
        assert progress.completion_percent == 100

        # Check telemetry event
        event = LearningEvent.objects.filter(user=learner, lesson=lesson).latest("timestamp")
        assert event.payload["action"] == "SIMULATION_SCORE"
        assert event.payload["score_percent"] == 85.5

    def test_simulation_report_requires_enrollment(self, api_client, setup_sim_data):
        """FR-SIM-03: Unenrolled learner cannot submit simulation scores."""
        outsider = User.objects.create_user(
            email="outsider@example.com",
            password="OutsiderPass123!",
            role=User.Role.LEARNER,
            terms_accepted=True,
            privacy_accepted=True,
        )
        sim_block = setup_sim_data["sim_block"]
        api_client.force_authenticate(user=outsider)

        url = reverse("simulation-report")
        payload = {
            "block_id": str(sim_block.id),
            "score_percent": 90,
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
