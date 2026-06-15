# app/services/crew.py
#
# Main orchestrator for ALL agents.
# Runs them in correct sequence.
#
# Flow:
# Email → Parser → Intent → Triage
#                               ↓
#                         Worker Agent
#                               ↓
#                         Response Agent
#                               ↓
#                         Customer Reply ✅

import json
from app.agents.email_parser import parse_email
from app.agents.intent_classifier import classify_intent
from app.agents.triage import triage_email
from app.agents.workers.invoice_agent import process_invoice_request
from app.agents.workers.payment_agent import check_payment_status
from app.agents.workers.servicenow_agent import process_dispute
from app.agents.workers.rag_agent import answer_general_query
from app.agents.response_agent import send_response


# ─────────────────────────────────────────
# HELPER — Extract JSON from agent output
# ─────────────────────────────────────────

def extract_json(text: str) -> dict:
    """
    Agents return JSON wrapped in markdown.
    This extracts clean JSON dict.
    """
    try:
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
# WORKER ROUTER
# ─────────────────────────────────────────

def run_worker_agent(
    triage: dict,
    parsed: dict,
    intent: dict
) -> str:
    """
    Routes to correct worker agent
    based on triage decision.
    """

    assigned = triage.get(
        "assigned_agent",
        "rag_agent"
    )

    print(f"\n[WORKER] Assigned to: {assigned}")

    if assigned == "invoice_agent":
        return process_invoice_request(
            parsed, intent
        )

    elif assigned == "payment_agent":
        return check_payment_status(
            parsed, intent
        )

    elif assigned == "servicenow_agent":
        return process_dispute(
            parsed, intent
        )

    else:
        # Default → RAG Agent
        return answer_general_query(
            parsed, intent
        )


# ─────────────────────────────────────────
# MAIN — Process One Email
# ─────────────────────────────────────────

def process_email(raw_email: dict) -> dict:
    """
    Full pipeline for one email.

    INPUT  → raw email dict from Gmail
    OUTPUT → complete processing result
    """

    print("\n" + "="*50)
    print("TELEAGENT PROCESSING EMAIL")
    print("="*50)
    print(f"From:    {raw_email['sender']}")
    print(f"Subject: {raw_email['subject']}")
    print("="*50)

    # ─────────────────────────────
    # STEP 1 — Parse Email
    # ─────────────────────────────
    print("\n[STEP 1] Email Parser Agent...")
    parser_result = parse_email(raw_email)

    # parse_email returns dict directly
    if isinstance(parser_result, dict):
        parsed = parser_result
    else:
        parsed = extract_json(str(parser_result))

    # Add sender info
    parsed["sender"] = raw_email["sender"]
    parsed["subject"] = raw_email["subject"]

    print(f"Core Message: {parsed.get('core_message')}")
    print(f"Account: {parsed.get('account_number')}")

    # ─────────────────────────────
    # STEP 2 — Classify Intent
    # ─────────────────────────────
    print("\n[STEP 2] Intent Classifier Agent...")
    intent_result = classify_intent(parsed)
    intent = extract_json(str(intent_result))

    print(f"Intent: {intent.get('primary_intent')}")
    print(f"Confidence: {intent.get('confidence')}")
    print(f"Urgency: {intent.get('urgency')}")

    # ─────────────────────────────
    # STEP 3 — Triage
    # ─────────────────────────────
    print("\n[STEP 3] Triage Agent...")
    triage_result = triage_email(parsed, intent)
    triage = extract_json(str(triage_result))

    print(f"Authorized: {triage.get('is_authorized')}")
    print(f"Assigned to: {triage.get('assigned_agent')}")
    print(f"Priority: {triage.get('priority')}")

    # ─────────────────────────────
    # CHECK AUTHORIZATION
    # ─────────────────────────────
    if not triage.get("is_authorized", False):
        print("\n❌ Customer not authorized!")
        send_response(
            parsed,
            json.dumps({
                "message": "We could not verify your account. Please contact BT support at 0800-800-150 with your account details."
            })
        )
        return {
            "success": False,
            "reason": "Not authorized"
        }

    # ─────────────────────────────
    # STEP 4 — Run Worker Agent
    # ─────────────────────────────
    print("\n[STEP 4] Running Worker Agent...")
    worker_result = run_worker_agent(
        triage, parsed, intent
    )
    print(f"Worker result received ✅")

    # ─────────────────────────────
    # STEP 5 — Send Response
    # ─────────────────────────────
    print("\n[STEP 5] Response Agent...")
    email_sent = send_response(
        parsed,
        str(worker_result)
    )

    # ─────────────────────────────
    # FINAL RESULT
    # ─────────────────────────────
    result = {
        "sender": raw_email["sender"],
        "subject": raw_email["subject"],
        "parsed": parsed,
        "intent": intent,
        "triage": triage,
        "worker_result": str(worker_result),
        "email_sent": email_sent,
        "overall_success": email_sent
    }

    print("\n" + "="*50)
    print("PROCESSING COMPLETE ✅")
    print(f"Email sent: {email_sent}")
    print("="*50)

    return result


# ─────────────────────────────────────────
# TEST — Full Pipeline
# ─────────────────────────────────────────

if __name__ == "__main__":

    # Test 1 — Invoice request
    print("\n🧪 TEST 1: Invoice Request")
    test_email_1 = {
        "id": "001",
        "sender": "haristerz97@gmail.com",
        "subject": "Invoice not received",
        "body": """Hi team,
        I haven't received my invoice
        for March 2026.
        My account number is BT12345.
        Please send urgently.
        Thanks""",
        "date": "2026-06-11"
    }

    result1 = process_email(test_email_1)
    print(f"\nTest 1 Success: {result1['overall_success']}")

    print("\n" + "-"*50)

    # Test 2 — Billing dispute
    print("\n🧪 TEST 2: Billing Dispute")
    test_email_2 = {
        "id": "002",
        "sender": "haristerz97@gmail.com",
        "subject": "Wrong charge on my bill",
        "body": """Hello,
        I was charged £25 extra
        on my March 2026 bill.
        Account: BT12345.
        Please investigate.""",
        "date": "2026-06-11"
    }

    result2 = process_email(test_email_2)
    print(f"\nTest 2 Success: {result2['overall_success']}")

    print("\n" + "-"*50)

    # Test 3 — General query
    print("\n🧪 TEST 3: General Query")
    test_email_3 = {
        "id": "003",
        "sender": "haristerz97@gmail.com",
        "subject": "Data allowance question",
        "body": """Hi,
        What is my data allowance
        on BT Unlimited plan?
        Account: BT12345""",
        "date": "2026-06-11"
    }

    result3 = process_email(test_email_3)
    print(f"\nTest 3 Success: {result3['overall_success']}")