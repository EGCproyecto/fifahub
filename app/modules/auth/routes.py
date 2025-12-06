import logging
import secrets
import time

from flask import jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm, TwoFactorLoginForm, TwoFactorRecoveryForm
from app.modules.auth.services import AuthenticationService, FollowService
from app.modules.dataset.models import Author
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
follow_service = FollowService()
logger = logging.getLogger(__name__)

PENDING_TWO_FACTOR_SESSION_KEY = "pending_two_factor_login"
PENDING_TWO_FACTOR_MAX_AGE = 300
PENDING_TWO_FACTOR_MAX_ATTEMPTS = 5
TWO_FACTOR_PROMPT = "Enter the 6-digit code from your authenticator app."


def _get_pending_two_factor():
    pending = session.get(PENDING_TWO_FACTOR_SESSION_KEY)
    if not pending:
        return None, None
    user = authentication_service.repository.get_by_id(pending.get("user_id"))
    if not user:
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        return None, None
    if time.time() - pending.get("created_at", 0) > PENDING_TWO_FACTOR_MAX_AGE:
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        return None, None
    return pending, user


def _increment_two_factor_attempts(pending: dict | None):
    if not pending:
        return 0, True
    attempts = pending.get("attempts", 0) + 1
    locked = attempts >= PENDING_TWO_FACTOR_MAX_ATTEMPTS
    if locked:
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
    else:
        pending["attempts"] = attempts
        session[PENDING_TWO_FACTOR_SESSION_KEY] = pending
    return attempts, locked


def _render_two_factor_challenge(
    totp_form: TwoFactorLoginForm,
    recovery_form: TwoFactorRecoveryForm,
    email: str,
    message: str = TWO_FACTOR_PROMPT,
    error: str | None = None,
    recovery_error: str | None = None,
    locked: bool = False,
):
    return render_template(
        "auth/two_factor_challenge.html",
        two_factor_form=totp_form,
        recovery_form=recovery_form,
        two_factor_email=email,
        two_factor_message=message,
        error=error,
        recovery_error=recovery_error,
        locked=locked,
    )


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        # Log user
        login_user(user, remember=True)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    two_factor_form = TwoFactorLoginForm()
    recovery_form = TwoFactorRecoveryForm()
    if request.method == "POST" and form.validate_on_submit():
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        result = authentication_service.login(
            form.email.data,
            form.password.data,
            remember=form.remember_me.data,
        )
        if result["status"] == "authenticated":
            return redirect(url_for("public.index"))

        if result["status"] == "two_factor_required":
            token = secrets.token_urlsafe(32)
            session[PENDING_TWO_FACTOR_SESSION_KEY] = {
                "user_id": result["user"].id,
                "token": token,
                "remember": bool(form.remember_me.data),
                "created_at": time.time(),
                "attempts": 0,
            }
            two_factor_form.token.data = token
            recovery_form.token.data = token
            return _render_two_factor_challenge(
                two_factor_form,
                recovery_form,
                result["user"].email,
                TWO_FACTOR_PROMPT,
            )

        return render_template(
            "auth/login_form.html", form=form, error="Invalid credentials", two_factor_form=two_factor_form
        )

    pending, pending_user = _get_pending_two_factor()
    if pending and pending_user:
        two_factor_form.token.data = pending.get("token")
        recovery_form.token.data = pending.get("token")
        return _render_two_factor_challenge(
            two_factor_form,
            recovery_form,
            pending_user.email,
            TWO_FACTOR_PROMPT,
        )

    return render_template("auth/login_form.html", form=form, two_factor_form=two_factor_form)


