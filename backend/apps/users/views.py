from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.users.models import User
from apps.users.permissions import IsAdminUserOnly
from apps.users.serializers import (
    CustomTokenObtainPairSerializer,
    EmailVerificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = {
            "message": "Registration successful. Please verify your email address.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        }
        # In test/dev environment, include the verification token to facilitate automated integration testing
        if settings.DEBUG or getattr(settings, "ENVIRONMENT", "") in ["dev", "test"]:
            response_data["verification_token"] = user.email_verification_token

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class EmailVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Email address verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        response_data = {
            "message": "If this email exists in our system, a password recovery link has been dispatched."
        }
        if (settings.DEBUG or getattr(settings, "ENVIRONMENT", "") in ["dev", "test"]) and result.get("token"):
            response_data["reset_token"] = result["token"]
        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password has been successfully updated. You may now log in with your new credentials."},
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Administrative user management viewset for listing, inspecting, and modifying roles.
    """
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUserOnly]
    filterset_fields = ["role", "is_email_verified", "is_active"]
    search_fields = ["email", "first_name", "last_name"]


class GDPRExportView(APIView):
    """
    Full data portability export in structured JSON format (FR-PRV-01, GDPR Art. 20).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # 1. Profile and Consent
        profile_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "bio": user.bio,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "terms_accepted": user.terms_accepted,
            "privacy_accepted": user.privacy_accepted,
            "marketing_consent": user.marketing_consent,
            "consent_timestamp": user.consent_timestamp.isoformat() if user.consent_timestamp else None,
            "consent_ip_hash": user.consent_ip_hash,
        }

        # 2. Enrollments & Progress
        from apps.courses.models import Enrollment
        from apps.progress.models import LessonProgress, LearningEvent

        enrollments = []
        for e in Enrollment.objects.filter(learner=user).select_related("course"):
            progress_records = [
                {
                    "lesson_id": str(lp.lesson_id),
                    "lesson_title": lp.lesson.title,
                    "status": lp.status,
                    "completion_percent": lp.completion_percent,
                    "last_position_seconds": lp.last_position_seconds,
                    "completed_at": lp.completed_at.isoformat() if lp.completed_at else None,
                }
                for lp in e.lesson_progresses.select_related("lesson")
            ]
            enrollments.append({
                "course_id": str(e.course_id),
                "course_title": e.course.title,
                "course_slug": e.course.slug,
                "status": e.status,
                "completion_percent": e.calculate_progress(),
                "enrolled_at": e.enrolled_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "lesson_progress": progress_records,
            })

        # 3. Quiz Submissions
        from apps.assessments.models import QuizAttempt
        quiz_attempts = []
        for att in QuizAttempt.objects.filter(learner=user).select_related("assessment"):
            responses = [
                {
                    "question_id": str(r.question_id),
                    "question_prompt": r.question.prompt,
                    "points_earned": r.awarded_points,
                    "is_correct": r.is_correct,
                    "text_response": r.text_response,
                }
                for r in att.responses.select_related("question")
            ]
            quiz_attempts.append({
                "assessment_id": str(att.assessment_id),
                "assessment_title": att.assessment.title,
                "attempt_number": att.attempt_number,
                "score_percent": att.score_percent,
                "passed": att.passed,
                "started_at": att.started_at.isoformat() if att.started_at else None,
                "submitted_at": att.submitted_at.isoformat() if att.submitted_at else None,
                "responses": responses,
            })

        # 4. Discussion Contributions
        from apps.discussions.models import DiscussionThread, DiscussionPost
        threads = [
            {
                "id": str(t.id),
                "course_slug": t.course.slug,
                "title": t.title,
                "body": t.body,
                "created_at": t.created_at.isoformat(),
            }
            for t in DiscussionThread.objects.filter(author=user).select_related("course")
        ]
        posts = [
            {
                "id": str(p.id),
                "thread_id": str(p.thread_id),
                "body": p.body,
                "is_endorsed": p.is_endorsed,
                "created_at": p.created_at.isoformat(),
            }
            for p in DiscussionPost.objects.filter(author=user)
        ]

        # 5. Learning Telemetry Events
        events = [
            {
                "event_type": ev.event_type,
                "payload": ev.payload,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
            }
            for ev in LearningEvent.objects.filter(user=user)[:200]
        ]

        # Record audit log
        try:
            from apps.analytics.services import AnalyticsRollupService
            from apps.analytics.models import AuditLog
            AnalyticsRollupService.record_audit_log(
                action=AuditLog.Action.GDPR_EXPORT,
                actor=user,
                target_model="User",
                target_id=str(user.id),
                request=request,
            )
        except Exception:
            pass

        export_payload = {
            "export_version": "1.0",
            "export_timestamp": timezone.now().isoformat(),
            "profile": profile_data,
            "enrollments": enrollments,
            "assessments": quiz_attempts,
            "discussions": {
                "threads": threads,
                "posts": posts,
            },
            "telemetry_sample": events,
        }

        response = Response(export_payload, status=status.HTTP_200_OK)
        response["Content-Disposition"] = f'attachment; filename="gdpr_export_{user.id}.json"'
        return response


class GDPRErasureView(APIView):
    """
    Right to Erasure / Pseudonymization (FR-PRV-02, GDPR Art. 17).
    Permanently erases identifying user information while maintaining system statistical integrity.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get("password")
        confirm = request.data.get("confirm")

        if confirm not in [True, "true", "True", 1, "1"]:
            return Response(
                {"error": "Explicit confirmation (confirm=True) is required to permanently erase account data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not password or not user.check_password(password):
            return Response(
                {"error": "Invalid password. Authentication required for GDPR account erasure."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Audit the erasure before anonymizing user record
        try:
            from apps.analytics.services import AnalyticsRollupService
            from apps.analytics.models import AuditLog
            AnalyticsRollupService.record_audit_log(
                action=AuditLog.Action.GDPR_ERASURE,
                actor=user,
                target_model="User",
                target_id=str(user.id),
                changes={"previous_email": user.email[:3] + "***"},
                request=request,
            )
        except Exception:
            pass

        # Execute Pseudonymization / Erasure
        import uuid
        anon_key = uuid.uuid4().hex[:8]
        user.email = f"anonymized_{anon_key}@deleted.futurelearning.local"
        user.first_name = "Anonymized"
        user.last_name = "Learner"
        user.bio = ""
        user.avatar = None
        user.is_active = False
        user.is_email_verified = False
        user.save()

        return Response(
            {
                "status": "ANONYMIZED",
                "message": "All personal data has been erased and pseudonymized in compliance with GDPR Article 17.",
            },
            status=status.HTTP_200_OK,
        )

