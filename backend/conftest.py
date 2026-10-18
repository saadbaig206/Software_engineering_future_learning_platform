import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Provides a fresh DRF APIClient for tests."""
    return APIClient()
