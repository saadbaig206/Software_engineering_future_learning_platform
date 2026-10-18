from django.shortcuts import get_object_or_404
from django.db.models import F
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from apps.courses.models import Course, Lesson
from apps.discussions.models import (
    DiscussionThread,
    DiscussionPost,
    ThreadVote,
    PostVote,
    ContentReport,
)
from apps.discussions.serializers import (
    DiscussionThreadListSerializer,
    DiscussionThreadDetailSerializer,
    DiscussionPostSerializer,
    CreateThreadSerializer,
    CreatePostSerializer,
    ContentReportSerializer,
)
from apps.notifications.tasks import dispatch_notification_task


class CourseThreadsListView(APIView):
    """
    List and filter discussion threads for a course, or create a new thread.
    Fulfills FR-DIS-01.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        queryset = DiscussionThread.objects.filter(
            course=course, status__in=[DiscussionThread.Status.ACTIVE, DiscussionThread.Status.PINNED, DiscussionThread.Status.LOCKED]
        ).select_related("author")

        lesson_id = request.query_params.get("lesson_id")
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        serializer = DiscussionThreadListSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        serializer = CreateThreadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lesson_id = serializer.validated_data.get("lesson_id")
        lesson = Lesson.objects.filter(id=lesson_id, module__course=course).first() if lesson_id else None

        thread = DiscussionThread.objects.create(
            course=course,
            lesson=lesson,
            author=request.user,
            title=serializer.validated_data["title"],
            body=serializer.validated_data["body"],
        )
        return Response(
            DiscussionThreadDetailSerializer(thread, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ThreadDetailView(RetrieveAPIView):
    """
    Retrieve full thread conversation with replies (FR-DIS-02).
    Increments view count.
    """
    queryset = DiscussionThread.objects.select_related("author").prefetch_related("posts__replies")
    serializer_class = DiscussionThreadDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        DiscussionThread.objects.filter(id=instance.id).update(views_count=F("views_count") + 1)
        instance.refresh_from_db(fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AddPostReplyView(APIView):
    """
    Add reply to a discussion thread or parent post.
    Dispatches asynchronous notification to thread author (FR-DIS-02, FR-NOT-01).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, thread_id):
        thread = get_object_or_404(DiscussionThread, id=thread_id)
        if thread.status == DiscussionThread.Status.LOCKED:
            return Response(
                {"detail": "This thread is locked by staff. No new replies allowed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreatePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parent_id = serializer.validated_data.get("parent_id")
        parent = DiscussionPost.objects.filter(id=parent_id, thread=thread).first() if parent_id else None

        post = DiscussionPost.objects.create(
            thread=thread,
            author=request.user,
            parent=parent,
            body=serializer.validated_data["body"],
        )

        # Notify thread author asynchronously via Celery if not self
        recipient_id = parent.author_id if parent else thread.author_id
        if recipient_id != request.user.id:
            try:
                dispatch_notification_task.delay(
                    recipient_id=str(recipient_id),
                    notification_type="FORUM_REPLY",
                    title="New reply on your discussion",
                    message=f"{request.user.first_name or request.user.email} replied to '{thread.title}'",
                    action_url=f"/courses/{thread.course.slug}?thread={thread.id}",
                )
            except Exception:
                pass

        return Response(
            DiscussionPostSerializer(post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ToggleThreadVoteView(APIView):
    """Toggle upvote on a discussion thread."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        thread = get_object_or_404(DiscussionThread, id=id)
        existing_vote = ThreadVote.objects.filter(thread=thread, user=request.user).first()

        if existing_vote:
            existing_vote.delete()
            thread.upvotes_count = max(0, thread.upvotes_count - 1)
            has_upvoted = False
        else:
            ThreadVote.objects.create(thread=thread, user=request.user)
            thread.upvotes_count += 1
            has_upvoted = True

        thread.save(update_fields=["upvotes_count"])
        return Response({
            "upvotes_count": thread.upvotes_count,
            "has_upvoted": has_upvoted,
        })


class TogglePostVoteView(APIView):
    """Toggle upvote on a reply post."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        post = get_object_or_404(DiscussionPost, id=id)
        existing_vote = PostVote.objects.filter(post=post, user=request.user).first()

        if existing_vote:
            existing_vote.delete()
            post.upvotes_count = max(0, post.upvotes_count - 1)
            has_upvoted = False
        else:
            PostVote.objects.create(post=post, user=request.user)
            post.upvotes_count += 1
            has_upvoted = True

        post.save(update_fields=["upvotes_count"])
        return Response({
            "upvotes_count": post.upvotes_count,
            "has_upvoted": has_upvoted,
        })


class EndorsePostView(APIView):
    """
    Instructor Answer Endorsement.
    Only instructors or admins can endorse an answer (FR-DIS-03).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        post = get_object_or_404(DiscussionPost, id=id)
        # Check authorization: user must be course instructor, staff, or admin
        is_instructor = (
            post.thread.course.instructor_id == request.user.id
            or request.user.role in ["INSTRUCTOR", "ADMINISTRATOR", "MODERATOR"]
            or request.user.is_staff
        )
        if not is_instructor:
            return Response(
                {"detail": "Only course instructors and moderators can endorse answers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        post.is_endorsed = not post.is_endorsed
        post.endorsed_by = request.user if post.is_endorsed else None
        post.endorsed_at = timezone.now() if post.is_endorsed else None
        post.save(update_fields=["is_endorsed", "endorsed_by", "endorsed_at"])

        if post.is_endorsed and post.author_id != request.user.id:
            try:
                dispatch_notification_task.delay(
                    recipient_id=str(post.author_id),
                    notification_type="ANSWER_ENDORSED",
                    title="Your answer was endorsed!",
                    message=f"An instructor endorsed your answer in '{post.thread.title}'",
                    action_url=f"/courses/{post.thread.course.slug}?thread={post.thread.id}",
                )
            except Exception:
                pass

        return Response({
            "is_endorsed": post.is_endorsed,
            "endorsed_at": post.endorsed_at.isoformat() if post.endorsed_at else None,
        })


class FileContentReportView(APIView):
    """
    File moderation report for inappropriate thread or post (FR-DIS-04).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        thread_id = request.data.get("thread_id")
        post_id = request.data.get("post_id")
        reason = request.data.get("reason", "OTHER")
        details = request.data.get("details", "")

        thread = DiscussionThread.objects.filter(id=thread_id).first() if thread_id else None
        post = DiscussionPost.objects.filter(id=post_id).first() if post_id else None

        if not thread and not post:
            return Response(
                {"detail": "Either thread_id or post_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report = ContentReport.objects.create(
            reporter=request.user,
            thread=thread,
            post=post,
            reason=reason,
            details=details,
        )
        return Response(
            ContentReportSerializer(report).data, status=status.HTTP_201_CREATED
        )


class ModerationQueueView(APIView):
    """
    Moderator review queue (FR-DIS-05).
    Accessible to Moderators, Instructors, and Administrators.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["MODERATOR", "ADMINISTRATOR", "INSTRUCTOR"] and not request.user.is_staff:
            return Response(
                {"detail": "Access restricted to moderators and staff."},
                status=status.HTTP_403_FORBIDDEN,
            )

        reports = ContentReport.objects.filter(status=ContentReport.Status.PENDING).select_related("reporter")
        return Response(ContentReportSerializer(reports, many=True).data)

    def post(self, request, report_id):
        if request.user.role not in ["MODERATOR", "ADMINISTRATOR"] and not request.user.is_staff:
            return Response(
                {"detail": "Access restricted to moderators and staff."},
                status=status.HTTP_403_FORBIDDEN,
            )

        report = get_object_or_404(ContentReport, id=report_id)
        action = request.data.get("action")  # "RESOLVE_HIDE", "DISMISS"
        notes = request.data.get("notes", "")

        if action == "RESOLVE_HIDE":
            report.status = ContentReport.Status.RESOLVED
            if report.post:
                report.post.status = DiscussionPost.Status.HIDDEN
                report.post.save(update_fields=["status"])
            elif report.thread:
                report.thread.status = DiscussionThread.Status.HIDDEN
                report.thread.save(update_fields=["status"])
        else:
            report.status = ContentReport.Status.DISMISSED

        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.resolution_notes = notes
        report.save()

        return Response(ContentReportSerializer(report).data)
