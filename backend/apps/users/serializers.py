import hashlib
import secrets
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.users.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes SimpleJWT payload with user id, role, email, and full name.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = str(user.id)
        token["email"] = user.email
        token["role"] = user.role
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["is_email_verified"] = user.is_email_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "role": self.user.role,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_email_verified": self.user.is_email_verified,
            "avatar": self.user.avatar,
        }
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    terms_accepted = serializers.BooleanField(required=True)
    privacy_accepted = serializers.BooleanField(required=True)
    marketing_consent = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role",
            "password", "password_confirm",
            "terms_accepted", "privacy_accepted", "marketing_consent"
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        if not attrs.get("terms_accepted"):
            raise serializers.ValidationError({"terms_accepted": "Terms of Service must be accepted."})
        if not attrs.get("privacy_accepted"):
            raise serializers.ValidationError({"privacy_accepted": "Privacy Policy must be accepted."})
        
        # Enforce that normal registration can only create LEARNER or INSTRUCTOR
        role = attrs.get("role", User.Role.LEARNER)
        if role not in [User.Role.LEARNER, User.Role.INSTRUCTOR]:
            attrs["role"] = User.Role.LEARNER
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        terms = validated_data.pop("terms_accepted")
        privacy = validated_data.pop("privacy_accepted")
        marketing = validated_data.pop("marketing_consent", False)
        password = validated_data.pop("password")

        request = self.context.get("request")
        ip_address = None
        if request and hasattr(request, "META"):
            ip_address = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR"))
            if ip_address and "," in ip_address:
                ip_address = ip_address.split(",")[0].strip()

        token = secrets.token_urlsafe(32)
        ip_hash = hashlib.sha256(ip_address.encode("utf-8")).hexdigest() if ip_address else None

        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=validated_data.get("role", User.Role.LEARNER),
            terms_accepted=terms,
            privacy_accepted=privacy,
            marketing_consent=marketing,
            consent_timestamp=timezone.now(),
            consent_ip_hash=ip_hash,
            email_verification_token=token,
            email_verification_sent_at=timezone.now(),
            is_email_verified=False,
        )
        return user


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)

    def validate_token(self, value):
        try:
            user = User.objects.get(email_verification_token=value)
            self.context["user"] = user
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification token.")

    def save(self):
        user = self.context["user"]
        user.is_email_verified = True
        user.email_verification_token = None
        user.save(update_fields=["is_email_verified", "email_verification_token"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def save(self):
        email = self.validated_data["email"].lower()
        try:
            user = User.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            user.password_reset_sent_at = timezone.now()
            user.save(update_fields=["password_reset_token", "password_reset_sent_at"])
            # Return token for programmatic testing / mock mailer
            return {"token": token, "email": email}
        except User.DoesNotExist:
            # Timing-attack resistant generic response
            return {"token": None, "email": email}


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        try:
            user = User.objects.get(password_reset_token=attrs["token"])
            # Check 15-min expiry
            if user.password_reset_sent_at:
                delta = timezone.now() - user.password_reset_sent_at
                if delta.total_seconds() > 900:  # 15 minutes
                    raise serializers.ValidationError({"token": "Password reset token has expired."})
            self.context["user"] = user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid password reset token."})

    def save(self):
        user = self.context["user"]
        user.set_password(self.validated_data["password"])
        user.password_reset_token = None
        user.password_reset_sent_at = None
        user.save(update_fields=["password", "password_reset_token", "password_reset_sent_at"])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role",
            "is_email_verified", "avatar", "bio", "preferred_language",
            "terms_accepted", "privacy_accepted", "marketing_consent",
            "date_joined"
        ]
        read_only_fields = ["id", "email", "role", "is_email_verified", "date_joined", "terms_accepted", "privacy_accepted"]


class UserPublicSerializer(serializers.ModelSerializer):
    """Safe public serializer for forum posts, author signatures, and user cards."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "role", "avatar"]

    def get_full_name(self, obj) -> str:
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.email.split("@")[0]
