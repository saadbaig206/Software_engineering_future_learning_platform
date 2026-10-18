import pytest
from django.urls import reverse
from rest_framework import status
from apps.users.models import User
from apps.courses.models import Course, Module, Lesson
from apps.discussions.models import (
    DiscussionThread,
    DiscussionPost,
    ThreadVote,
    PostVote,
    ContentReport,
)


@pytest.mark.django_db
class TestDiscussionEngine:

    @pytest.fixture
    def setup_discussion_data(self):
        instructor = User.objects.create_user(
            email="instructor_disc@example.com",
            password="InstructorPass123!",
            role=User.Role.INSTRUCTOR,
            terms_accepted=True,
            privacy_accepted=True,
        )
        moderator = User.objects.create_user(
            email="mod_disc@example.com",
            password="ModPass123!",
            role=User.Role.MODERATOR,
            terms_accepted=True,
            privacy_accepted=True,
        )
        learner = User.objects.create_user(
            email="learner_disc@example.com",
            password="LearnerPass123!",
            role=User.Role.LEARNER,
            terms_accepted=True,
            privacy_accepted=True,
        )
        course = Course.objects.create(
            instructor=instructor,
            title="Cloud Architecture",
            slug="cloud-architecture",
            status=Course.Status.PUBLISHED,
        )
        module = Module.objects.create(course=course, title="Networking", position=1)
        lesson = Lesson.objects.create(
            module=module,
            title="VPC Peering",
            slug="vpc-peering",
            position=1,
            is_published=True,
        )

        return {
            "instructor": instructor,
            "moderator": moderator,
            "learner": learner,
            "course": course,
            "lesson": lesson,
        }

    def test_create_and_list_course_discussion_thread(self, api_client, setup_discussion_data):
        """FR-DIS-01: Contextual course thread creation and retrieval."""
        learner = setup_discussion_data["learner"]
        course = setup_discussion_data["course"]
        lesson = setup_discussion_data["lesson"]
        api_client.force_authenticate(user=learner)

        url = reverse("discussions:course-threads", kwargs={"course_slug": course.slug})
        payload = {
            "title": "How does VPC peering handle overlapping CIDRs?",
            "body": "Does AWS or GCP support overlapping IP ranges when establishing peering?",
            "lesson_id": str(lesson.id),
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == payload["title"]

        # List threads
        list_res = api_client.get(url)
        assert list_res.status_code == status.HTTP_200_OK
        assert len(list_res.data) == 1
        assert list_res.data[0]["title"] == payload["title"]

    def test_nested_post_reply_and_instructor_endorsement(self, api_client, setup_discussion_data):
        """FR-DIS-02 & FR-DIS-03: Nested replies and instructor answer endorsement."""
        instructor = setup_discussion_data["instructor"]
        learner = setup_discussion_data["learner"]
        course = setup_discussion_data["course"]

        thread = DiscussionThread.objects.create(
            course=course,
            author=learner,
            title="Question on latency",
            body="How to reduce p99 latency?",
        )

        # 1. Post reply
        api_client.force_authenticate(user=instructor)
        reply_url = reverse("discussions:thread-add-post", kwargs={"thread_id": thread.id})
        post_payload = {"body": "Implement edge caching and connection pooling."}
        res = api_client.post(reply_url, post_payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        post_id = res.data["id"]

        # 2. Endorse reply (FR-DIS-03)
        endorse_url = reverse("discussions:post-endorse", kwargs={"id": post_id})
        endorse_res = api_client.post(endorse_url)
        assert endorse_res.status_code == status.HTTP_200_OK
        assert endorse_res.data["is_endorsed"] is True

        post = DiscussionPost.objects.get(id=post_id)
        assert post.is_endorsed is True
        assert post.endorsed_by == instructor

    def test_learner_cannot_endorse_answer(self, api_client, setup_discussion_data):
        """FR-DIS-03: Ordinary learner cannot endorse answers."""
        learner = setup_discussion_data["learner"]
        course = setup_discussion_data["course"]

        thread = DiscussionThread.objects.create(
            course=course,
            author=learner,
            title="Title",
            body="Body",
        )
        post = DiscussionPost.objects.create(
            thread=thread,
            author=learner,
            body="My own solution",
        )

        api_client.force_authenticate(user=learner)
        endorse_url = reverse("discussions:post-endorse", kwargs={"id": post.id})
        response = api_client.post(endorse_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_toggle_thread_vote_idempotent(self, api_client, setup_discussion_data):
        """Test upvote toggle prevents duplicate votes."""
        learner = setup_discussion_data["learner"]
        course = setup_discussion_data["course"]

        thread = DiscussionThread.objects.create(
            course=course,
            author=learner,
            title="Interesting Architecture Question",
            body="Body",
            upvotes_count=0,
        )

        api_client.force_authenticate(user=learner)
        vote_url = reverse("discussions:thread-vote", kwargs={"id": thread.id})

        # Upvote
        res1 = api_client.post(vote_url)
        assert res1.status_code == status.HTTP_200_OK
        assert res1.data["upvotes_count"] == 1
        assert res1.data["has_upvoted"] is True

        # Toggle remove upvote
        res2 = api_client.post(vote_url)
        assert res2.status_code == status.HTTP_200_OK
        assert res2.data["upvotes_count"] == 0
        assert res2.data["has_upvoted"] is False

    def test_file_report_and_moderation_queue(self, api_client, setup_discussion_data):
        """FR-DIS-04 & FR-DIS-05: Learners report abusive content; moderators resolve queue."""
        learner = setup_discussion_data["learner"]
        moderator = setup_discussion_data["moderator"]
        course = setup_discussion_data["course"]

        thread = DiscussionThread.objects.create(
            course=course,
            author=learner,
            title="Spam Thread",
            body="Buy cheap stuff at spam.com",
        )

        # 1. Learner reports thread
        api_client.force_authenticate(user=learner)
        report_url = reverse("discussions:file-report")
        report_payload = {
            "thread_id": str(thread.id),
            "reason": ContentReport.Reason.SPAM,
            "details": "Obvious promotional spam",
        }
        rep_res = api_client.post(report_url, report_payload, format="json")
        assert rep_res.status_code == status.HTTP_201_CREATED
        report_id = rep_res.data["id"]

        # 2. Moderator checks queue
        api_client.force_authenticate(user=moderator)
        queue_url = reverse("discussions:moderation-queue")
        queue_res = api_client.get(queue_url)
        assert queue_res.status_code == status.HTTP_200_OK
        assert len(queue_res.data) >= 1

        # 3. Moderator resolves report by hiding thread
        resolve_url = reverse("discussions:moderation-resolve", kwargs={"report_id": report_id})
        resolve_payload = {
            "action": "RESOLVE_HIDE",
            "notes": "Spam confirmed. Thread hidden.",
        }
        action_res = api_client.post(resolve_url, resolve_payload, format="json")
        assert action_res.status_code == status.HTTP_200_OK
        assert action_res.data["status"] == ContentReport.Status.RESOLVED

        thread.refresh_from_db()
        assert thread.status == DiscussionThread.Status.HIDDEN
