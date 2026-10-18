import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.courses.models import Category, Course, Enrollment, Lesson, Module
from apps.learning.engine import RuleBasedAdaptiveStrategy, get_adaptive_engine
from apps.learning.models import (
    LearningPath,
    LearningPathItem,
    LessonSkill,
    Skill,
    SkillPrerequisite,
    StudentSkill,
)
from apps.learning.tasks import recompute_student_mastery_task
from apps.users.models import User


@pytest.fixture
def learner_user(db):
    return User.objects.create_user(
        email="adaptive.learner@example.com",
        password="TestPassword123!",
        role=User.Role.LEARNER,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def instructor_user(db):
    return User.objects.create_user(
        email="adaptive.instructor@example.com",
        password="TestPassword123!",
        role=User.Role.INSTRUCTOR,
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )


@pytest.fixture
def skill_tree(db):
    # Foundational -> Intermediate -> Advanced
    s_basics = Skill.objects.create(name="Python Basics", slug="python-basics")
    s_oop = Skill.objects.create(name="Object-Oriented Programming", slug="python-oop")
    s_design = Skill.objects.create(name="Design Patterns", slug="design-patterns")

    # Prerequisite edges: Basics -> OOP -> Design Patterns
    SkillPrerequisite.objects.create(skill=s_oop, prerequisite=s_basics)
    SkillPrerequisite.objects.create(skill=s_design, prerequisite=s_oop)

    return s_basics, s_oop, s_design


@pytest.fixture
def adaptive_course(db, instructor_user, skill_tree):
    s_basics, s_oop, s_design = skill_tree
    cat = Category.objects.create(name="Programming", slug="programming-cat")
    course = Course.objects.create(
        title="Software Architecture Masterclass",
        slug="arch-masterclass",
        instructor=instructor_user,
        category=cat,
        status=Course.Status.DRAFT,
    )
    mod1 = Module.objects.create(course=course, title="Foundations", position=1)
    les_foundational = Lesson.objects.create(
        module=mod1,
        title="Intro to Python Classes",
        slug="intro-python-classes",
        position=1,
        is_required=True,
        is_published=True,
    )
    LessonSkill.objects.create(lesson=les_foundational, skill=s_basics, contribution_weight=1.0)

    mod2 = Module.objects.create(course=course, title="Advanced Patterns", position=2)
    les_patterns = Lesson.objects.create(
        module=mod2,
        title="Factory & Strategy Patterns",
        slug="factory-strategy-patterns",
        position=1,
        is_required=True,
        is_published=True,
    )
    LessonSkill.objects.create(lesson=les_patterns, skill=s_design, contribution_weight=1.0)

    course.publish()
    return course, les_foundational, les_patterns


@pytest.fixture
def auth_client(learner_user):
    client = APIClient()
    client.force_authenticate(user=learner_user)
    return client


@pytest.mark.django_db
class TestSkillDAGInvariants:
    def test_self_prerequisite_rejected(self, skill_tree):
        s_basics, _, _ = skill_tree
        with pytest.raises(ValidationError) as exc:
            SkillPrerequisite.objects.create(skill=s_basics, prerequisite=s_basics)
        assert "A skill cannot be a prerequisite of itself" in str(exc.value)

    def test_circular_prerequisite_rejected(self, skill_tree):
        s_basics, s_oop, s_design = skill_tree
        # s_basics -> s_oop -> s_design already exists.
        # Adding s_basics with prerequisite s_design would create a cycle!
        with pytest.raises(ValidationError) as exc:
            SkillPrerequisite.objects.create(skill=s_basics, prerequisite=s_design)
        assert "Circular prerequisite dependency detected" in str(exc.value)


@pytest.mark.django_db
class TestAdaptiveEngine:
    def test_remediation_path_assembly_for_struggling_learner(
        self, learner_user, adaptive_course, skill_tree
    ):
        course, les_foundational, les_patterns = adaptive_course
        s_basics, s_oop, s_design = skill_tree
        Enrollment.objects.create(learner=learner_user, course=course)

        # Student has low mastery (45% < 70%) on Design Patterns
        StudentSkill.objects.create(learner=learner_user, skill=s_design, mastery_score=45)

        engine = RuleBasedAdaptiveStrategy()
        path = engine.generate_path(learner_user, course)

        items = list(path.items.all())
        # First item should be remediation of foundational lesson
        remediation_items = [i for i in items if i.path_type == LearningPathItem.PathType.REMEDIATION]
        assert len(remediation_items) >= 1
        assert "Remediation:" in remediation_items[0].reason
        assert "45% < 70%" in remediation_items[0].reason

    def test_enrichment_path_for_mastered_learner(
        self, learner_user, adaptive_course, skill_tree
    ):
        course, les_foundational, les_patterns = adaptive_course
        s_basics, s_oop, s_design = skill_tree
        Enrollment.objects.create(learner=learner_user, course=course)

        # Student has high mastery (92% >= 85%) on Design Patterns
        StudentSkill.objects.create(learner=learner_user, skill=s_design, mastery_score=92)

        engine = RuleBasedAdaptiveStrategy()
        path = engine.generate_path(learner_user, course)

        enrichment_items = [i for i in path.items.all() if i.path_type == LearningPathItem.PathType.ENRICHMENT]
        assert len(enrichment_items) >= 1
        assert "Enrichment:" in enrichment_items[0].reason
        assert "92%" in enrichment_items[0].reason


@pytest.mark.django_db
class TestAdaptiveAPIEndpoints:
    def test_get_learning_path(self, auth_client, learner_user, adaptive_course):
        course, _, _ = adaptive_course
        Enrollment.objects.create(learner=learner_user, course=course)

        url = reverse("learning:learning-path", kwargs={"course_slug": course.slug})
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["course_slug"] == course.slug
        assert len(res.data["items"]) >= 2
        for item in res.data["items"]:
            assert "reason" in item
            assert len(item["reason"]) > 0

    def test_path_regeneration_rate_limiting(self, auth_client, learner_user, adaptive_course):
        course, _, _ = adaptive_course
        Enrollment.objects.create(learner=learner_user, course=course)

        url = reverse("learning:learning-path-regenerate", kwargs={"course_slug": course.slug})
        
        # First call succeeds
        res1 = auth_client.post(url)
        assert res1.status_code == status.HTTP_200_OK

        # Immediate second call is rate-limited (FR-PER-04)
        res2 = auth_client.post(url)
        assert res2.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "rate-limited" in res2.data["detail"]

    def test_evaluate_skill_synchronous(self, auth_client, skill_tree):
        s_basics, _, _ = skill_tree
        url = reverse("learning:skill-evaluate", kwargs={"skill_slug": s_basics.slug})
        payload = {"score": 85, "max_score": 100, "async_mode": False}

        res = auth_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["mastery_score"] == 85

    def test_evaluate_skill_celery_task(self, learner_user, skill_tree, adaptive_course):
        course, _, _ = adaptive_course
        s_basics, _, _ = skill_tree
        Enrollment.objects.create(learner=learner_user, course=course)

        # Call celery task directly
        result = recompute_student_mastery_task(
            learner_id=str(learner_user.id),
            skill_id=str(s_basics.id),
            score_obtained=90,
            max_score=100,
        )
        assert result["status"] == "success"
        assert result["mastery_score"] == 90
        assert course.slug in result["refreshed_paths"]
