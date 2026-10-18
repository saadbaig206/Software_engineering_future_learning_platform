import hashlib
import logging
from datetime import datetime, time, timedelta, timezone as dt_timezone
from django.db import models
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from django.core.cache import cache

from apps.analytics.models import AuditLog, CourseAnalyticsSnapshot, DailyActiveUserMetric
from apps.courses.models import Course, Enrollment, Lesson
from apps.progress.models import LearningEvent, LessonProgress
from apps.assessments.models import Assessment, Question, QuizAttempt, QuestionResponse
from apps.discussions.models import DiscussionThread
from apps.users.models import User

logger = logging.getLogger(__name__)


class AnalyticsRollupService:
    """
    Core analytics calculation service for instructors, learners, and administrators.
    """

    @classmethod
    def record_audit_log(
        cls,
        action: str,
        actor: User = None,
        target_model: str = "",
        target_id: str = "",
        changes: dict = None,
        request=None,
    ) -> AuditLog:
        """Helper to create immutable audit trail records with privacy-preserving IP hashes."""
        ip_hash = ""
        if request and hasattr(request, "META"):
            raw_ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
            if raw_ip:
                ip_hash = hashlib.sha256(raw_ip.encode("utf-8")).hexdigest()

        return AuditLog.objects.create(
            actor=actor,
            action=action,
            target_model=target_model,
            target_id=str(target_id),
            ip_hash=ip_hash,
            changes=changes or {},
        )

    @classmethod
    def get_instructor_course_analytics(cls, course: Course) -> dict:
        """
        Calculates live/cached instructor course performance metrics (FR-ANL-02).
        Includes drop-off curve, quiz score distributions, and difficult questions.
        """
        cache_key = f"fl:analytics:crs:{course.id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        enrollments = Enrollment.objects.filter(course=course)
        total_enrolled = enrollments.count()
        completed_count = enrollments.filter(status=Enrollment.Status.COMPLETED).count()
        completion_rate = round((completed_count / total_enrolled * 100), 1) if total_enrolled > 0 else 0.0

        # Active students (had progress or activity in last 14 days)
        cutoff_date = timezone.now() - timedelta(days=14)
        active_count = enrollments.filter(
            lesson_progresses__updated_at__gte=cutoff_date
        ).distinct().count()

        # Quiz & assessment performance across this course
        attempts = QuizAttempt.objects.filter(
            assessment__course=course, status=QuizAttempt.Status.SUBMITTED
        )
        avg_score_data = attempts.aggregate(avg_score=Avg("score_percent"))
        avg_quiz_score = round(avg_score_data["avg_score"] or 0.0, 1)

        # Difficult questions breakdown (bottom 5 by pass rate)
        responses = QuestionResponse.objects.filter(
            attempt__assessment__course=course
        ).values("question_id", "question__prompt").annotate(
            total_answers=Count("id"),
            correct_answers=Count("id", filter=Q(is_correct=True)),
        ).filter(total_answers__gte=1)

        difficult_questions = []
        for r in responses:
            total = r["total_answers"]
            correct = r["correct_answers"]
            pass_rate = round((correct / total * 100), 1) if total > 0 else 0.0
            difficult_questions.append({
                "question_id": str(r["question_id"]),
                "prompt": r["question__prompt"][:80] + "..." if len(r["question__prompt"]) > 80 else r["question__prompt"],
                "total_attempts": total,
                "pass_rate_percent": pass_rate,
            })
        difficult_questions.sort(key=lambda x: x["pass_rate_percent"])
        difficult_questions = difficult_questions[:5]

        # Lesson drop-off funnel
        # Count completed students per lesson in order
        all_lessons = list(
            Lesson.objects.filter(module__course=course, is_published=True)
            .select_related("module")
            .order_by("module__position", "position")
        )
        drop_off_curve = []
        for l in all_lessons:
            lesson_completions = LessonProgress.objects.filter(
                lesson=l, status=LessonProgress.Status.COMPLETED
            ).count()
            pct_of_enrolled = round((lesson_completions / total_enrolled * 100), 1) if total_enrolled > 0 else 0.0
            drop_off_curve.append({
                "lesson_id": str(l.id),
                "title": l.title,
                "module_title": l.module.title,
                "completed_count": lesson_completions,
                "completion_percent_of_enrolled": pct_of_enrolled,
            })

        # Forum activity count
        forum_threads_count = DiscussionThread.objects.filter(course=course).count()

        result = {
            "course_id": str(course.id),
            "course_title": course.title,
            "course_slug": course.slug,
            "total_enrolled": total_enrolled,
            "active_students_14d": active_count,
            "completed_students": completed_count,
            "completion_rate_percent": completion_rate,
            "avg_quiz_score_percent": avg_quiz_score,
            "total_forum_threads": forum_threads_count,
            "difficult_questions": difficult_questions,
            "drop_off_curve": drop_off_curve,
            "last_computed_at": timezone.now().isoformat(),
        }

        # Cache for 10 minutes
        cache.set(cache_key, result, timeout=600)
        return result

    @classmethod
    def get_admin_platform_overview(cls) -> dict:
        """
        Calculates executive platform-wide health, adoption, and growth metrics (FR-ANL-03, FR-ADM-03).
        """
        cache_key = "fl:analytics:admin:overview"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        total_users = User.objects.count()
        users_by_role = dict(
            User.objects.values("role").annotate(c=Count("id")).values_list("role", "c")
        )

        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(status=Course.Status.PUBLISHED).count()
        total_enrollments = Enrollment.objects.count()
        completed_enrollments = Enrollment.objects.filter(status=Enrollment.Status.COMPLETED).count()
        platform_completion_rate = (
            round((completed_enrollments / total_enrollments * 100), 1)
            if total_enrollments > 0
            else 0.0
        )

        # 30-day active users
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users_30d = LearningEvent.objects.filter(
            timestamp__gte=thirty_days_ago
        ).values("user_id").distinct().count()

        # Learning minutes from heartbeats
        total_heartbeats = LearningEvent.objects.filter(
            event_type=LearningEvent.EventType.MEDIA_HEARTBEAT
        ).count()
        estimated_learning_hours = round((total_heartbeats * 10) / 3600, 1)

        # Recent system audit logs (latest 10)
        recent_audit_logs = [
            {
                "id": str(a.id),
                "actor_email": a.actor.email if a.actor else "System",
                "action": a.action,
                "target_model": a.target_model,
                "target_id": a.target_id,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in AuditLog.objects.select_related("actor")[:10]
        ]

        result = {
            "total_users": total_users,
            "users_by_role": users_by_role,
            "active_users_30d": active_users_30d,
            "total_courses": total_courses,
            "published_courses": published_courses,
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "platform_completion_rate": platform_completion_rate,
            "estimated_learning_hours": estimated_learning_hours,
            "recent_audit_logs": recent_audit_logs,
            "last_computed_at": timezone.now().isoformat(),
        }

        # Cache for 5 minutes
        cache.set(cache_key, result, timeout=300)
        return result

    @classmethod
    def get_learner_engagement_summary(cls, user: User) -> dict:
        """
        Calculates personal learning streak, total learning hours, and course mastery (FR-ANL-01).
        """
        enrollments = Enrollment.objects.filter(learner=user).select_related("course")
        total_enrolled = enrollments.count()
        completed_courses = enrollments.filter(status=Enrollment.Status.COMPLETED).count()
        in_progress_courses = enrollments.filter(status=Enrollment.Status.ACTIVE).count()

        # Compute completed lessons
        completed_lessons_count = LessonProgress.objects.filter(
            enrollment__learner=user, status=LessonProgress.Status.COMPLETED
        ).count()

        # Compute learning events & total estimated minutes
        heartbeat_count = LearningEvent.objects.filter(
            user=user, event_type=LearningEvent.EventType.MEDIA_HEARTBEAT
        ).count()
        total_minutes = round((heartbeat_count * 10) / 60, 1)

        # Active streak calculation (consecutive days with learning events)
        event_dates = list(
            LearningEvent.objects.filter(user=user)
            .dates("timestamp", "day", order="DESC")
        )
        streak_days = 0
        if event_dates:
            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            # Check if active today or yesterday
            if event_dates[0] in [today, yesterday]:
                expected = event_dates[0]
                for d in event_dates:
                    if d == expected:
                        streak_days += 1
                        expected = expected - timedelta(days=1)
                    else:
                        break

        # Quiz attempts and passing count
        attempts = QuizAttempt.objects.filter(learner=user)
        total_quizzes = attempts.count()
        passed_quizzes = attempts.filter(passed=True).count()

        return {
            "total_enrolled_courses": total_enrolled,
            "in_progress_courses": in_progress_courses,
            "completed_courses": completed_courses,
            "completed_lessons_count": completed_lessons_count,
            "total_learning_minutes": total_minutes,
            "active_streak_days": streak_days,
            "quiz_attempts_count": total_quizzes,
            "quizzes_passed_count": passed_quizzes,
            "member_since": user.date_joined.isoformat() if user.date_joined else None,
        }

    @classmethod
    def compute_daily_snapshot(cls, target_date=None):
        """
        Celery Beat periodic task helper to snapshot daily metrics.
        """
        target_date = target_date or (timezone.now().date() - timedelta(days=1))
        start_dt = datetime.combine(target_date, time.min, tzinfo=dt_timezone.utc)
        end_dt = start_dt + timedelta(days=1)

        dau_count = LearningEvent.objects.filter(
            timestamp__gte=start_dt, timestamp__lt=end_dt
        ).values("user_id").distinct().count()

        new_regs = User.objects.filter(
            date_joined__gte=start_dt, date_joined__lt=end_dt
        ).count()

        enrollments = Enrollment.objects.filter(
            enrolled_at__gte=start_dt, enrolled_at__lt=end_dt
        ).count()

        completions = Enrollment.objects.filter(
            completed_at__gte=start_dt, completed_at__lt=end_dt
        ).count()

        heartbeats = LearningEvent.objects.filter(
            timestamp__gte=start_dt,
            timestamp__lt=end_dt,
            event_type=LearningEvent.EventType.MEDIA_HEARTBEAT,
        ).count()

        quiz_count = QuizAttempt.objects.filter(
            started_at__gte=start_dt, started_at__lt=end_dt
        ).count()

        metric, _ = DailyActiveUserMetric.objects.update_or_create(
            date=target_date,
            defaults={
                "daily_active_users": dau_count,
                "new_registrations": new_regs,
                "total_enrollments": enrollments,
                "course_completions": completions,
                "total_learning_minutes": int((heartbeats * 10) / 60),
                "quiz_attempts_submitted": quiz_count,
            },
        )
        return metric
