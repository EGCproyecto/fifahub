from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()


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
    if request.method == "POST" and form.validate_on_submit():
        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for("public.index"))

        return render_template("auth/login_form.html", form=form, error="Invalid credentials")

    return render_template("auth/login_form.html", form=form)


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
