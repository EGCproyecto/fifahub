import logging

from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService, FollowService
from app.modules.dataset.models import Author
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
follow_service = FollowService()
logger = logging.getLogger(__name__)


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
