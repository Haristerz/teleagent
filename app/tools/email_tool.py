# app/tools/email_tool.py

import imaplib
import smtplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.header import decode_header
from email import encoders
from typing import List, Optional
from app.core.config import settings

# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT   = 993
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587


# ─────────────────────────────────────────
# HELPER — Decode Subject
# ─────────────────────────────────────────

def decode_subject(subject: str) -> str:
    """
    Decodes encoded email subjects.
    Example:
    =?UTF-8?q?Hello?= → Hello
    """
    if not subject:
        return "No Subject"

    decoded = decode_header(subject)
    parts = []
    for part, encoding in decoded:
        if isinstance(part, bytes):
            parts.append(
                part.decode(
                    encoding or "utf-8",
                    errors="ignore"
                )
            )
        else:
            parts.append(str(part))
    return " ".join(parts)


# ─────────────────────────────────────────
# HELPER — Extract Plain Text Body
# ─────────────────────────────────────────

def extract_body(msg) -> str:
    """
    Extracts plain text from email.
    Handles both simple and multipart emails.
    """
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(
                    decode=True
                ).decode("utf-8", errors="ignore")
                break
    else:
        body = msg.get_payload(
            decode=True
        ).decode("utf-8", errors="ignore")

    return body.strip()


# ─────────────────────────────────────────
# FUNCTION 1 — Read Unread Emails
# ─────────────────────────────────────────

def read_unread_emails(max_emails: int = 10) -> List[dict]:
    """
    Reads unread emails from Gmail inbox.

    INPUT  → max_emails: how many to fetch
    OUTPUT → list of email dicts
    """

    emails = []

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

        # Login
        mail.login(
            settings.gmail_user,
            settings.gmail_password
        )
        print("Connected to Gmail ✅")

        # Open inbox
        mail.select("INBOX")

        # Search unread emails only
        status, messages = mail.search(None, "UNSEEN")

        # Get list of email IDs
        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} unread emails")

        # Take only last N emails
        email_ids = email_ids[-max_emails:]

        # Loop through each email
        for email_id in email_ids:

            # Fetch full email content
            status, msg_data = mail.fetch(
                email_id, "(RFC822)"
            )

            # Parse raw bytes to email object
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract all details
            # Fix sender decoding
            sender = decode_subject(msg["From"] or "")
            subject = decode_subject(msg["Subject"])
            date    = msg["Date"] or ""
            # Fix HTML body
            body = extract_body(msg)
            if body.startswith("<!DOCTYPE") or body.startswith("<html"):
                body = "HTML email - content not extracted"

            # Add to list
            emails.append({
                "id":      email_id.decode(),
                "sender":  sender,
                "subject": subject,
                "body":    body,
                "date":    date
            })

        # Logout safely
        mail.logout()
        print(f"Fetched {len(emails)} emails ✅")
        return emails

    except Exception as e:
        print(f"Error reading emails: {e}")
        return []


# ─────────────────────────────────────────
# FUNCTION 2 — Send Reply Email
# ─────────────────────────────────────────

def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None
) -> bool:
    """
    Sends email reply to customer.

    INPUT:
    → to          : customer email
    → subject     : email subject
    → body        : email body text
    → attachments : list of file paths

    OUTPUT:
    → True if sent ✅
    → False if failed ❌
    """

    try:
        # Create email container
        msg = MIMEMultipart()
        msg["From"]    = settings.gmail_user
        msg["To"]      = to
        msg["Subject"] = subject

        # Add body text
        msg.attach(MIMEText(body, "plain"))

        # Add attachments if any
        if attachments:
            for file_path in attachments:
                with open(file_path, "rb") as f:
                    part = MIMEBase(
                        "application",
                        "octet-stream"
                    )
                    part.set_payload(f.read())

                encoders.encode_base64(part)
                filename = os.path.basename(file_path)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename}"
                )
                msg.attach(part)

        # Connect to Gmail SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

        # Start secure connection
        server.starttls()

        # Login
        server.login(
            settings.gmail_user,
            settings.gmail_password
        )

        # Send email
        server.sendmail(
            settings.gmail_user,
            to,
            msg.as_string()
        )

        # Close connection
        server.quit()

        print(f"Email sent to {to} ✅")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# ─────────────────────────────────────────
# FUNCTION 3 — Mark Email as Read
# ─────────────────────────────────────────

def mark_as_read(email_id: str) -> bool:
    """
    Marks email as read after processing.
    So we don't process same email twice.
    """

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(
            settings.gmail_user,
            settings.gmail_password
        )
        mail.select("INBOX")

        # +FLAGS (\Seen) = mark as read
        mail.store(email_id, "+FLAGS", "\\Seen")
        mail.logout()

        print(f"Email {email_id} marked as read ✅")
        return True

    except Exception as e:
        print(f"Error marking email: {e}")
        return False


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("Testing email_tool.py...")

    # Test 1 - Reading emails
    print("\n--- TEST 1: Reading emails ---")
    emails = read_unread_emails(max_emails=2)
    for e in emails:
        print(f"From:    {e['sender']}")
        print(f"Subject: {e['subject']}")
        print(f"Date:    {e['date']}")
        print(f"Body:    {e['body'][:100]}...")
        print("---")

    # Test 2 - Sending email
    print("\n--- TEST 2: Sending email ---")
    result = send_email(
        to="haristerz97@gmail.com",
        subject="Test from TeleAgent",
        body="Hello! This is a test from BT Project TeleAgent system."
    )
    print(f"Send result: {result}")