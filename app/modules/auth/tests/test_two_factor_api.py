import pyotp
import pytest

from app.modules.auth.services import AuthenticationService

PENDING_SESSION_KEY = "pending_two_factor_login"


def _create_two_factor_user(app, email: str):
    with app.app_context():
        service = AuthenticationService()
        user = service.create_with_profile(name="Foo", surname="Bar", email=email, password="secret123")
        setup = service.generate_two_factor_setup(user)
        totp = pyotp.TOTP(setup["secret"])
        recovery_codes = service.verify_two_factor_setup(user, totp.now())
        return {"email": user.email, "secret": setup["secret"], "recovery_codes": recovery_codes}


@pytest.fixture(autouse=True)
def set_two_factor_key(monkeypatch):
    monkeypatch.setenv("TWO_FACTOR_ENCRYPTION_KEY", "test-two-factor-key")


def test_api_two_factor_totp_success(test_app, test_client, clean_database):
    user_info = _create_two_factor_user(test_app, "api-totp@example.com")

    login_resp = test_client.post(
        "/login",
        data={"email": user_info["email"], "password": "secret123"},
        follow_redirects=False,
    )
    assert login_resp.status_code == 200

    with test_client.session_transaction() as session:
        pending = session.get(PENDING_SESSION_KEY)
        assert pending is not None
        token = pending["token"]

    totp_code = pyotp.TOTP(user_info["secret"]).now()
    verify_resp = test_client.post("/auth/2fa/verify", json={"token": token, "code": totp_code})

    assert verify_resp.status_code == 200
    assert verify_resp.get_json()["method"] == "totp"

    settings_resp = test_client.get("/2fa/settings")
    assert settings_resp.status_code == 200
    test_client.get("/logout")


def test_api_two_factor_recovery_success(test_app, test_client, clean_database):
    user_info = _create_two_factor_user(test_app, "api-recovery@example.com")

    login_resp = test_client.post(
        "/login",
        data={"email": user_info["email"], "password": "secret123"},
        follow_redirects=False,
    )
    assert login_resp.status_code == 200

    with test_client.session_transaction() as session:
        token = session[PENDING_SESSION_KEY]["token"]

    recovery_code = user_info["recovery_codes"][0]
    verify_resp = test_client.post(
        "/auth/2fa/verify",
        json={"token": token, "recovery_code": recovery_code},
    )

    assert verify_resp.status_code == 200
    assert verify_resp.get_json()["method"] == "recovery"
    test_client.get("/logout")

    # Reutilizar el mismo código debe fallar
    login_resp = test_client.post(
        "/login",
        data={"email": user_info["email"], "password": "secret123"},
        follow_redirects=False,
    )
    assert login_resp.status_code == 200
    with test_client.session_transaction() as session:
        token = session[PENDING_SESSION_KEY]["token"]

    reuse_resp = test_client.post(
        "/auth/2fa/verify",
        json={"token": token, "recovery_code": recovery_code},
    )

    assert reuse_resp.status_code == 400
    assert reuse_resp.get_json()["message"]


def test_api_two_factor_invalid_code_rate_limit(test_app, test_client, clean_database):
    user_info = _create_two_factor_user(test_app, "api-totp-invalid@example.com")

    test_client.post(
        "/login",
        data={"email": user_info["email"], "password": "secret123"},
        follow_redirects=False,
    )
    with test_client.session_transaction() as session:
        token = session[PENDING_SESSION_KEY]["token"]

    for attempt in range(1, 6):
        resp = test_client.post(
            "/auth/2fa/verify",
            json={"token": token, "code": "000000"},
        )
        if attempt < 5:
            assert resp.status_code == 400
            body = resp.get_json()
            assert body["attempts"] == attempt
            assert body["locked"] is False
        else:
            assert resp.status_code == 429
            body = resp.get_json()
            assert body["locked"] is True
            assert "Too many invalid codes" in body["message"]

    resp = test_client.post("/auth/2fa/verify", json={"token": token, "code": "111111"})
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "No pending 2FA challenge"


def test_api_two_factor_invalid_token(test_app, test_client, clean_database):
    user_info = _create_two_factor_user(test_app, "api-invalid-token@example.com")

    test_client.post(
        "/login",
        data={"email": user_info["email"], "password": "secret123"},
        follow_redirects=False,
    )

    resp = test_client.post(
        "/auth/2fa/verify",
        json={"token": "wrong-token", "code": "123456"},
    )

    assert resp.status_code == 400
    assert resp.get_json()["message"] == "Invalid or expired 2FA session"


def test_api_two_factor_rate_limit_blocks_requests(test_app, test_client, clean_database):
    previous_limit = test_app.config.get("TWO_FACTOR_RATE_LIMIT", 10)
    test_app.config["TWO_FACTOR_RATE_LIMIT"] = 2
    try:
        user_info = _create_two_factor_user(test_app, "api-rate-limit@example.com")
        test_client.post("/login", data={"email": user_info["email"], "password": "secret123"}, follow_redirects=False)
        with test_client.session_transaction() as session:
            token = session[PENDING_SESSION_KEY]["token"]

        for _ in range(2):
            resp = test_client.post("/auth/2fa/verify", json={"token": token, "code": "000000"})
            assert resp.status_code == 400

        resp = test_client.post("/auth/2fa/verify", json={"token": token, "code": "000000"})
        assert resp.status_code == 429
        assert resp.get_json()["message"] == "Too many attempts. Please wait and try again."
    finally:
        test_app.config["TWO_FACTOR_RATE_LIMIT"] = previous_limit
