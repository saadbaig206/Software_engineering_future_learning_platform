from rest_framework import serializers
from apps.content.models import ContentBlock, CourseVersionSnapshot, MediaAsset
from apps.content.services.storage import StorageService


class MediaAssetSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = [
            "id", "uploaded_by", "storage_key", "original_filename",
            "mime_type", "size_bytes", "duration_seconds", "thumbnail_key",
            "transcript_url", "captions_url", "status", "download_url",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "uploaded_by", "status", "duration_seconds",
            "thumbnail_key", "download_url", "created_at", "updated_at"
        ]

    def get_download_url(self, obj):
        request = self.context.get("request")
        return StorageService.generate_download_url(obj.storage_key, request=request)


class ContentBlockSerializer(serializers.ModelSerializer):
    media_asset_details = MediaAssetSerializer(source="media_asset", read_only=True)

    class Meta:
        model = ContentBlock
        fields = [
            "id", "lesson", "block_type", "title", "position",
            "content_payload", "media_asset", "media_asset_details",
            "is_draft", "version", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        block_type = attrs.get("block_type")
        payload = attrs.get("content_payload", {})

        # Basic payload shape verification per block type
        if block_type == ContentBlock.BlockType.TEXT and "markdown" not in payload and "html" not in payload:
            # Provide default empty markdown if not provided
            payload.setdefault("markdown", "")
        elif block_type == ContentBlock.BlockType.SIMULATION and "sim_url" not in payload:
            payload.setdefault("sim_url", "")
            payload.setdefault("sandbox_flags", "allow-scripts allow-same-origin")

        attrs["content_payload"] = payload
        return attrs


class PresignedUploadRequestSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255, required=True)
    mime_type = serializers.CharField(max_length=100, required=True)
    size_bytes = serializers.IntegerField(min_value=1, max_value=1073741824, required=True)  # 1 GB max (FR-MED-01)


class MediaConfirmSerializer(serializers.Serializer):
    storage_key = serializers.CharField(max_length=500, required=True)
    original_filename = serializers.CharField(max_length=255, required=True)
    mime_type = serializers.CharField(max_length=100, required=True)
    size_bytes = serializers.IntegerField(min_value=1, required=True)


class CourseVersionSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseVersionSnapshot
        fields = ["id", "course", "version_number", "created_by", "changelog", "created_at"]
        read_only_fields = ["id", "created_at"]
