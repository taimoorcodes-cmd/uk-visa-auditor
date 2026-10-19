"""Email verification with a 6-digit code."""
import re
import secrets
import smtplib
from email.message import EmailMessage

from . import config, db

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match((email or "").strip()))


def smtp_ready() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD)


def _send_mail(to: str, code: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Your UK Visa Auditor code"
    msg["From"] = config.SMTP_FROM
    msg["To"] = to
    msg.set_content(
        f"Your code is: {code}\n\n"
        f"It works for {config.OTP_MINUTES} minutes. If you did not ask for it, ignore this email."
    )
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(msg)


def send_code(email: str):
    """Returns (ok, message, dev_code). dev_code is only set in test mode (DEV_SHOW_CODE=1)."""
    email = (email or "").strip().lower()
    if not valid_email(email):
        return False, "Please enter a correct email address.", None
    wait = db.seconds_until_resend(email)
    if wait > 0:
        return False, f"Please wait {wait} seconds before asking for a new code.", None

    code = f"{secrets.randbelow(1_000_000):06d}"
    if smtp_ready():
        try:
            _send_mail(email, code)
        except Exception:
            return False, "We could not send the email. Please try again in a few minutes.", None
        db.store_otp(email, code)
        return True, "We sent a 6-digit code to your email.", None

    if config.DEV_SHOW_CODE:
        db.store_otp(email, code)
        return True, "Test mode: email is not set up, so the code is shown on screen.", code

    return False, "Email sending is not set up yet. Add the SMTP settings to your .env file.", None