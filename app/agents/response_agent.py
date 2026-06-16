# app/agents/response_agent.py
from langfuse import observe
import json
from app.tools.email_tool import send_email


def extract_message(worker_result: str) -> str:
    """
    Extract message from worker agent JSON result.
    """
    try:
        # Remove markdown if present
        text = worker_result.strip()
        if "```json" in text:
            text = text.split("```json")[1]
            text = text.split("```")[0]

        result_dict = json.loads(text.strip())
        return result_dict.get(
            "message",
            worker_result
        )
    except:
        return worker_result

@observe
def send_response(
    parsed_email: dict,
    worker_result: str
) -> bool:
    """
    Sends professional reply to customer.

    INPUT:
    → parsed_email: original email details
    → worker_result: JSON from worker agent

    OUTPUT:
    → True if sent ✅
    → False if failed ❌
    """

    # Extract professional message
    message = extract_message(worker_result)

    # Add BT signature
    full_message = f"""Dear Customer,

{message}

Best regards,
BT Customer Service Team
━━━━━━━━━━━━━━━━━━━━━━
BT Group plc
Phone: 0800-800-150
Email: support@bt.com
━━━━━━━━━━━━━━━━━━━━━━
This is an automated response.
For urgent issues call 0800-800-150
"""

    # Send email
    result = send_email(
        to=parsed_email['sender'],
        subject=f"Re: {parsed_email['subject']}",
        body=full_message
    )

    if result:
        print(f"Reply sent to {parsed_email['sender']} ✅")
    else:
        print(f"Failed to send reply ❌")

    return result


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":

    test_parsed = {
        "sender": "haristerz97@gmail.com",
        "subject": "Invoice not received"
    }

    test_worker_result = '''```json
{
    "found": true,
    "invoice_number": "INV-2026-03-001",
    "amount": "£50.00",
    "date": "March 1, 2026",
    "message": "Good news! Your March 2026 invoice INV-2026-03-001 for £50.00 has been located."
}```'''

    print("Testing Response Agent...")
    result = send_response(
        test_parsed,
        test_worker_result
    )
    print(f"Result: {result}")