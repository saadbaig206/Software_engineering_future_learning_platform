from django.urls import path
from apps.discussions.views import (
    CourseThreadsListView,
    ThreadDetailView,
    AddPostReplyView,
    ToggleThreadVoteView,
    TogglePostVoteView,
    EndorsePostView,
    FileContentReportView,
    ModerationQueueView,
)

app_name = "discussions"

urlpatterns = [
    path("courses/<slug:course_slug>/threads/", CourseThreadsListView.as_view(), name="course-threads"),
    path("threads/<uuid:id>/", ThreadDetailView.as_view(), name="thread-detail"),
    path("threads/<uuid:thread_id>/posts/", AddPostReplyView.as_view(), name="thread-add-post"),
    path("threads/<uuid:id>/vote/", ToggleThreadVoteView.as_view(), name="thread-vote"),
    path("posts/<uuid:id>/vote/", TogglePostVoteView.as_view(), name="post-vote"),
    path("posts/<uuid:id>/endorse/", EndorsePostView.as_view(), name="post-endorse"),
    path("reports/", FileContentReportView.as_view(), name="file-report"),
    path("moderation/reports/", ModerationQueueView.as_view(), name="moderation-queue"),
    path("moderation/reports/<uuid:report_id>/resolve/", ModerationQueueView.as_view(), name="moderation-resolve"),
]
