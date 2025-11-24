import os, smtplib, ssl
from email.message import EmailMessage
import certifi

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER or "")
EMAIL_TO   = os.getenv("EMAIL_TO", "")

def send_deal_email(subject: str, body: str) -> dict:
    """Send a plaintext email. Returns {ok: bool, error: str|None}."""
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS and EMAIL_FROM and EMAIL_TO):
        return {"ok": False, "error": "Missing SMTP/EMAIL_* env vars"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content(body)

    try:
        # Use certifi CA bundle for macOS/Python SSL trust
        context = ssl.create_default_context(cafile=certifi.where())
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as s:
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.ehlo()
                s.starttls(context=context)
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        return {"ok": True, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}
