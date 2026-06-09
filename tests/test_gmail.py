import imaplib
from dotenv import load_dotenv
import os

load_dotenv()

def test_gmail():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(
            os.getenv("GMAIL_USER"),
            os.getenv("GMAIL_PASSWORD")
        )
        print("Gmail connected! ✅")
        mail.logout()
    except Exception as e:
        print(f"Gmail failed: {e}")

test_gmail()