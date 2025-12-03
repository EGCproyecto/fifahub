from locust import HttpUser, TaskSet, between, task

from core.environment.host import get_host_for_locust_testing


class TrendingBehavior(TaskSet):
    @task
    def trending(self):
        with self.client.get("/datasets/trending", name="/datasets/trending", catch_response=True) as response:
            if response.status_code >= 500:
                response.failure(f"Unexpected {response.status_code}")
            else:
                try:
                    payload = response.json()
                    if not isinstance(payload, list):
                        response.failure("Response is not a list")
                except Exception as exc:
                    response.failure(f"Invalid JSON: {exc}")


class TrendingUser(HttpUser):
    tasks = [TrendingBehavior]
    wait_time = between(1, 3)
    host = get_host_for_locust_testing()


# Run with:
# locust -f app/modules/dataset/tests/locust_trending.py -u 50 -r 10
