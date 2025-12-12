import pyotp
import pytest
from flask import url_for

from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.profile.repositories import UserProfileRepository
from core.services.encryption import decrypt_text


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_login_success(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="bademail@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="basspassword"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_signup_user_no_name(test_client):
    response = test_client.post(
        "/signup",
        data=dict(surname="Foo", email="test@example.com", password="test1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert b"This field is required" in response.data, response.data


def test_signup_user_unsuccessful(test_client):
    email = "test@example.com"
    response = test_client.post(
        "/signup",
        data=dict(name="Test", surname="Foo", email=email, password="test1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert f"Email {email} in use".encode("utf-8") in response.data


def test_signup_user_successful(test_client):
    response = test_client.post(
        "/signup",
        data=dict(name="Foo", surname="Example", email="foo@example.com", password="foo1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("public.index"), "Signup was unsuccessful"


def test_service_create_with_profie_success(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "service_test@example.com",
        "password": "test1234",
    }

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "test@example.com",
        "password": "",
    }

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def _prepare_user_with_two_factor(email: str):
    service = AuthenticationService()
    user = service.create_with_profile(name="Foo", surname="Bar", email=email, password="test1234")
    setup = service.generate_two_factor_setup(user)
    totp = pyotp.TOTP(setup["secret"])
    codes = service.verify_two_factor_setup(user, totp.now())
    return service, user, codes


def test_recovery_codes_generated_and_returned(test_app, clean_database):
    with test_app.app_context():
        service, user, codes = _prepare_user_with_two_factor("recover1@example.com")

        assert user.two_factor_enabled is True
        assert len(codes) == 8
        assert all(len(code) == 10 for code in codes)


def test_recovery_code_consumed_after_use(test_app, clean_database):
    with test_app.app_context():
        service, user, codes = _prepare_user_with_two_factor("recover2@example.com")

        assert service.use_recovery_code(user, codes[0]) is True
        with pytest.raises(ValueError):
            service.use_recovery_code(user, codes[0])


def test_regenerate_recovery_codes_replaces_previous(test_app, clean_database):
    with test_app.app_context():
        service, user, codes = _prepare_user_with_two_factor("recover3@example.com")

        new_codes = service.regenerate_recovery_codes(user)

        assert len(new_codes) == 8
        assert new_codes != codes
        with pytest.raises(ValueError):
            service.use_recovery_code(user, codes[0])
        assert service.use_recovery_code(user, new_codes[0]) is True


def test_regenerate_requires_enabled_two_factor(test_app, clean_database):
    with test_app.app_context():
        service = AuthenticationService()
        user = service.create_with_profile(name="Foo", surname="Bar", email="recover4@example.com", password="abc1234")

        with pytest.raises(ValueError):
            service.regenerate_recovery_codes(user)


def test_recovery_code_invalid_value(test_app, clean_database):
    with test_app.app_context():
        service, user, codes = _prepare_user_with_two_factor("recover5@example.com")

        with pytest.raises(ValueError):
            service.use_recovery_code(user, "invalid")
        assert service.use_recovery_code(user, codes[1]) is True


@pytest.fixture(autouse=True)
def set_two_factor_key(monkeypatch):
    monkeypatch.setenv("TWO_FACTOR_ENCRYPTION_KEY", "test-two-factor-key")


def test_two_factor_secret_is_encrypted(test_app, clean_database):
    with test_app.app_context():
        service = AuthenticationService()
        user = service.create_with_profile(name="Secret", surname="User", email="secret@example.com", password="secret123")
        setup = service.generate_two_factor_setup(user)
        assert user.two_factor_secret is not None
        assert user.two_factor_secret != setup["secret"]
        assert decrypt_text(user.two_factor_secret) == setup["secret"]


def test_recovery_codes_are_encrypted_at_rest(test_app, clean_database):
    with test_app.app_context():
        service, user, codes = _prepare_user_with_two_factor("recover-encrypted@example.com")
        stored_codes = [record.encrypted_code for record in user.recovery_codes]
        assert stored_codes
        for stored, plain in zip(stored_codes, codes):
            assert stored != plain
            assert decrypt_text(stored) == plain
