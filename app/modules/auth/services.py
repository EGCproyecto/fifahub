import base64
import os
import secrets
from io import BytesIO
from typing import List

import pyotp
import qrcode
from flask_login import current_user, login_user
from sqlalchemy.exc import SQLAlchemyError

from app.modules.auth.models import User, UserFollowAuthor, UserFollowCommunity, UserTwoFactorRecoveryCode
from app.modules.auth.repositories import (
    UserFollowAuthorRepository,
    UserFollowCommunityRepository,
    UserRepository,
)
from app.modules.dataset.models import Author
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService
from core.services.encryption import InvalidToken, decrypt_text, encrypt_text


class AuthenticationService(BaseService):
    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is None or not user.check_password(password):
            return {"status": "invalid", "user": None}
        if user.two_factor_enabled:
            return {"status": "two_factor_required", "user": user}
        login_user(user, remember=remember)
        return {"status": "authenticated", "user": user}

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()
        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))

    def generate_two_factor_setup(self, user: User) -> dict:
        if user is None:
            raise ValueError("User required")
        secret = pyotp.random_base32()
        issuer = os.getenv("FLASK_APP_NAME", "FifaHub")
        totp = pyotp.TOTP(secret)
        otpauth_url = totp.provisioning_uri(name=user.email, issuer_name=issuer)
        qr_image = qrcode.make(otpauth_url)
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        qr_data = base64.b64encode(buffer.getvalue()).decode("ascii")
        user.two_factor_secret = encrypt_text(secret)
        user.two_factor_enabled = False
        self._recovery_codes_query(user).delete()
        self.repository.session.commit()
        return {
            "secret": secret,
            "otpauth_url": otpauth_url,
            "qr_code": f"data:image/png;base64,{qr_data}",
        }

    def _recovery_codes_query(self, user: User):
        return self.repository.session.query(UserTwoFactorRecoveryCode).filter_by(user_id=user.id)

    def _generate_recovery_codes(self, user: User, count: int = 8) -> list[str]:
        self._recovery_codes_query(user).delete()
        codes: list[str] = []
        for _ in range(count):
            code = secrets.token_hex(5)
            encrypted = encrypt_text(code)
            record = UserTwoFactorRecoveryCode(user_id=user.id, encrypted_code=encrypted)
            self.repository.session.add(record)
            codes.append(code)
        return codes

    def regenerate_recovery_codes(self, user: User) -> list[str]:
        if user is None:
            raise ValueError("User required")
        persisted = self.repository.get_by_id(user.id)
        if persisted is None:
            raise ValueError("User required")
        user = persisted
        if not user.two_factor_enabled:
            raise ValueError("2FA no activada")
        codes = self._generate_recovery_codes(user)
        self.repository.session.commit()
        return codes

    def use_recovery_code(self, user: User, code: str) -> bool:
        if user is None:
            raise ValueError("User required")
        candidate = (code or "").strip().lower()
        if not candidate:
            raise ValueError("Código inválido")

        records = self._recovery_codes_query(user).all()
        for record in records:
            try:
                stored = decrypt_text(record.encrypted_code).lower()
            except InvalidToken:
                continue
            if secrets.compare_digest(stored, candidate):
                self.repository.session.delete(record)
                self.repository.session.commit()
                return True

        raise ValueError("Código de recuperación inválido")

    def verify_two_factor_setup(self, user: User, code: str) -> list[str]:
        if user is None:
            raise ValueError("User required")
        trimmed = (code or "").strip()
        if len(trimmed) != 6 or not trimmed.isdigit():
            raise ValueError("Código inválido")
        secret = self._get_user_secret(user)
        totp = pyotp.TOTP(secret)
        if not totp.verify(trimmed, valid_window=1):
            raise ValueError("Código inválido")
        user.two_factor_enabled = True
        user.two_factor_secret = encrypt_text(secret)
        codes = self._generate_recovery_codes(user)
        self.repository.session.commit()
        return codes

    def complete_two_factor_login(self, user: User, code: str, remember: bool = True):
        if user is None:
            raise ValueError("User required")
        persisted = self.repository.get_by_id(user.id)
        if persisted is None:
            raise ValueError("User required")
        user = persisted
        if not user.two_factor_enabled:
            raise ValueError("2FA no activada")
        trimmed = (code or "").strip()
        if len(trimmed) != 6 or not trimmed.isdigit():
            raise ValueError("Código inválido")
        secret = self._get_user_secret(user)
        totp = pyotp.TOTP(secret)
        if not totp.verify(trimmed, valid_window=1):
            raise ValueError("Código inválido")
        login_user(user, remember=remember)
        return True

    def _get_user_secret(self, user: User) -> str:
        if not user.two_factor_secret:
            raise ValueError("No hay secreto configurado")
        try:
            return decrypt_text(user.two_factor_secret)
        except InvalidToken as exc:
            raise RuntimeError("Secreto inválido") from exc

    def disable_two_factor(self, user: User, password: str | None = None, totp_code: str | None = None) -> str:
        if user is None:
            raise ValueError("User required")
        if not user.two_factor_enabled:
            raise ValueError("2FA no activada")
        password_candidate = (password or "").strip()
        totp_candidate = (totp_code or "").strip()
        if not password_candidate and not totp_candidate:
            raise ValueError("Contraseña o código requerido")

        method_used = None
        if password_candidate:
            if not user.check_password(password_candidate):
                raise ValueError("Contraseña inválida")
            method_used = "password"
        elif totp_candidate:
            if len(totp_candidate) != 6 or not totp_candidate.isdigit():
                raise ValueError("Código inválido")
            secret = self._get_user_secret(user)
            totp = pyotp.TOTP(secret)
            if not totp.verify(totp_candidate, valid_window=1):
                raise ValueError("Código inválido")
            method_used = "totp"

        user.two_factor_enabled = False
        user.two_factor_secret = None
        self._recovery_codes_query(user).delete()
        self.repository.session.commit()
        return method_used or "totp"


