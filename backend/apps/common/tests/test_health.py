import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_endpoint():
    """Verify GET /api/v1/health/ returns healthy status and inspects subsystems."""
    client = APIClient()
    url = reverse("common:health-check")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "django" in data["services"]
    assert data["services"]["django"]["status"] == "ok"

@pytest.mark.django_db
def test_smoke_test_endpoint():
    """Verify GET /api/v1/smoke-test/ executes cross-system checks."""
    client = APIClient()
    url = reverse("common:smoke-test")
    response = client.get(url)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_207_MULTI_STATUS]
    data = response.json()
    assert "pipeline" in data
    assert "1_django_api" in data["pipeline"]
    assert data["pipeline"]["1_django_api"]["status"] == "SUCCESS"
