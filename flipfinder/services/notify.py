import os, smtplib
from email.message import EmailMessage

GMAIL_USER = os.getenv("SMTP_USER") or os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("SMTP_PASS") or os.getenv("GMAIL_APP_PASSWORD")
TO_EMAIL   = os.getenv("DEAL_TO_EMAIL") or GMAIL_USER

def email_deal(listing_id: int, comp: dict) -> None:
    # Skip silently if not configured
    if not (GMAIL_USER and GMAIL_PASS and TO_EMAIL):
        return

    subj = f"[FlipFinder] Potential deal — ID {listing_id}"
    body = (
        f"Listing ID: {listing_id}\n"
        f"Estimated Profit: {comp.get('estimated_profit')}\n"
        f"ROI: {comp.get('roi')}\n"
        f"Asking: {comp.get('asking_price')}\n"
        f"Source URL: {comp.get('source_url') or comp.get('url')}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subj
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
