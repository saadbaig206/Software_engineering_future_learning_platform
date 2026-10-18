from abc import ABC, abstractmethod
from typing import List, Optional
from django.db import transaction
from django.utils import timezone

from apps.courses.models import Course, Enrollment, Lesson
from apps.learning.models import (
    LearningPath,
    LearningPathItem,
    LessonSkill,
    Skill,
    SkillPrerequisite,
    StudentSkill,
)
from apps.progress.models import LearningEvent, LessonProgress
from apps.users.models import User


class AdaptiveStrategy(ABC):
    """
    FR-PER-05: Pluggable Recommendation Strategy Interface.
    Encapsulates adaptive path generation behind a clean strategy contract,
    enabling rule-based, knowledge-space, or future machine learning algorithms.
    """

    @abstractmethod
    def generate_path(self, learner: User, course: Course) -> LearningPath:
        """
        Assembles and persists an explainable personalized learning path.
        """
        pass

    @abstractmethod
    def update_mastery(
        self, learner: User, skill: Skill, score_obtained: int, max_score: int = 100
    ) -> StudentSkill:
        """
        Updates learner mastery score for a skill based on assessment outcomes.
        """
        pass


class RuleBasedAdaptiveStrategy(AdaptiveStrategy):
    """
    Rule-Based Adaptive Engine implementing D-004 and FR-PER-01 to FR-PER-04:
    - Mastery < 70%: Recommends foundational prerequisite remediation lessons.
    - Mastery >= 85%: Recommends advanced enrichment branches.
    - 70% <= Mastery < 85%: Standard curriculum progression.
    All recommendations provide human-readable pedagogical explanations.
    """

    REMEDIATION_THRESHOLD = 70
    ENRICHMENT_THRESHOLD = 85

    @transaction.atomic
    def generate_path(self, learner: User, course: Course) -> LearningPath:
        # 1. Fetch or create the active LearningPath
        path, _ = LearningPath.objects.get_or_create(
            learner=learner,
            course=course,
            status=LearningPath.Status.ACTIVE,
        )

        # 2. Get all published lessons in course order
        curriculum_lessons = (
            Lesson.objects.filter(
                module__course=course,
                is_published=True,
            )
            .select_related("module")
            .order_by("module__position", "position")
        )

        # 3. Query existing progress records
        enrollment = Enrollment.objects.filter(learner=learner, course=course).first()
        completed_lesson_ids = set()
        if enrollment:
            completed_lesson_ids = set(
                LessonProgress.objects.filter(
                    enrollment=enrollment,
                    status=LessonProgress.Status.COMPLETED,
                ).values_list("lesson_id", flat=True)
            )

        # 4. Map skills and student mastery
        student_masteries = {
            ss.skill_id: ss.mastery_score
            for ss in StudentSkill.objects.filter(learner=learner)
        }

        # Clear existing items for this path
        path.items.all().delete()

        path_items_to_create = []
        included_lesson_ids = set()
        current_position = 1

        for lesson in curriculum_lessons:
            # Check skills mapped to this lesson
            lesson_skills = LessonSkill.objects.filter(lesson=lesson).select_related("skill")

            # Check if learner has prerequisite gaps (Mastery < 70%)
            for ls in lesson_skills:
                skill = ls.skill
                mastery = student_masteries.get(skill.id, 50)  # Default 50% if new

                if mastery < self.REMEDIATION_THRESHOLD:
                    # Find all transitive prerequisites for this struggling skill (Knowledge-Space DAG)
                    prereq_skills = []
                    visited_ids = set()
                    queue = list(SkillPrerequisite.objects.filter(skill=skill).select_related("prerequisite"))
                    while queue:
                        edge = queue.pop(0)
                        if edge.prerequisite_id not in visited_ids:
                            visited_ids.add(edge.prerequisite_id)
                            prereq_skills.append(edge.prerequisite)
                            queue.extend(
                                SkillPrerequisite.objects.filter(
                                    skill_id=edge.prerequisite_id
                                ).select_related("prerequisite")
                            )

                    for prereq_skill in prereq_skills:
                        prereq_mastery = student_masteries.get(prereq_skill.id, 50)
                        
                        # Find any foundational lesson that teaches this prerequisite
                        foundational_ls = LessonSkill.objects.filter(
                            skill=prereq_skill,
                            lesson__is_published=True,
                        ).select_related("lesson").first()

                        if foundational_ls and foundational_ls.lesson_id not in completed_lesson_ids:
                            # If already present in path, upgrade it to REMEDIATION with explanation
                            existing_item = next(
                                (item for item in path_items_to_create if item.lesson_id == foundational_ls.lesson_id),
                                None
                            )
                            if existing_item:
                                existing_item.path_type = LearningPathItem.PathType.REMEDIATION
                                existing_item.reason = (
                                    f"Remediation: Prerequisite skill '{prereq_skill.name}' "
                                    f"needs reinforcement before attempting '{skill.name}' "
                                    f"(Current mastery: {mastery}% < {self.REMEDIATION_THRESHOLD}% threshold)."
                                )
                            elif foundational_ls.lesson_id not in included_lesson_ids:
                                path_items_to_create.append(
                                    LearningPathItem(
                                        learning_path=path,
                                        lesson=foundational_ls.lesson,
                                        position=current_position,
                                        path_type=LearningPathItem.PathType.REMEDIATION,
                                        reason=(
                                            f"Remediation: Prerequisite skill '{prereq_skill.name}' "
                                            f"needs reinforcement before attempting '{skill.name}' "
                                            f"(Current mastery: {mastery}% < {self.REMEDIATION_THRESHOLD}% threshold)."
                                        ),
                                        is_completed=False,
                                    )
                                )
                                included_lesson_ids.add(foundational_ls.lesson_id)
                                current_position += 1

                elif mastery >= self.ENRICHMENT_THRESHOLD:
                    # Advanced enrichment branch
                    if lesson.id not in included_lesson_ids:
                        path_items_to_create.append(
                            LearningPathItem(
                                learning_path=path,
                                lesson=lesson,
                                position=current_position,
                                path_type=LearningPathItem.PathType.ENRICHMENT,
                                reason=(
                                    f"Enrichment: You have mastered '{skill.name}' "
                                    f"with {mastery}% score (≥ {self.ENRICHMENT_THRESHOLD}%). "
                                    f"Fast-tracking advanced architectural challenges."
                                ),
                                is_completed=lesson.id in completed_lesson_ids,
                            )
                        )
                        included_lesson_ids.add(lesson.id)
                        current_position += 1

            # Standard curriculum item if not already added
            if lesson.id not in included_lesson_ids:
                is_done = lesson.id in completed_lesson_ids
                path_items_to_create.append(
                    LearningPathItem(
                        learning_path=path,
                        lesson=lesson,
                        position=current_position,
                        path_type=LearningPathItem.PathType.STANDARD,
                        reason=f"Core syllabus unit: Module {lesson.module.position} · {lesson.title}",
                        is_completed=is_done,
                    )
                )
                included_lesson_ids.add(lesson.id)
                current_position += 1

        # Bulk create all assembled path items
        LearningPathItem.objects.bulk_create(path_items_to_create)

        # Log telemetry event
        LearningEvent.objects.create(
            user=learner,
            enrollment=enrollment,
            event_type=LearningEvent.EventType.PATH_REGENERATE,
            payload={
                "course_slug": course.slug,
                "total_items": len(path_items_to_create),
                "remediations": sum(1 for item in path_items_to_create if item.path_type == LearningPathItem.PathType.REMEDIATION),
                "enrichments": sum(1 for item in path_items_to_create if item.path_type == LearningPathItem.PathType.ENRICHMENT),
            }
        )

        return path

    def update_mastery(
        self, learner: User, skill: Skill, score_obtained: int, max_score: int = 100
    ) -> StudentSkill:
        percentage = int(round((score_obtained / max_score) * 100)) if max_score > 0 else 0
        clamped = max(0, min(100, percentage))

        student_skill, created = StudentSkill.objects.get_or_create(
            learner=learner,
            skill=skill,
            defaults={"mastery_score": clamped}
        )
        if not created:
            # Exponential moving average / monotonically updating mastery
            new_mastery = int(round(student_skill.mastery_score * 0.4 + clamped * 0.6))
            student_skill.update_mastery(new_mastery)
        return student_skill


def get_adaptive_engine() -> AdaptiveStrategy:
    """
    Factory function returning the active AdaptiveStrategy instance (FR-PER-05).
    """
    return RuleBasedAdaptiveStrategy()
