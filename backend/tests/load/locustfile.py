"""
FutureLearning Learning Engine - Locust Performance & Load Test Suite
Evaluates NFR-PERF-01 (<500ms p95 latency under 500 concurrent virtual users).

Run locally with:
    locust -f backend/tests/load/locustfile.py --host=http://127.0.0.1:8000
Or headless batch benchmark:
    locust -f backend/tests/load/locustfile.py --headless -u 100 -r 10 --run-time 1m --host=http://127.0.0.1:8000
"""
from locust import HttpUser, task, between
import random


class FutureLearningLoadTester(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Simulate user login or token acquisition if available."""
        self.access_token = None
        # Attempt to obtain a token if credentials match test seed
        try:
            resp = self.client.post(
                "/api/v1/auth/token/",
                json={"email": "learner@test.com", "password": "Password123!"},
            )
            if resp.status_code == 200:
                self.access_token = resp.json().get("access")
        except Exception:
            pass

    @task(5)
    def browse_course_catalog(self):
        """High-frequency public catalog browsing."""
        self.client.get("/api/v1/courses/?page=1&ordering=-created_at", name="/api/v1/courses/")

    @task(3)
    def check_health(self):
        """Service liveness probe."""
        self.client.get("/api/v1/health/", name="/api/v1/health/")

    @task(4)
    def browse_discussions(self):
        """Public or course discussion thread listing."""
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        self.client.get("/api/v1/discussions/threads/", headers=headers, name="/api/v1/discussions/threads/")

    @task(2)
    def simulate_telemetry_heartbeat(self):
        """High-concurrency video progress heartbeat simulation."""
        if not self.access_token:
            return
        headers = {"Authorization": f"Bearer {self.access_token}"}
        # Fake lesson ID for benchmarking endpoint latency & Redis write-through
        self.client.post(
            "/api/v1/progress/heartbeat/",
            json={
                "lesson_id": "00000000-0000-0000-0000-000000000001",
                "last_position_seconds": random.randint(10, 300),
                "completion_percent": random.randint(5, 95),
            },
            headers=headers,
            name="/api/v1/progress/heartbeat/",
        )