@auth_bp.route("/login/2fa", methods=["POST"])
def login_two_factor():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    pending, pending_user = _get_pending_two_factor()
    if not pending or not pending_user:
        logger.warning("2FA verification attempted without pending session")
        return redirect(url_for("auth.login"))

    totp_form = TwoFactorLoginForm()
    recovery_form = TwoFactorRecoveryForm()
    use_recovery = "recovery_code" in request.form
    active_form = recovery_form if use_recovery else totp_form

    if not active_form.validate_on_submit():
        totp_form.token.data = pending.get("token")
        recovery_form.token.data = pending.get("token")
        return _render_two_factor_challenge(
            totp_form,
            recovery_form,
            pending_user.email,
            TWO_FACTOR_PROMPT,
            error="Código inválido" if not use_recovery else None,
            recovery_error="Código inválido" if use_recovery else None,
        )

    if active_form.token.data != pending.get("token"):
        logger.warning("2FA token mismatch for user %s", pending_user.id)
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        return redirect(url_for("auth.login"))

    if time.time() - pending.get("created_at", 0) > PENDING_TWO_FACTOR_MAX_AGE:
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        return render_template(
            "auth/login_form.html",
            form=LoginForm(),
            two_factor_form=TwoFactorLoginForm(),
            error="Two-factor session expired. Please login again.",
        )

    try:
        if use_recovery:
            authentication_service.use_recovery_code(pending_user, recovery_form.recovery_code.data)
            login_user(pending_user, remember=pending.get("remember", False))
        else:
            authentication_service.complete_two_factor_login(
                pending_user,
                totp_form.code.data,
                remember=pending.get("remember", False),
            )
    except ValueError as exc:
        attempts, locked = _increment_two_factor_attempts(pending)
        if locked:
            challenge_totp = TwoFactorLoginForm()
            challenge_recovery = TwoFactorRecoveryForm()
            session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        else:
            challenge_totp = totp_form
            challenge_recovery = recovery_form
            challenge_totp.token.data = pending.get("token")
            challenge_recovery.token.data = pending.get("token")
        message = "Too many invalid codes. Please login again." if locked else str(exc)
        return _render_two_factor_challenge(
            challenge_totp,
            challenge_recovery,
            pending_user.email,
            TWO_FACTOR_PROMPT,
            error=message if not use_recovery else None,
            recovery_error=message if use_recovery else None,
            locked=locked,
        )

    session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
    return redirect(url_for("public.index"))


@auth_bp.route("/auth/2fa/verify", methods=["POST"])
def verify_two_factor_api():
    if current_user.is_authenticated:
        return jsonify({"message": "Already authenticated"}), 400

    pending, pending_user = _get_pending_two_factor()
    if not pending or not pending_user:
        return jsonify({"message": "No pending 2FA challenge"}), 400

    payload = request.get_json(silent=True) or {}
    token = (payload.get("token") or "").strip()
    if not token or token != pending.get("token"):
        logger.warning("Invalid 2FA token via API for user %s", pending_user.id)
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        return jsonify({"message": "Invalid or expired 2FA session"}), 400

    recovery_code = (payload.get("recovery_code") or "").strip()
    totp_code = (payload.get("totp_code") or payload.get("code") or "").strip()

    def _error_response(message, status=400):
        return jsonify({"message": message}), status

    if recovery_code:
        try:
            authentication_service.use_recovery_code(pending_user, recovery_code)
            login_user(pending_user, remember=pending.get("remember", False))
        except ValueError as exc:
            attempts, locked = _increment_two_factor_attempts(pending)
            message = "Too many invalid codes. Please login again." if locked else str(exc)
            return jsonify({"message": message, "locked": locked, "attempts": attempts}), 429 if locked else 400
        except Exception:
            attempts, locked = _increment_two_factor_attempts(pending)
            logger.exception("Unexpected error verifying recovery code for user %s", pending_user.id)
            return (
                jsonify(
                    {
                        "message": "Unable to verify recovery code",
                        "locked": locked,
                        "attempts": attempts,
                    }
                ),
                500 if not locked else 429,
            )
        session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
        return jsonify({"message": "2FA verified", "method": "recovery"}), 200

    if not totp_code:
        return _error_response("Code is required")

    try:
        authentication_service.complete_two_factor_login(
            pending_user,
            totp_code,
            remember=pending.get("remember", False),
        )
    except ValueError as exc:
        attempts, locked = _increment_two_factor_attempts(pending)
        message = "Too many invalid codes. Please login again." if locked else str(exc)
        return jsonify({"message": message, "locked": locked, "attempts": attempts}), 429 if locked else 400
    except Exception:
        attempts, locked = _increment_two_factor_attempts(pending)
        logger.exception("Unexpected error verifying TOTP code for user %s", pending_user.id)
        return (
            jsonify(
                {
                    "message": "Unable to verify 2FA code",
                    "locked": locked,
                    "attempts": attempts,
                }
            ),
            500 if not locked else 429,
        )

    session.pop(PENDING_TWO_FACTOR_SESSION_KEY, None)
    return jsonify({"message": "2FA verified", "method": "totp"}), 200


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))