class FollowService(BaseService):
    def __init__(self):
        super().__init__(UserFollowAuthorRepository())
        self.user_follow_author_repository = UserFollowAuthorRepository()
        self.user_follow_community_repository = UserFollowCommunityRepository()

    def _ensure_user(self, user: User):
        if user is None:
            raise ValueError("User is required")
        if user.id is None:
            raise ValueError("User must be persisted before using follow features")

    def _ensure_author(self, author: Author):
        if author is None:
            raise ValueError("Author is required")
        if author.id is None:
            raise ValueError("Author must be persisted before being followed")

    def _normalize_community_id(self, community) -> str:
        if community is None:
            raise ValueError("Community is required")
        if isinstance(community, str):
            return community
        community_id = getattr(community, "id", None) or getattr(community, "name", None)
        if community_id is None:
            raise ValueError("Community identifier is required")
        return str(community_id)

    def follow_author(self, user: User, author: Author) -> UserFollowAuthor:
        self._ensure_user(user)
        self._ensure_author(author)
        if user.id == getattr(author, "id", None):
            raise ValueError("Users cannot follow themselves.")
        existing = self.user_follow_author_repository.get_by_user_and_author(user.id, author.id)
        if existing is not None:
            return existing
        try:
            return self.user_follow_author_repository.create(
                user_id=user.id,
                author_id=author.id,
            )
        except SQLAlchemyError as exc:
            raise RuntimeError("Failed to follow author") from exc

    def unfollow_author(self, user: User, author: Author) -> bool:
        self._ensure_user(user)
        self._ensure_author(author)
        try:
            return self.user_follow_author_repository.delete_by_user_and_author(user.id, author.id)
        except SQLAlchemyError as exc:
            raise RuntimeError("Failed to unfollow author") from exc

    def follow_community(self, user: User, community) -> UserFollowCommunity:
        self._ensure_user(user)
        community_id = self._normalize_community_id(community)
        existing = self.user_follow_community_repository.get_by_user_and_community(user.id, community_id)
        if existing is not None:
            return existing
        try:
            return self.user_follow_community_repository.create(
                user_id=user.id,
                community_id=community_id,
            )
        except SQLAlchemyError as exc:
            raise RuntimeError("Failed to follow community") from exc

    def unfollow_community(self, user: User, community) -> bool:
        self._ensure_user(user)
        community_id = self._normalize_community_id(community)
        try:
            return self.user_follow_community_repository.delete_by_user_and_community(user.id, community_id)
        except SQLAlchemyError as exc:
            raise RuntimeError("Failed to unfollow community") from exc

    def get_followed_authors_for_user(self, user: User) -> List[Author]:
        self._ensure_user(user)
        rows = self.user_follow_author_repository.get_for_user(user.id)
        if not rows:
            return []
        author_ids = [row.author_id for row in rows]
        return Author.query.filter(Author.id.in_(author_ids)).all()

    def get_followed_communities_for_user(self, user: User) -> List[str]:
        self._ensure_user(user)
        rows = self.user_follow_community_repository.get_for_user(user.id)
        return [row.community_id for row in rows]

    def get_followers_for_author(self, author: Author) -> List[User]:
        self._ensure_author(author)
        rows = self.user_follow_author_repository.get_for_author(author.id)
        if not rows:
            return []
        user_ids = [row.user_id for row in rows]
        return User.query.filter(User.id.in_(user_ids)).all()

    def get_followers_for_community(self, community) -> List[User]:
        community_id = self._normalize_community_id(community)
        rows = self.user_follow_community_repository.get_for_community(community_id)
        if not rows:
            return []
        user_ids = [row.user_id for row in rows]
        return User.query.filter(User.id.in_(user_ids)).all()
