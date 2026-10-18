from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views import (
    CustomTokenObtainPairView,
    EmailVerificationView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    UserManagementViewSet,
    UserProfileView,
    UserRegistrationView,
    GDPRExportView,
    GDPRErasureView,
)

router = DefaultRouter()
router.register(r"admin/users", UserManagementViewSet, basename="admin-users")

urlpatterns = [
    # Authentication endpoints
    path("register/", UserRegistrationView.as_view(), name="auth-register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("verify-email/", EmailVerificationView.as_view(), name="auth-verify-email"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("me/", UserProfileView.as_view(), name="auth-me"),
    # GDPR Privacy & Data Subject Rights (FR-PRV-01, FR-PRV-02)
    path("privacy/export/", GDPRExportView.as_view(), name="privacy-export"),
    path("privacy/erase/", GDPRErasureView.as_view(), name="privacy-erase"),
    # User management
    path("", include(router.urls)),
]
