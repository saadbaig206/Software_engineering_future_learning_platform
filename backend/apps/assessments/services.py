import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.assessments.models import (
    Assessment,
    Question,
    Choice,
    QuizAttempt,
    QuestionResponse,
)
from apps.progress.models import LessonProgress, LearningEvent

logger = logging.getLogger("futurelearning.assessments")


class AttemptLimitExceededError(Exception):
    """Raised when a student exceeds the maximum allowed attempts configured by instructor."""
    pass


class AssessmentGraderService:
    """
    Secure server-side grading engine.
    Conceals answers, validates attempts, scores multi-format questions,
    and bridges scores into the adaptive skill engine.
    Fulfills FR-ASM-02, FR-ASM-03, FR-ASM-04, FR-ASM-05, and D-004.
    """

    @staticmethod
    def start_or_resume_attempt(assessment: Assessment, learner) -> QuizAttempt:
        """
        Idempotently starts a new quiz attempt or resumes an active in-progress one.
        Enforces instructor-configured max_attempts limit.
        """
        # 1. Check for active in-progress attempt
        active_attempt = QuizAttempt.objects.filter(
            assessment=assessment,
            learner=learner,
            status=QuizAttempt.Status.IN_PROGRESS,
        ).first()

        if active_attempt:
            # Check if time limit has already expired
            if assessment.time_limit_minutes > 0:
                elapsed = (timezone.now() - active_attempt.started_at).total_seconds()
                allowed = assessment.time_limit_minutes * 60 + 30  # 30s network grace period
                if elapsed > allowed:
                    # Auto-close expired attempt
                    active_attempt.status = QuizAttempt.Status.TIMED_OUT
                    active_attempt.submitted_at = timezone.now()
                    active_attempt.save(update_fields=["status", "submitted_at"])
                else:
                    return active_attempt
            else:
                return active_attempt

        # 2. Count existing completed/submitted attempts
        existing_count = QuizAttempt.objects.filter(
            assessment=assessment, learner=learner
        ).count()

        if existing_count >= assessment.max_attempts:
            raise AttemptLimitExceededError(
                f"Maximum attempt limit reached ({assessment.max_attempts} attempts allowed)."
            )

        # 3. Create fresh attempt
        attempt = QuizAttempt.objects.create(
            assessment=assessment,
            learner=learner,
            attempt_number=existing_count + 1,
            status=QuizAttempt.Status.IN_PROGRESS,
        )

        LearningEvent.objects.create(
            user=learner,
            lesson=assessment.lesson,
            event_type=LearningEvent.EventType.QUIZ_SUBMIT,
            payload={
                "action": "ATTEMPT_STARTED",
                "assessment_id": str(assessment.id),
                "attempt_id": str(attempt.id),
                "attempt_number": attempt.attempt_number,
            },
        )

        return attempt

    @classmethod
    @transaction.atomic
    def grade_attempt(
        cls, attempt: QuizAttempt, answers: dict
    ) -> dict:
        """
        Grades submitted answers server-side.
        `answers` format: { "<question_id>": [choice_id_1, ...] or "text answer" }
        """
        if attempt.status == QuizAttempt.Status.SUBMITTED:
            return cls._build_grade_summary(attempt)

        assessment = attempt.assessment
        now = timezone.now()

        # Check time limit
        is_timed_out = False
        if assessment.time_limit_minutes > 0:
            elapsed = (now - attempt.started_at).total_seconds()
            allowed = assessment.time_limit_minutes * 60 + 30
            if elapsed > allowed:
                is_timed_out = True

        total_points_earned = 0.0
        total_points_possible = 0.0
        skill_calibrations = []

        questions = assessment.questions.prefetch_related("choices").all()

        for question in questions:
            q_id_str = str(question.id)
            user_answer = answers.get(q_id_str)
            points_possible = float(question.points)
            total_points_possible += points_possible

            awarded_points = 0.0
            is_correct = False
            feedback = question.explanation
            selected_choice_objs = []
            text_response = ""

            if question.question_type in [
                Question.QuestionType.SINGLE_CHOICE,
                Question.QuestionType.TRUE_FALSE,
            ]:
                # Single choice: user_answer expected as string choice_id or 1-element list
                selected_id = user_answer[0] if isinstance(user_answer, list) and user_answer else user_answer
                if selected_id:
                    choice = question.choices.filter(id=selected_id).first()
                    if choice:
                        selected_choice_objs.append(choice)
                        if choice.is_correct:
                            awarded_points = points_possible
                            is_correct = True
                        if choice.feedback:
                            feedback = choice.feedback

            elif question.question_type == Question.QuestionType.MULTIPLE_CHOICE:
                # Multiple choice checkbox: user_answer expected as list of choice_ids
                selected_ids = user_answer if isinstance(user_answer, list) else ([user_answer] if user_answer else [])
                selected_choices = list(question.choices.filter(id__in=selected_ids))
                selected_choice_objs.extend(selected_choices)

                correct_choices = list(question.choices.filter(is_correct=True))
                correct_ids = {str(c.id) for c in correct_choices}
                user_selected_ids = {str(c.id) for c in selected_choices}

                if correct_ids and user_selected_ids == correct_ids:
                    awarded_points = points_possible
                    is_correct = True
                elif correct_ids:
                    # Partial credit scoring: (correct_selected - incorrect_selected) / total_correct
                    correct_hits = len(user_selected_ids.intersection(correct_ids))
                    incorrect_hits = len(user_selected_ids.difference(correct_ids))
                    score_ratio = max(0.0, (correct_hits - incorrect_hits) / len(correct_ids))
                    awarded_points = round(score_ratio * points_possible, 2)
                    is_correct = awarded_points >= points_possible

            elif question.question_type == Question.QuestionType.SHORT_ANSWER:
                text_response = str(user_answer or "").strip()
                # Check against acceptable choices
                acceptable_texts = [
                    c.text.strip().lower()
                    for c in question.choices.filter(is_correct=True)
                ]
                if text_response.lower() in acceptable_texts:
                    awarded_points = points_possible
                    is_correct = True
                else:
                    awarded_points = 0.0

            elif question.question_type == Question.QuestionType.CODE_SNIPPET:
                text_response = str(user_answer or "").strip()
                # Compare against model answer or expected keywords
                acceptable_choices = question.choices.filter(is_correct=True)
                if acceptable_choices.exists():
                    matched = any(
                        c.text.strip().lower() in text_response.lower()
                        for c in acceptable_choices
                    )
                    if matched:
                        awarded_points = points_possible
                        is_correct = True
                elif len(text_response) > 5:
                    # Baseline submission credit
                    awarded_points = points_possible
                    is_correct = True

            total_points_earned += awarded_points

            # Record QuestionResponse
            resp, _ = QuestionResponse.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "text_response": text_response,
                    "is_correct": is_correct,
                    "awarded_points": awarded_points,
                    "feedback": feedback,
                },
            )
            if selected_choice_objs:
                resp.selected_choices.set(selected_choice_objs)

            # Record skill calibration event if mapped to KST Skill DAG
            if question.target_skill:
                skill_calibrations.append({
                    "skill": question.target_skill,
                    "score": 100 if is_correct else (awarded_points / points_possible * 100 if points_possible else 0),
                    "weight": question.discrimination_weight,
                })

        score_percent = (
            round((total_points_earned / total_points_possible) * 100, 1)
            if total_points_possible > 0
            else 100.0
        )
        passed = score_percent >= assessment.passing_score_percent

        attempt.status = (
            QuizAttempt.Status.TIMED_OUT
            if is_timed_out
            else QuizAttempt.Status.SUBMITTED
        )
        attempt.submitted_at = now
        attempt.score_percent = score_percent
        attempt.points_earned = total_points_earned
        attempt.points_possible = total_points_possible
        attempt.passed = passed
        attempt.answers_payload = answers
        attempt.save()

        # Update high-water mark for lesson progress if linked
        if assessment.lesson:
            from apps.courses.models import Enrollment
            enrollment = Enrollment.objects.filter(
                learner=attempt.learner, course=assessment.course
            ).first()
            if enrollment:
                progress, _ = LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=assessment.lesson,
                    defaults={"status": LessonProgress.Status.IN_PROGRESS},
                )
                if passed:
                    progress.status = LessonProgress.Status.COMPLETED
                    progress.completion_percent = 100
                    progress.completed_at = now
                    progress.save()
                    enrollment.calculate_progress()

        # Emit telemetry event
        LearningEvent.objects.create(
            user=attempt.learner,
            lesson=assessment.lesson,
            event_type=LearningEvent.EventType.QUIZ_SUBMIT,
            payload={
                "assessment_id": str(assessment.id),
                "attempt_id": str(attempt.id),
                "score_percent": score_percent,
                "passed": passed,
                "attempt_number": attempt.attempt_number,
            },
        )

        # Trigger adaptive engine skill updates asynchronously / synchronously
        for cal in skill_calibrations:
            try:
                from apps.learning.engine import get_adaptive_strategy
                strategy = get_adaptive_strategy()
                strategy.update_mastery(
                    learner=attempt.learner,
                    skill=cal["skill"],
                    assessment_score=cal["score"],
                )
            except Exception as e:
                logger.warning("Adaptive skill mastery calibration failed: %s", e)

        return cls._build_grade_summary(attempt)

    @staticmethod
    def _build_grade_summary(attempt: QuizAttempt) -> dict:
        assessment = attempt.assessment
        responses = attempt.responses.select_related("question").prefetch_related("selected_choices").all()

        details = []
        for r in responses:
            q = r.question
            details.append({
                "question_id": str(q.id),
                "prompt": q.prompt,
                "question_type": q.question_type,
                "points_possible": q.points,
                "awarded_points": r.awarded_points,
                "is_correct": r.is_correct,
                "explanation": q.explanation,
                "feedback": r.feedback,
                "selected_choices": [str(c.id) for c in r.selected_choices.all()],
                "text_response": r.text_response,
                "correct_choices": [
                    {"id": str(c.id), "text": c.text}
                    for c in q.choices.filter(is_correct=True)
                ],
            })

        return {
            "attempt_id": str(attempt.id),
            "assessment_id": str(assessment.id),
            "assessment_title": assessment.title,
            "attempt_number": attempt.attempt_number,
            "max_attempts": assessment.max_attempts,
            "attempts_remaining": max(0, assessment.max_attempts - attempt.attempt_number),
            "status": attempt.status,
            "score_percent": attempt.score_percent,
            "points_earned": attempt.points_earned,
            "points_possible": attempt.points_possible,
            "passing_score_percent": assessment.passing_score_percent,
            "passed": attempt.passed,
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            "questions": details,
        }
