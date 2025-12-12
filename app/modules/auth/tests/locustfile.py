import pyotp
from bs4 import BeautifulSoup
from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token


class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/signup",
            data={
                "email": fake.email(),
                "password": fake.password(),
                "csrf_token": csrf_token,
            },
        )
        if response.status_code != 200:
            print(f"Signup failed: {response.status_code}")


class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        response = self.client.get("/logout")
        if response.status_code != 200:
            print(f"Logout failed or no active session: {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            print("Already logged in or unexpected response, redirecting to logout")
            self.ensure_logged_out()
            response = self.client.get("/login")

        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/login",
            data={
                "email": "user1@example.com",
                "password": "1234",
                "csrf_token": csrf_token,
            },
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")


class AuthUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()


def _extract_two_factor_token(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    token_input = soup.find("input", {"name": "token"})
    if not token_input:
        raise ValueError("Two-factor token not found in challenge page")
    return token_input.get("value")


class TwoFactorFlow(TaskSet):
    def on_start(self):
        self.email = fake.email()
        self.password = fake.password()
        self.secret = None
        self.recovery_codes: list[str] = []
        self._signup_user()
        self._enable_two_factor()

    def _signup_user(self):
        response = self.client.get("/signup/")
        csrf_token = get_csrf_token(response)
        payload = {
            "name": fake.first_name(),
            "surname": fake.last_name(),
            "email": self.email,
            "password": self.password,
            "csrf_token": csrf_token,
        }
        self.client.post("/signup/", data=payload, name="signup_two_factor")
        self.client.get("/logout")

    def _login_basic(self):
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        return self.client.post(
            "/login",
            data={"email": self.email, "password": self.password, "csrf_token": csrf_token},
            name="login_form",
        )

    def _start_two_factor_challenge(self):
        self.client.get("/logout")
        challenge = self._login_basic()
        token = _extract_two_factor_token(challenge.text)
        return token

    def _verify_via_api(self, payload: dict):
        response = self.client.post("/auth/2fa/verify", json=payload, name="api_verify_two_factor")
        return response

    def _complete_login_via_totp(self):
        token = self._start_two_factor_challenge()
        code = pyotp.TOTP(self.secret).now()
        self._verify_via_api({"token": token, "code": code})

    def _enable_two_factor(self):
        self._login_basic()
        setup = self.client.post("/2fa/setup", name="two_factor_setup")
        data = setup.json()
        secret = data["secret"]
        code = pyotp.TOTP(secret).now()
        verify = self.client.post("/2fa/verify-setup", json={"code": code}, name="two_factor_verify_setup")
        self.secret = secret
        self.recovery_codes = verify.json()["recovery_codes"]
        self.client.get("/logout")

    def _ensure_recovery_codes(self):
        if self.recovery_codes:
            return
        self._complete_login_via_totp()
        regenerate = self.client.post("/2fa/recovery/regenerate", name="two_factor_recovery_regenerate")
        if regenerate.status_code == 200:
            self.recovery_codes = regenerate.json()["recovery_codes"]
        else:
            print(f"Unable to regenerate recovery codes: {regenerate.status_code}")
            self.recovery_codes = []
        self.client.get("/logout")

    @task
    def login_endpoint_requires_two_factor(self):
        token = self._start_two_factor_challenge()
        if not token:
            raise AssertionError("Missing two-factor token in challenge")

    @task
    def totp_verification_endpoint(self):
        token = self._start_two_factor_challenge()
        code = pyotp.TOTP(self.secret).now()
        response = self._verify_via_api({"token": token, "code": code})
        if response.status_code != 200:
            print(f"TOTP verification failed: {response.status_code}")
        self.client.get("/logout")

    @task
    def recovery_code_verification(self):
        self._ensure_recovery_codes()
        token = self._start_two_factor_challenge()
        code = self.recovery_codes.pop()
        response = self._verify_via_api({"token": token, "recovery_code": code})
        if response.status_code != 200:
            print(f"Recovery code verification failed: {response.status_code}")
        self.client.get("/logout")

    @task
    def setup_endpoints_under_load(self):
        self._complete_login_via_totp()
        setup = self.client.post("/2fa/setup", name="two_factor_setup_under_load")
        secret = setup.json()["secret"]
        code = pyotp.TOTP(secret).now()
        verify = self.client.post("/2fa/verify-setup", json={"code": code}, name="two_factor_verify_setup_under_load")
        if verify.status_code == 200:
            self.secret = secret
            self.recovery_codes = verify.json()["recovery_codes"]
        self.client.get("/logout")


class TwoFactorPerformanceUser(HttpUser):
    tasks = [TwoFactorFlow]
    min_wait = 3000
    max_wait = 6000
    host = get_host_for_locust_testing()
