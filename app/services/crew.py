# app/services/crew.py
#
# Main orchestrator for all agents.
# Runs them in correct sequence.

import json
from app.agents.email_parser import parse_email
from app.agents.intent_classifier import classify_intent
from app.agents.triage import triage_email
from app.core.models import EmailProcessingResult


# ─────────────────────────────────────────
# HELPER — Parse JSON from agent output
# ─────────────────────────────────────────

def extract_json(text: str) -> dict:
    """
    Agents return JSON wrapped in markdown:
```json
    {"key": "value"}
```

    This function extracts just the JSON.
    """
    try:
        # Remove markdown code blocks
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1]
            text = text.split("```")[0]
        elif "```" in text:
            text = text.split("```")[1]
            text = text.split("```")[0]

        return json.loads(text.strip())
    except Exception as e:
        print(f"JSON parse error: {e}")
        return {}


# ─────────────────────────────────────────
# MAIN — Process One Email
# ─────────────────────────────────────────

def process_email(raw_email: dict) -> dict:
    """
    Full pipeline for processing one email.

    INPUT → raw email dict from Gmail
    OUTPUT → complete processing result
    """

    print("\n" + "="*50)
    print("PROCESSING EMAIL")
    print("="*50)
    print(f"From: {raw_email['sender']}")
    print(f"Subject: {raw_email['subject']}")

    # ─────────────────────────────
    # STEP 1 — Parse Email
    # ─────────────────────────────
    print("\n[STEP 1] Running Email Parser Agent...")
    parser_result = parse_email(raw_email)
    parsed = extract_json(parser_result)

    print(f"Core Message: {parsed.get('core_message')}")
    print(f"Account: {parsed.get('account_number')}")

    # Add sender to parsed
    parsed["sender"] = raw_email["sender"]
    parsed["subject"] = raw_email["subject"]

    # ─────────────────────────────
    # STEP 2 — Classify Intent
    # ─────────────────────────────
    print("\n[STEP 2] Running Intent Classifier Agent...")
    intent_result = classify_intent(parsed)
    intent = extract_json(intent_result)

    print(f"Intent: {intent.get('primary_intent')}")
    print(f"Confidence: {intent.get('confidence')}")
    print(f"Urgency: {intent.get('urgency')}")

    # ─────────────────────────────
    # STEP 3 — Triage
    # ─────────────────────────────
    print("\n[STEP 3] Running Triage Agent...")
    triage_result = triage_email(parsed, intent)
    triage = extract_json(triage_result)

    print(f"Authorized: {triage.get('is_authorized')}")
    print(f"Assigned to: {triage.get('assigned_agent')}")
    print(f"Priority: {triage.get('priority')}")

    # ─────────────────────────────
    # FINAL RESULT
    # ─────────────────────────────
    result = {
        "sender": raw_email["sender"],
        "subject": raw_email["subject"],
        "parsed_email": parsed,
        "intent": intent,
        "triage": triage,
        "overall_success": triage.get("is_authorized", False)
    }

    print("\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)

    return result


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":

    # Simulate a customer email
    test_email = {
        "id": "001",
        "sender": "haristerz97@gmail.com",
        "subject": "Invoice not received",
        "body": """Hi team,
        I haven't received my invoice
        for March 2026.
        My account number is BT12345.
        Please send it urgently.
        Thanks, Hari""",
        "date": "2026-06-10"
    }

    result = process_email(test_email)

    print("\n\nFINAL RESULT:")
    print(f"Sender: {result['sender']}")
    print(f"Intent: {result['intent'].get('primary_intent')}")
    print(f"Assigned to: {result['triage'].get('assigned_agent')}")
    print(f"Success: {result['overall_success']}")