import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def learner_user(db):
    user = User.objects.create_user(
        email="learner@futurelearning.test",
        password="ValidPassword123!",
        role=User.Role.LEARNER,
        first_name="Learner",
        last_name="User",
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )
    return user


@pytest.fixture
def instructor_user(db):
    user = User.objects.create_user(
        email="instructor@futurelearning.test",
        password="ValidPassword123!",
        role=User.Role.INSTRUCTOR,
        first_name="Jane",
        last_name="Professor",
        is_email_verified=True,
        terms_accepted=True,
        privacy_accepted=True,
    )
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(
        email="admin@futurelearning.test",
        password="AdminPassword123!",
        first_name="Platform",
        last_name="Admin",
    )
    return user


@pytest.mark.django_db
class TestAuthenticationAndUserManagement:
    """
    Test suite for Module 1 requirements: FR-AUTH-01 through FR-AUTH-05.
    """

    def test_registration_with_gdpr_consent_success(self, api_client):
        """FR-AUTH-01, FR-AUTH-05: Learner can register with valid credentials and explicit consent."""
        url = reverse("auth-register")
        payload = {
            "email": "newstudent@futurelearning.test",
            "password": "StrongPassword99!",
            "password_confirm": "StrongPassword99!",
            "first_name": "New",
            "last_name": "Student",
            "role": "LEARNER",
            "terms_accepted": True,
            "privacy_accepted": True,
            "marketing_consent": False,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert response.data["user"]["email"] == "newstudent@futurelearning.test"

        user = User.objects.get(email="newstudent@futurelearning.test")
        assert user.is_email_verified is False
        assert user.terms_accepted is True
        assert user.privacy_accepted is True
        assert user.consent_timestamp is not None
        assert user.email_verification_token is not None

    def test_registration_rejects_missing_gdpr_consent(self, api_client):
        """FR-AUTH-05: Registration must reject users who do not accept terms and privacy policy."""
        url = reverse("auth-register")
        payload = {
            "email": "noconsent@futurelearning.test",
            "password": "StrongPassword99!",
            "password_confirm": "StrongPassword99!",
            "terms_accepted": False,
            "privacy_accepted": True,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "terms_accepted" in response.data

    def test_registration_rejects_password_mismatch(self, api_client):
        """FR-AUTH-01: Password confirmation must match."""
        url = reverse("auth-register")
        payload = {
            "email": "mismatch@futurelearning.test",
            "password": "StrongPassword99!",
            "password_confirm": "DifferentPassword123!",
            "terms_accepted": True,
            "privacy_accepted": True,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_email_verification_flow(self, api_client):
        """FR-AUTH-01: Verifying email via token sets is_email_verified to True."""
        user = User.objects.create_user(
            email="unverified@futurelearning.test",
            password="ValidPassword123!",
            email_verification_token="test-verification-token-12345",
            is_email_verified=False,
            terms_accepted=True,
            privacy_accepted=True,
        )
        url = reverse("auth-verify-email")
        response = api_client.post(url, {"token": "test-verification-token-12345"}, format="json")
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_email_verified is True
        assert user.email_verification_token is None

    def test_jwt_login_returns_custom_claims(self, api_client, instructor_user):
        """FR-AUTH-03: JWT login returns access & refresh tokens with custom claims (role, email, user_id)."""
        url = reverse("token-obtain-pair")
        response = api_client.post(
            url,
            {"email": instructor_user.email, "password": "ValidPassword123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["role"] == User.Role.INSTRUCTOR
        assert response.data["user"]["email"] == instructor_user.email

    def test_password_reset_flow(self, api_client, learner_user):
        """FR-AUTH-04: Password reset request generates token and confirm updates password."""
        req_url = reverse("auth-password-reset")
        req_response = api_client.post(req_url, {"email": learner_user.email}, format="json")
        assert req_response.status_code == status.HTTP_200_OK

        learner_user.refresh_from_db()
        token = learner_user.password_reset_token
        assert token is not None

        confirm_url = reverse("auth-password-reset-confirm")
        confirm_response = api_client.post(
            confirm_url,
            {
                "token": token,
                "password": "NewSecretPassword2026!",
                "password_confirm": "NewSecretPassword2026!",
            },
            format="json",
        )
        assert confirm_response.status_code == status.HTTP_200_OK

        # Verify login with new password succeeds
        login_url = reverse("token-obtain-pair")
        login_response = api_client.post(
            login_url,
            {"email": learner_user.email, "password": "NewSecretPassword2026!"},
            format="json",
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_user_profile_me_endpoint(self, api_client, learner_user):
        """Learner can view and update their own profile."""
        api_client.force_authenticate(user=learner_user)
        url = reverse("auth-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == learner_user.email

        update_response = api_client.patch(url, {"bio": "Aspiring AI Engineer", "marketing_consent": True}, format="json")
        assert update_response.status_code == status.HTTP_200_OK
        learner_user.refresh_from_db()
        assert learner_user.bio == "Aspiring AI Engineer"
        assert learner_user.marketing_consent is True
