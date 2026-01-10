"""Mailer helper with SMTP backend or console fallback for local/dev use."""
import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587)) if os.environ.get('SMTP_PORT') else None
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'no-reply@ricai.com')


def send_email(to_address: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg['From'] = EMAIL_FROM
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.set_content(body)

    if SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS:
        # Try SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    else:
        # Fallback: print to console (or store file) to make testing possible
        # This is intentionally simple for local development; in production configure SMTP.
        print(f"--- Sending email to {to_address} ---")
        print("Subject:", subject)
        print(body)
        print("--- end email ---")
