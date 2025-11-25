from locust import HttpUser, TaskSet, between, task


class FakenodoTaskSet(TaskSet):

    def on_start(self):
        self.deposition_id = None

    def _create_deposition_and_store_id(self):
        data = {"dataset_id": 1}

        with self.client.post("/fakenodo/depositions", json=data, catch_response=True) as resp:
            if resp.status_code == 201:
                try:
                    body = resp.json()
                    self.deposition_id = body.get("deposition_id")
                    if not self.deposition_id:
                        resp.failure("No 'deposition_id' field in response JSON")
                    else:
                        resp.success()
                except Exception as e:
                    resp.failure(f"Error parsing JSON response: {e}")
            else:
                resp.failure(f"Unexpected status code creating deposition: {resp.status_code}")

    def _ensure_deposition_exists(self):
        if self.deposition_id is None:
            self._create_deposition_and_store_id()

    @task(2)
    def create_deposition(self):
        self._create_deposition_and_store_id()

    @task(2)
    def upload_file(self):
        self._ensure_deposition_exists()
        if not self.deposition_id:
            return

        data = {"dataset_id": 1}

        self.client.post(
            f"/fakenodo/depositions/{self.deposition_id}/upload", json=data, name="/fakenodo/depositions/[id]/upload"
        )

    @task(1)
    def publish(self):
        self._ensure_deposition_exists()
        if not self.deposition_id:
            return

        self.client.post(
            f"/fakenodo/depositions/{self.deposition_id}/publish", name="/fakenodo/depositions/[id]/publish"
        )

    @task(1)
    def delete_dep(self):
        self._ensure_deposition_exists()
        if not self.deposition_id:
            return

        self.client.delete(f"/fakenodo/depositions/{self.deposition_id}", name="/fakenodo/depositions/[id]")

        self.deposition_id = None


class FakenodoUser(HttpUser):
    host = "http://127.0.0.1:5000"
    tasks = [FakenodoTaskSet]
    wait_time = between(1, 3)

    def on_start(self):
        self.client.post("/login", data={"email": "admin@example.com", "password": "admin"})
