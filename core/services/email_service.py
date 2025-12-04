import logging
import smtplib
import ssl
from email.message import EmailMessage
from html import unescape
from typing import Iterable, List, Optional

from flask import current_app

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.logger = logger

    def send_email(
        self,
        subject: str,
        recipients: List[str],
        html_body: str,
        text_body: Optional[str] = None,
    ) -> None:
        """Send an email using SMTP configuration from Flask config."""
        if not recipients:
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = current_app.config.get("MAIL_DEFAULT_SENDER")
        msg["To"] = ", ".join(self._clean_recipients(recipients))

        if text_body:
            msg.set_content(text_body)
        else:
            msg.set_content(self._fallback_text(html_body))

        msg.add_alternative(html_body, subtype="html")

        try:
            self._deliver(msg)
        except Exception:
            self.logger.exception("Failed to send email to %s", recipients)

    def _deliver(self, msg: EmailMessage) -> None:
        server = current_app.config.get("MAIL_SERVER")
        port = current_app.config.get("MAIL_PORT")
        username = current_app.config.get("MAIL_USERNAME")
        password = current_app.config.get("MAIL_PASSWORD")
        use_tls = current_app.config.get("MAIL_USE_TLS", True)
        use_ssl = current_app.config.get("MAIL_USE_SSL", False)

        if not server or not port:
            self.logger.warning("Mail server configuration missing; skipping email delivery.")
            return

        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(server, port, context=context) as smtp:
                self._login_if_needed(smtp, username, password)
                smtp.send_message(msg)
            return

        with smtplib.SMTP(server, port) as smtp:
            if use_tls:
                smtp.starttls(context=ssl.create_default_context())
            self._login_if_needed(smtp, username, password)
            smtp.send_message(msg)

    @staticmethod
    def _login_if_needed(smtp: smtplib.SMTP, username: Optional[str], password: Optional[str]) -> None:
        if username and password:
            smtp.login(username, password)

    @staticmethod
    def _fallback_text(html_body: str) -> str:
        """Very simple fallback: strip tags and unescape."""
        text = []
        skip = False
        for char in html_body:
            if char == "<":
                skip = True
            elif char == ">":
                skip = False
                continue
            if not skip:
                text.append(char)
        return unescape("".join(text))

    @staticmethod
    def _clean_recipients(recipients: Iterable[str]) -> list[str]:
        return [r.strip() for r in recipients if r and r.strip()]


email_service = EmailService()
