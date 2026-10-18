from django.urls import path
from apps.notifications.views import (
    NotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)

app_name = "notifications"

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<uuid:id>/read/", MarkNotificationReadView.as_view(), name="notification-read"),
    path("notifications/mark-all-read/", MarkAllNotificationsReadView.as_view(), name="notification-mark-all-read"),
]
