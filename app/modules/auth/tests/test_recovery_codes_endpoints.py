import pyotp
import pytest

from app import db
from app.modules.auth.models import User, UserTwoFactorRecoveryCode
from app.modules.auth.services import AuthenticationService
from app.modules.profile.models import UserProfile


def _create_user(app, email: str, password: str = "secret1234"):
    with app.app_context():
        AuthenticationService().create_with_profile(
            name="Test",
            surname="User",
            email=email,
            password=password,
        )
    return password


def _login(test_client, email: str, password: str):
    resp = test_client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)


def _reset_auth_tables(app):
    with app.app_context():
        db.session.query(UserTwoFactorRecoveryCode).delete()
        db.session.query(UserProfile).delete()
        db.session.query(User).delete()
        db.session.commit()


@pytest.fixture(autouse=True)
def set_two_factor_key(monkeypatch):
    monkeypatch.setenv("TWO_FACTOR_ENCRYPTION_KEY", "test-two-factor-key")


def test_setup_endpoint_generates_secret(test_app, test_client):
    _reset_auth_tables(test_app)
    email = "endpoint-setup@example.com"
    password = _create_user(test_app, email)
    _login(test_client, email, password)

    resp = test_client.post("/2fa/setup")
    assert resp.status_code == 200

    data = resp.get_json()
    assert "secret" in data and data["secret"]
    assert "otpauth_url" in data and data["otpauth_url"].startswith("otpauth://totp")
    assert "qr_code" in data and data["qr_code"].startswith("data:image/png;base64,")

    with test_app.app_context():
        user = AuthenticationService().repository.get_by_email(email)
        assert user.two_factor_secret is not None
        assert user.two_factor_enabled is False


def test_recovery_code_flow_via_endpoints(test_app, test_client):
    _reset_auth_tables(test_app)
    email = "endpoint-flow@example.com"
    password = _create_user(test_app, email)
    _login(test_client, email, password)

    setup_resp = test_client.post("/2fa/setup")
    assert setup_resp.status_code == 200
    setup = setup_resp.get_json()
    totp_code = pyotp.TOTP(setup["secret"]).now()

    verify_resp = test_client.post("/2fa/verify-setup", json={"code": totp_code})
    assert verify_resp.status_code == 200
    payload = verify_resp.get_json()
    recovery_codes = payload["recovery_codes"]
    assert len(recovery_codes) == 8

    resp = test_client.post("/2fa/recovery/verify", json={"code": recovery_codes[0]})
    assert resp.status_code == 200

    resp = test_client.post("/2fa/recovery/verify", json={"code": recovery_codes[0]})
    assert resp.status_code == 400

    regen_resp = test_client.post("/2fa/recovery/regenerate")
    assert regen_resp.status_code == 200
    new_codes = regen_resp.get_json()["recovery_codes"]
    assert len(new_codes) == 8
    assert new_codes != recovery_codes

    resp = test_client.post("/2fa/recovery/verify", json={"code": new_codes[0]})
    assert resp.status_code == 200

    with test_app.app_context():
        user = AuthenticationService().repository.get_by_email(email)
        assert user.two_factor_enabled is True
