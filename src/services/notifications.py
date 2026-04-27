"""Notification helpers for account confirmation emails."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import logging
import os
import smtplib

logger = logging.getLogger(__name__)

# Default logger usage notes:
# - When SMTP is not configured we log an info-level preview so developers
#   can see what would be sent without sending mail. The logger is used with
#   structured 'extra' data so log aggregation systems can index recipient/subject.


@dataclass(frozen=True)
class EmailDeliveryResult:
    sent: bool
    detail: str
    subject: str
    body: str


def send_confirmation_email(
    recipient_email: str, confirmation_message: str
) -> EmailDeliveryResult:
    """Send a confirmation email or log a preview when SMTP is not set.

    Returns an EmailDeliveryResult indicating whether the message was sent
    or only previewed in logs.
    """
    subject = "PersonalFinanceAnalyzer account confirmation"
    body = (
        f"Subject: {subject}\n\n"
        f"{confirmation_message}\n\n"
        "If you did not request this account, you can ignore this message."
    )

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from_email = os.getenv(
        "SMTP_FROM_EMAIL", smtp_username or "no-reply@personalfinanceanalyzer.local"
    )
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if not smtp_host:
        logger.info(
            "confirmation_email_preview",
            extra={"recipient": recipient_email, "subject": subject},
        )
        return EmailDeliveryResult(
            sent=False,
            detail="SMTP is not configured; confirmation email preview logged.",
            subject=subject,
            body=body,
        )

    message = EmailMessage()
    message["To"] = recipient_email
    message["From"] = smtp_from_email
    message["Subject"] = subject
    message.set_content(confirmation_message)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        if smtp_use_tls:
            server.starttls()
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)
        server.send_message(message)

    return EmailDeliveryResult(
        sent=True, detail="Confirmation email sent.", subject=subject, body=body
    )
