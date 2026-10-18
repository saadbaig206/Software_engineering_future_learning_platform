import uuid

from django.db import models


class BaseTimeStampedModel(models.Model):
    """
    Abstract base model providing self-updating UUID primary key
    and timezone-aware created_at and updated_at fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
