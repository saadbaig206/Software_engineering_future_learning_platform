from rest_framework import serializers
from apps.discussions.models import (
    DiscussionThread,
    DiscussionPost,
    ThreadVote,
    PostVote,
    ContentReport,
)
from apps.users.serializers import UserPublicSerializer


class DiscussionPostSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    has_upvoted = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionPost
        fields = [
            "id",
            "thread",
            "author",
            "parent",
            "body",
            "is_endorsed",
            "endorsed_by",
            "endorsed_at",
            "status",
            "upvotes_count",
            "has_upvoted",
            "replies",
            "created_at",
            "updated_at",
        ]

    def get_has_upvoted(self, obj) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return PostVote.objects.filter(post=obj, user=request.user).exists()
        return False

    def get_replies(self, obj):
        # Only nest 1-level down if this is a top-level post
        if obj.parent_id is None:
            child_posts = obj.replies.filter(status=DiscussionPost.Status.ACTIVE).select_related("author")
            return DiscussionPostSerializer(child_posts, many=True, context=self.context).data
        return []


class DiscussionThreadListSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    has_upvoted = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionThread
        fields = [
            "id",
            "course",
            "lesson",
            "author",
            "title",
            "body",
            "status",
            "is_pinned",
            "upvotes_count",
            "views_count",
            "replies_count",
            "has_upvoted",
            "created_at",
            "updated_at",
        ]

    def get_has_upvoted(self, obj) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ThreadVote.objects.filter(thread=obj, user=request.user).exists()
        return False


class DiscussionThreadDetailSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    posts = serializers.SerializerMethodField()
    has_upvoted = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionThread
        fields = [
            "id",
            "course",
            "lesson",
            "author",
            "title",
            "body",
            "status",
            "is_pinned",
            "upvotes_count",
            "views_count",
            "has_upvoted",
            "posts",
            "created_at",
            "updated_at",
        ]

    def get_has_upvoted(self, obj) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ThreadVote.objects.filter(thread=obj, user=request.user).exists()
        return False

    def get_posts(self, obj):
        # Return only top-level posts (parent=None); nested replies are populated by DiscussionPostSerializer
        top_posts = obj.posts.filter(parent=None, status=DiscussionPost.Status.ACTIVE).select_related("author")
        return DiscussionPostSerializer(top_posts, many=True, context=self.context).data


class CreateThreadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    lesson_id = serializers.UUIDField(required=False, allow_null=True)


class CreatePostSerializer(serializers.Serializer):
    body = serializers.CharField()
    parent_id = serializers.UUIDField(required=False, allow_null=True)


class ContentReportSerializer(serializers.ModelSerializer):
    reporter = UserPublicSerializer(read_only=True)

    class Meta:
        model = ContentReport
        fields = [
            "id",
            "reporter",
            "thread",
            "post",
            "reason",
            "details",
            "status",
            "created_at",
            "resolved_at",
        ]
