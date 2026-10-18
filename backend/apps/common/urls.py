from django.urls import path

from .views import HealthCheckView, SmokeTestView

app_name = "common"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("smoke-test/", SmokeTestView.as_view(), name="smoke-test"),
]
