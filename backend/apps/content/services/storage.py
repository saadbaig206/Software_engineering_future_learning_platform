import os
import uuid
import mimetypes
from django.conf import settings
from django.urls import reverse


MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
    "application/pdf": [b"%PDF"],
    "video/mp4": [b"ftyp", b"\x00\x00\x00"],
    "video/webm": [b"\x1a\x45\xdf\xa3"],
    "audio/mpeg": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "audio/wav": [b"RIFF"],
    "audio/ogg": [b"OggS"],
}


class StorageService:
    """
    Provider-agnostic storage abstraction handling presigned upload URLs
    and validation across AWS S3, Cloudflare R2, and local development.
    """

    @classmethod
    def get_s3_client(cls):
        aws_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        aws_secret = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        region = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")

        if aws_key and aws_secret and bucket:
            try:
                import boto3
                from botocore.config import Config
                session = boto3.session.Session()
                return session.client(
                    "s3",
                    region_name=region,
                    endpoint_url=endpoint,
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                    config=Config(signature_version="s3v4"),
                ), bucket
            except ImportError:
                pass
        return None, None

    @classmethod
    def generate_storage_key(cls, user_id, original_filename, prefix="media"):
        ext = os.path.splitext(original_filename)[1].lower()
        asset_uuid = uuid.uuid4()
        return f"{prefix}/{user_id}/{asset_uuid}{ext}"

    @classmethod
    def generate_presigned_upload(cls, storage_key, mime_type, expires_in=900, request=None):
        client, bucket = cls.get_s3_client()
        if client and bucket:
            upload_url = client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": bucket,
                    "Key": storage_key,
                    "ContentType": mime_type,
                },
                ExpiresIn=expires_in,
            )
            return {
                "upload_url": upload_url,
                "storage_key": storage_key,
                "storage_provider": "s3",
                "method": "PUT",
                "headers": {"Content-Type": mime_type},
            }

        # Local development / CI direct endpoint fallback
        base_url = "http://localhost:8000"
        if request:
            base_url = request.build_absolute_uri("/").rstrip("/")
        
        fallback_url = f"{base_url}/api/v1/content/media/local-upload/?key={storage_key}"
        return {
            "upload_url": fallback_url,
            "storage_key": storage_key,
            "storage_provider": "local",
            "method": "PUT",
            "headers": {"Content-Type": mime_type},
        }

    @classmethod
    def generate_download_url(cls, storage_key, expires_in=3600, request=None):
        client, bucket = cls.get_s3_client()
        if client and bucket:
            return client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": storage_key},
                ExpiresIn=expires_in,
            )
        base_url = "http://localhost:8000"
        if request:
            base_url = request.build_absolute_uri("/").rstrip("/")
        return f"{base_url}/media/{storage_key}"

    @classmethod
    def validate_magic_bytes(cls, header_bytes: bytes, mime_type: str) -> bool:
        """
        FR-MED-02: Validates initial magic bytes to reject spoofed MIME extensions.
        """
        signatures = MAGIC_BYTES.get(mime_type)
        if not signatures:
            # For types without registered signatures (like plaintext/markdown/json), allow by default
            return True
        return any(sig in header_bytes for sig in signatures)
