from rest_framework import permissions
from apps.users.models import User


class IsLearner(permissions.BasePermission):
    """Allows access only to authenticated users with LEARNER role (or Admin)."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.LEARNER or request.user.is_staff or request.user.is_superuser)
        )


class IsInstructor(permissions.BasePermission):
    """Allows access only to authenticated users with INSTRUCTOR or ADMIN role."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN] or request.user.is_superuser)
        )


class IsModerator(permissions.BasePermission):
    """Allows access to community moderators and administrators."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.MODERATOR, User.Role.ADMIN] or request.user.is_superuser)
        )


class IsAdminUserOnly(permissions.BasePermission):
    """Allows access only to users with the ADMIN role or superuser status."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.ADMIN or request.user.is_staff or request.user.is_superuser)
        )


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Public read access for SAFE_METHODS; write operations restricted to Instructors and Admins.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN] or request.user.is_superuser)
        )


class IsCourseOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission allowing only the course's instructor (or Admin) to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == User.Role.ADMIN or request.user.is_superuser:
            return True
        # Check if obj is Course or has instructor attribute
        instructor = getattr(obj, "instructor", None)
        if instructor is None and hasattr(obj, "course"):
            instructor = getattr(obj.course, "instructor", None)
        elif instructor is None and hasattr(obj, "module"):
            instructor = getattr(obj.module.course, "instructor", None)
        elif instructor is None and hasattr(obj, "lesson"):
            instructor = getattr(obj.lesson.module.course, "instructor", None)
        return instructor == request.user
