import io
import uuid

from bs4 import BeautifulSoup
from locust import HttpUser, constant, task

from core.environment.host import get_host_for_locust_testing

REQUIRED_HEADER = [
    "ID",
    "Name",
    "Age",
    "Nationality",
    "Overall",
    "Potential",
    "Club",
    "Value",
    "Wage",
    "Preferred Foot",
    "Weak Foot",
    "Skill Moves",
    "Position",
    "Height",
    "Weight",
]


class FifaHubUser(HttpUser):
    host = get_host_for_locust_testing()
    wait_time = constant(1)

    def on_start(self):
        self.login()

    def _extract_csrf(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find("input", {"name": "csrf_token"})
        if not token:
            raise ValueError("CSRF token not found in login page")
        return token["value"]

    def login(self):
        response = self.client.get("/login")
        csrf_token = self._extract_csrf(response)

        login_response = self.client.post(
            "/login",
            data={
                "email": "user1@example.com",
                "password": "1234",
                "csrf_token": csrf_token,
            },
        )
        if login_response.status_code not in (200, 302):
            login_response.failure(f"Login failed with status {login_response.status_code}")

    def _build_csv_bytes(self):
        header_line = ",".join(REQUIRED_HEADER)
        row = ",".join(
            [
                "1",
                "Test Player",
                "25",
                "Country",
                "80",
                "85",
                "Club",
                "1000000",
                "50000",
                "Right",
                "4",
                "4",
                "ST",
                "180",
                "75",
            ]
        )
        csv_content = f"{header_line}\n{row}\n"
        return io.BytesIO(csv_content.encode("utf-8"))

    @task
    def upload_dataset(self):
        response = self.client.get("/tabular/upload")
        if response.status_code != 200:
            response.failure(f"Failed to load upload page: {response.status_code}")
            return

        try:
            csrf_token = self._extract_csrf(response)
        except ValueError:
            response.failure("Could not extract CSRF token from upload page")
            return

        csv_file = self._build_csv_bytes()
        files = {"csv_file": ("fifa.csv", csv_file, "text/csv")}

        unique_name = f"Locust Test {uuid.uuid4().hex[:8]}"
        data = {"name": unique_name, "csrf_token": csrf_token}

        with self.client.post(
            "/tabular/upload",
            data=data,
            files=files,
            catch_response=True,
            allow_redirects=False,
        ) as post_response:
            if post_response.status_code in (200, 302):
                post_response.success()
            elif post_response.status_code == 400:
                post_response.failure("Validation Error (400) - Check CSV format")
            else:
                post_response.failure(f"Upload failed with status {post_response.status_code}")
