import pyotp
import pytest
from flask import url_for

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
    assert "C\u00f3digo inv\u00e1lido".encode("utf-8") in verify.data

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