@auth_bp.route("/2fa/settings", methods=["GET"])
@login_required
def two_factor_settings():
    return render_template("auth/two_factor_setup.html")


@auth_bp.route("/2fa/setup", methods=["POST"])
@login_required
def two_factor_setup():
    try:
        data = authentication_service.generate_two_factor_setup(current_user)
    except Exception:
        return jsonify({"message": "Unable to generate 2FA setup"}), 500
    return jsonify(data)


@auth_bp.route("/2fa/verify-setup", methods=["POST"])
@login_required
def verify_two_factor_setup():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    try:
        codes = authentication_service.verify_two_factor_setup(current_user, code)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        return jsonify({"message": "Unable to verify 2FA setup"}), 500
    return jsonify({"recovery_codes": codes})


@auth_bp.route("/2fa/recovery/regenerate", methods=["POST"])
@login_required
def regenerate_recovery_codes():
    try:
        codes = authentication_service.regenerate_recovery_codes(current_user)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        return jsonify({"message": "Unable to regenerate recovery codes"}), 500
    return jsonify({"recovery_codes": codes})


@auth_bp.route("/2fa/recovery/verify", methods=["POST"])
@login_required
def verify_recovery_code():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    try:
        authentication_service.use_recovery_code(current_user, code)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        return jsonify({"message": "Unable to verify recovery code"}), 500
    return jsonify({"message": "Recovery code accepted"})


@auth_bp.route("/2fa/disable", methods=["POST"])
@login_required
def disable_two_factor():
    payload = request.get_json(silent=True) or {}
    password = (payload.get("password") or "").strip()
    totp_code = (payload.get("code") or payload.get("totp_code") or "").strip()
    try:
        method = authentication_service.disable_two_factor(
            current_user,
            password=password,
            totp_code=totp_code,
        )
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        logger.exception("Unable to disable 2FA for user %s", current_user.id)
        return jsonify({"message": "Unable to disable 2FA"}), 500
    logger.info("User %s disabled 2FA using %s verification", current_user.id, method)
    return jsonify({"message": "Two-factor authentication disabled", "method": method})


@auth_bp.route("/follow/author/<int:author_id>", methods=["POST"])
@login_required
def follow_author(author_id: int):
    author = Author.query.get(author_id)
    if author is None:
        return jsonify({"message": "Author not found"}), 404

    try:
        follow = follow_service.follow_author(current_user, author)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        logger.exception("Error while following author")
        return jsonify({"message": "Unable to follow author"}), 500

    return jsonify({"message": "Author followed", "author_id": author.id, "follow_id": follow.id}), 200


@auth_bp.route("/unfollow/author/<int:author_id>", methods=["POST"])
@login_required
def unfollow_author(author_id: int):
    author = Author.query.get(author_id)
    if author is None:
        return jsonify({"message": "Author not found"}), 404

    try:
        removed = follow_service.unfollow_author(current_user, author)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        logger.exception("Error while unfollowing author")
        return jsonify({"message": "Unable to unfollow author"}), 500

    if not removed:
        return jsonify({"message": "Author was not followed", "author_id": author.id}), 200

    return jsonify({"message": "Author unfollowed", "author_id": author.id}), 200


@auth_bp.route("/follow/community/<string:community_id>", methods=["POST"])
@login_required
def follow_community(community_id: str):
    community_id = (community_id or "").strip()
    if not community_id:
        return jsonify({"message": "Community identifier is required"}), 400

    try:
        follow = follow_service.follow_community(current_user, community_id)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        logger.exception("Error while following community")
        return jsonify({"message": "Unable to follow community"}), 500

    return (
        jsonify(
            {
                "message": "Community followed",
                "community_id": follow.community_id,
                "follow_id": follow.id,
            }
        ),
        200,
    )


@auth_bp.route("/unfollow/community/<string:community_id>", methods=["POST"])
@login_required
def unfollow_community(community_id: str):
    community_id = (community_id or "").strip()
    if not community_id:
        return jsonify({"message": "Community identifier is required"}), 400

    try:
        removed = follow_service.unfollow_community(current_user, community_id)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        logger.exception("Error while unfollowing community")
        return jsonify({"message": "Unable to unfollow community"}), 500

    if not removed:
        return jsonify({"message": "Community was not followed", "community_id": community_id}), 200

    return jsonify({"message": "Community unfollowed", "community_id": community_id}), 200
