import time

import pyotp
import pytest
from flask import url_for

from app.modules.auth.routes import PENDING_TWO_FACTOR_SESSION_KEY, PENDING_TWO_FACTOR_MAX_AGE
from app.modules.auth.services import AuthenticationService

PENDING_SESSION_KEY = "pending_two_factor_login"


@pytest.fixture(autouse=True)
def set_two_factor_key(monkeypatch):
    monkeypatch.setenv("TWO_FACTOR_ENCRYPTION_KEY", "test-two-factor-key")


def _prepare_two_factor_user(app, email: str):
    with app.app_context():
        service = AuthenticationService()
        user = service.create_with_profile(name="Foo", surname="Bar", email=email, password="secret123")
        setup = service.generate_two_factor_setup(user)
        totp = pyotp.TOTP(setup["secret"])
        service.verify_two_factor_setup(user, totp.now())
        return setup["secret"], user.email


def test_login_requires_two_factor_verification(test_app, test_client, clean_database):
    secret, email = _prepare_two_factor_user(test_app, "login-2fa@example.com")

    response = test_client.post(
        "/login",
        data={"email": email, "password": "secret123"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"Two-Factor Authentication" in response.data

    with test_client.session_transaction() as session:
        pending = session.get(PENDING_SESSION_KEY)
        assert pending is not None
        token = pending["token"]

    code = pyotp.TOTP(secret).now()
    verify = test_client.post(
        "/login/2fa",
        data={"token": token, "code": code},
        follow_redirects=False,
    )

    assert verify.status_code in (302, 303)
    assert verify.headers["Location"].endswith(url_for("public.index"))
    test_client.get("/logout", follow_redirects=True)


def test_login_two_factor_invalid_code_keeps_challenge(test_app, test_client, clean_database):
    secret, email = _prepare_two_factor_user(test_app, "login-2fa-invalid@example.com")

    response = test_client.post(
        "/login",
        data={"email": email, "password": "secret123"},
        follow_redirects=False,
    )

    assert response.status_code == 200

    with test_client.session_transaction() as session:
        pending = session.get(PENDING_SESSION_KEY)
        token = pending["token"]

    verify = test_client.post(
        "/login/2fa",
        data={"token": token, "code": "000000"},
        follow_redirects=False,
    )

    assert verify.status_code == 200
    assert b"Unable to verify the authentication code." in verify.data

    with test_client.session_transaction() as session:
        pending = session.get(PENDING_SESSION_KEY)
        assert pending is not None
        assert pending["attempts"] == 1

    code = pyotp.TOTP(secret).now()
    verify = test_client.post(
        "/login/2fa",
        data={"token": token, "code": code},
        follow_redirects=False,
    )

    assert verify.status_code in (302, 303)
    test_client.get("/logout", follow_redirects=True)


def test_login_two_factor_rate_limit_blocks_requests(test_app, test_client, clean_database):
    previous_limit = test_app.config.get("TWO_FACTOR_RATE_LIMIT", 10)
    test_app.config["TWO_FACTOR_RATE_LIMIT"] = 1
    try:
        _, email = _prepare_two_factor_user(test_app, "login-2fa-rate@example.com")

        response = test_client.post(
            "/login",
            data={"email": email, "password": "secret123"},
            follow_redirects=False,
        )
        assert response.status_code == 200

        with test_client.session_transaction() as session:
            pending = session.get(PENDING_SESSION_KEY)
            token = pending["token"]

        # First invalid attempt allowed
        verify = test_client.post("/login/2fa", data={"token": token, "code": "000000"}, follow_redirects=False)
        assert verify.status_code == 200

        # Second attempt should hit rate limit independent of lock threshold
        verify = test_client.post("/login/2fa", data={"token": token, "code": "111111"}, follow_redirects=False)
        assert verify.status_code == 429
        assert b"Too many attempts. Please wait and try again." in verify.data
    finally:
        test_app.config["TWO_FACTOR_RATE_LIMIT"] = previous_limit


def test_login_two_factor_session_expired_shows_error(test_app, test_client, clean_database):
    secret, email = _prepare_two_factor_user(test_app, "login-2fa-expired@example.com")

    response = test_client.post(
        "/login",
        data={"email": email, "password": "secret123"},
        follow_redirects=False,
    )
    assert response.status_code == 200

    with test_client.session_transaction() as session:
        pending = session.get(PENDING_SESSION_KEY)
        token = pending["token"]
        pending["created_at"] = time.time() - (PENDING_TWO_FACTOR_MAX_AGE + 10)
        session[PENDING_SESSION_KEY] = pending

    verify = test_client.post("/login/2fa", data={"token": token, "code": "000000"}, follow_redirects=False)
    assert verify.status_code == 302
    assert verify.headers["Location"].endswith("/login")
    with test_client.session_transaction() as session:
        assert PENDING_SESSION_KEY not in session
