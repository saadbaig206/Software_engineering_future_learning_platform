import pytest
from django.urls import reverse
from rest_framework import status
from apps.users.models import User
from apps.courses.models import Course, Module, Lesson, Enrollment
from apps.progress.models import LessonProgress
from apps.learning.models import Skill
from apps.assessments.models import (
    Assessment,
    Question,
    Choice,
    QuizAttempt,
)
from apps.assessments.services import (
    AssessmentGraderService,
    AttemptLimitExceededError,
)


@pytest.mark.django_db
class TestAssessmentEngine:

    @pytest.fixture
    def setup_data(self):
        instructor = User.objects.create_user(
            email="prof@example.com",
            password="ProfPassword123!",
            role=User.Role.INSTRUCTOR,
            terms_accepted=True,
            privacy_accepted=True,
        )
        learner = User.objects.create_user(
            email="student@example.com",
            password="StudentPassword123!",
            role=User.Role.LEARNER,
            terms_accepted=True,
            privacy_accepted=True,
        )
        course = Course.objects.create(
            instructor=instructor,
            title="Distributed Systems",
            slug="distributed-systems",
            status=Course.Status.PUBLISHED,
        )
        module = Module.objects.create(course=course, title="Module 1", position=1)
        lesson = Lesson.objects.create(
            module=module,
            title="Raft Consensus",
            slug="raft-consensus",
            position=1,
            is_published=True,
        )
        Enrollment.objects.create(learner=learner, course=course, status=Enrollment.Status.ACTIVE)

        skill = Skill.objects.create(name="Consensus", slug="consensus")

        assessment = Assessment.objects.create(
            course=course,
            lesson=lesson,
            title="Raft Checkpoint",
            passing_score_percent=70,
            max_attempts=2,
            is_published=True,
        )

        # Single choice
        q1 = Question.objects.create(
            assessment=assessment,
            question_type=Question.QuestionType.SINGLE_CHOICE,
            prompt="Who leads the Raft cluster?",
            points=2,
            position=0,
            explanation="The leader accepts log entries and coordinates replication.",
            target_skill=skill,
        )
        c1_1 = Choice.objects.create(question=q1, text="Leader", is_correct=True, position=0)
        c1_2 = Choice.objects.create(question=q1, text="Follower", is_correct=False, position=1)

        # Multiple choice checkbox
        q2 = Question.objects.create(
            assessment=assessment,
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            prompt="Which of the following are valid Raft node states?",
            points=2,
            position=1,
            explanation="Raft nodes exist in Follower, Candidate, or Leader states.",
            target_skill=skill,
        )
        c2_1 = Choice.objects.create(question=q2, text="Leader", is_correct=True, position=0)
        c2_2 = Choice.objects.create(question=q2, text="Candidate", is_correct=True, position=1)
        c2_3 = Choice.objects.create(question=q2, text="Follower", is_correct=True, position=2)
        c2_4 = Choice.objects.create(question=q2, text="Arbitrator", is_correct=False, position=3)

        # Short answer
        q3 = Question.objects.create(
            assessment=assessment,
            question_type=Question.QuestionType.SHORT_ANSWER,
            prompt="What is the unit of consensus in Raft?",
            points=1,
            position=2,
            explanation="A log entry is the discrete unit of replication.",
        )
        Choice.objects.create(question=q3, text="log entry", is_correct=True, position=0)

        return {
            "instructor": instructor,
            "learner": learner,
            "course": course,
            "lesson": lesson,
            "assessment": assessment,
            "q1": q1,
            "c1_1": c1_1,
            "c1_2": c1_2,
            "q2": q2,
            "c2_1": c2_1,
            "c2_2": c2_2,
            "c2_3": c2_3,
            "c2_4": c2_4,
            "q3": q3,
            "skill": skill,
        }

    def test_assessment_detail_conceals_answer_keys_for_learner(self, api_client, setup_data):
        """FR-ASM-02: Learner API view omits is_correct and explanation prior to submission."""
        learner = setup_data["learner"]
        assessment = setup_data["assessment"]
        api_client.force_authenticate(user=learner)

        url = reverse("assessments:assessment-detail", kwargs={"id": assessment.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["title"] == "Raft Checkpoint"
        assert len(data["questions"]) == 3

        for q in data["questions"]:
            assert "explanation" not in q  # Concealed
            for c in q["choices"]:
                assert "is_correct" not in c  # Concealed

    def test_start_attempt_and_attempt_limit_enforcement(self, setup_data):
        """FR-ASM-03: Attempt limit decided by instructor is strictly enforced."""
        learner = setup_data["learner"]
        assessment = setup_data["assessment"]

        # Attempt 1
        att1 = AssessmentGraderService.start_or_resume_attempt(assessment, learner)
        assert att1.attempt_number == 1
        att1.status = QuizAttempt.Status.SUBMITTED
        att1.save()

        # Attempt 2
        att2 = AssessmentGraderService.start_or_resume_attempt(assessment, learner)
        assert att2.attempt_number == 2
        att2.status = QuizAttempt.Status.SUBMITTED
        att2.save()

        # Attempt 3 exceeds max_attempts (2)
        with pytest.raises(AttemptLimitExceededError):
            AssessmentGraderService.start_or_resume_attempt(assessment, learner)

    def test_grading_perfect_score_marks_lesson_completed(self, setup_data):
        """FR-ASM-02 & FR-ASM-04: Perfect score passes assessment and completes linked lesson."""
        learner = setup_data["learner"]
        assessment = setup_data["assessment"]
        q1 = setup_data["q1"]
        c1_1 = setup_data["c1_1"]
        q2 = setup_data["q2"]
        c2_1 = setup_data["c2_1"]
        c2_2 = setup_data["c2_2"]
        c2_3 = setup_data["c2_3"]
        q3 = setup_data["q3"]

        attempt = AssessmentGraderService.start_or_resume_attempt(assessment, learner)

        answers = {
            str(q1.id): str(c1_1.id),
            str(q2.id): [str(c2_1.id), str(c2_2.id), str(c2_3.id)],
            str(q3.id): "Log Entry",
        }

        result = AssessmentGraderService.grade_attempt(attempt, answers)

        assert result["passed"] is True
        assert result["score_percent"] == 100.0
        assert result["points_earned"] == 5.0
        assert result["points_possible"] == 5.0

        # Check immediate pedagogical feedback
        assert len(result["questions"]) == 3
        q1_result = next(q for q in result["questions"] if q["question_id"] == str(q1.id))
        assert q1_result["is_correct"] is True
        assert q1_result["explanation"] == "The leader accepts log entries and coordinates replication."

        # Verify linked lesson progress is marked COMPLETED
        progress = LessonProgress.objects.get(enrollment__learner=learner, lesson=setup_data["lesson"])
        assert progress.status == LessonProgress.Status.COMPLETED
        assert progress.completion_percent == 100

    def test_partial_credit_on_multiple_choice(self, setup_data):
        """FR-ASM-02: Partial credit properly computed on checkbox questions."""
        learner = setup_data["learner"]
        assessment = setup_data["assessment"]
        q1 = setup_data["q1"]
        c1_2 = setup_data["c1_2"]  # Incorrect
        q2 = setup_data["q2"]
        c2_1 = setup_data["c2_1"]  # Correct (1 of 3)
        c2_2 = setup_data["c2_2"]  # Correct (2 of 3)
        q3 = setup_data["q3"]

        attempt = AssessmentGraderService.start_or_resume_attempt(assessment, learner)

        answers = {
            str(q1.id): str(c1_2.id),  # 0 pts
            str(q2.id): [str(c2_1.id), str(c2_2.id)],  # 2 of 3 correct = 2/3 * 2 pts = 1.33 pts
            str(q3.id): "wrong answer",  # 0 pts
        }

        result = AssessmentGraderService.grade_attempt(attempt, answers)

        assert result["passed"] is False  # 1.33 / 5 = 26.6% < 70%
        assert result["points_earned"] == 1.33
        assert result["score_percent"] == 26.6

    def test_api_submit_attempt_endpoint(self, api_client, setup_data):
        """Integration test for POST /api/v1/attempts/{id}/submit/."""
        learner = setup_data["learner"]
        assessment = setup_data["assessment"]
        q1 = setup_data["q1"]
        c1_1 = setup_data["c1_1"]

        api_client.force_authenticate(user=learner)

        attempt = AssessmentGraderService.start_or_resume_attempt(assessment, learner)

        url = reverse("assessments:attempt-submit", kwargs={"attempt_id": attempt.id})
        payload = {
            "answers": {
                str(q1.id): str(c1_1.id),
            }
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempt_id"] == str(attempt.id)
        assert response.data["status"] == QuizAttempt.Status.SUBMITTED
