# Common Module (`apps.common`)

## Overview
Provides core cross-cutting infrastructure, utilities, base abstract models, storage abstractions, and system health checks for the FutureLearning Learning Engine.

## Contents
- **`models.py`:** `BaseTimeStampedModel` (UUID primary key, timezone-aware `created_at` and `updated_at`).
- **`storage.py`:** S3-compatible provider-agnostic storage adapter (`boto3`) and presigned upload ticket generator ([`D-003`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-003-provider-agnostic-storage-abstraction-with-presigned-uploads)).
- **`views.py`:**
  - `HealthCheckView` (`GET /api/v1/health/`): Real-time subsystem inspection (Django, Neon DB, Redis, Celery).
  - `SmokeTestView` (`GET /api/v1/smoke-test/`): Multi-tier verification pipeline.
- **`tests/`:** Pytest test suite for common health and smoke endpoints.
