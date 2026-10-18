from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(ListAPIView):
    """
    List user notifications with unread badge count (FR-NOT-02).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient_id=self.request.user.id).order_by("-created_at")[:50]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        unread_count = Notification.objects.filter(
            recipient_id=request.user.id, is_read=False
        ).count()
        return Response({
            "unread_count": unread_count,
            "results": response.data,
        })


class MarkNotificationReadView(APIView):
    """Mark a specific notification as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        notification = Notification.objects.filter(
            id=id, recipient_id=request.user.id
        ).first()
        if not notification:
            return Response({"detail": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        return Response({"status": "marked_read", "id": str(notification.id)})


class MarkAllNotificationsReadView(APIView):
    """Mark all notifications as read for current user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        now = timezone.now()
        updated = Notification.objects.filter(
            recipient_id=request.user.id, is_read=False
        ).update(is_read=True, read_at=now)
        return Response({"status": "all_marked_read", "count": updated})
