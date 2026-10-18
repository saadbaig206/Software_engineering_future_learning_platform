import os
import uuid

import boto3
from botocore.config import Config
from django.conf import settings


def get_s3_client():
    """
    Returns a configured boto3 S3 client using environment variables,
    supporting AWS S3, Cloudflare R2, MinIO, or Wasabi (Provider-Agnostic D-003).
    """
    endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL") or None
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_S3_REGION_NAME", "auto"),
        config=Config(signature_version="s3v4"),
    )

def generate_presigned_upload_url(
    filename: str,
    mime_type: str,
    folder: str = "media",
    expires_in: int = 900,
) -> dict:
    """
    Generates a secure presigned PUT URL allowing direct browser uploads.
    Fulfills FR-MED-01 and NFR-SEC-01.
    """
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    storage_key = f"{folder}/{uuid.uuid4()}.{extension}" if extension else f"{folder}/{uuid.uuid4()}"
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", "futurelearning-media")

    if getattr(settings, "USE_S3_STORAGE", False):
        s3_client = get_s3_client()
        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket_name,
                "Key": storage_key,
                "ContentType": mime_type,
            },
            ExpiresIn=expires_in,
        )
        return {
            "mode": "s3_direct",
            "upload_url": upload_url,
            "storage_key": storage_key,
            "bucket": bucket_name,
            "expires_in": expires_in,
        }
    else:
        # Development fallback mode
        return {
            "mode": "dev_local",
            "upload_url": f"/api/v1/media/dev-upload/{storage_key}/",
            "storage_key": storage_key,
            "bucket": "local-disk",
            "expires_in": expires_in,
        }
