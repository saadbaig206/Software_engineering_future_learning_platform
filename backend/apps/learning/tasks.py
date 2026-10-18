import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from apps.courses.models import Course, Enrollment
from apps.learning.engine import get_adaptive_engine
from apps.learning.models import LessonSkill, Skill

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    name="apps.learning.tasks.recompute_student_mastery_task",
    queue="adaptive",
    max_retries=3,
    default_retry_delay=10,
)
def recompute_student_mastery_task(learner_id: str, skill_id: str, score_obtained: int, max_score: int = 100):
    """
    Asynchronous Celery task for recomputing student skill mastery and
    refreshing personalized learning paths without blocking HTTP request workers.
    """
    try:
        learner = User.objects.get(pk=learner_id)
        skill = Skill.objects.get(pk=skill_id)
    except (User.DoesNotExist, Skill.DoesNotExist) as e:
        logger.error(f"Cannot recompute mastery: {e}")
        return {"status": "error", "message": str(e)}

    engine = get_adaptive_engine()
    student_skill = engine.update_mastery(learner, skill, score_obtained, max_score)
    logger.info(f"Updated mastery for {learner.email} on {skill.name}: {student_skill.mastery_score}%")

    # Find courses that teach this skill and regenerate learning paths if enrolled
    related_course_ids = LessonSkill.objects.filter(skill=skill).values_list("lesson__module__course_id", flat=True).distinct()
    enrollments = Enrollment.objects.filter(learner=learner, course_id__in=related_course_ids, status=Enrollment.Status.ACTIVE)

    refreshed_courses = []
    for enrollment in enrollments:
        engine.generate_path(learner, enrollment.course)
        refreshed_courses.append(enrollment.course.slug)

    return {
        "status": "success",
        "learner": learner.email,
        "skill": skill.name,
        "mastery_score": student_skill.mastery_score,
        "refreshed_paths": refreshed_courses,
    }
