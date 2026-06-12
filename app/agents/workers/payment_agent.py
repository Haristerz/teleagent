

from crewai import Agent, Task, Crew, LLM

from app.core.config import settings




# app/agents/workers/payment_agent.py

PAYMENTS = {
    "BT12345": [
        {
            "payment_id": "PAY-2026-03-001",
            "amount": "£50.00",
            "date": "March 15, 2026",
            "status": "received",
            "method": "bank transfer"
        }
    ],
    "BT99999": [
        {
            "payment_id": "PAY-2026-03-002",
            "amount": "£75.00",
            "date": "March 10, 2026",
            "status": "received",
            "method": "card"
        }
    ]
}
# ─────────────────────────────────────────
# HELPER — Find Payment confirmation
# ─────────────────────────────────────────

def find_payment(account_number: str) -> list:
    """
    Finds Payment confirmation for a customer.
    In production → queries real database.
    """
    return PAYMENTS.get(account_number, [])


# ─────────────────────────────────────────
# LLM
# ─────────────────────────────────────────

llm = LLM(
    model=f"bedrock/{settings.claude_model}",
    aws_region_name=settings.aws_region
)


# ─────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────

payment_agent = Agent(
    role="Payment Confirmation Specialist",
    goal="""Check the customer payment status
            accurately and professionally.""",
    backstory="""You are a BT Payment Confirmation specialist
                 with access to payments database.
                 You help customers to confirm
                 their payment status.""",
    llm=llm,
    verbose=True
)
def payment_confirmation_task(
        parsed_email: dict,
        intent: dict
) -> Task:
    
    account = parsed_email.get('account_number','unknown')
    core_message = parsed_email.get('core_message')
    payment = find_payment(account)
    return Task(
        description=f"""
        Customer wants a confirmation on the payment.

        CUSTOMER DETAILS:
        Account Number: {account}
        Core Request: {core_message}

        AVAILABLE PAYMENT DETAILS FROM DATABASE:
        {payment}

        "Your job:
        1. Find the most relevant payment
        2. If found → return payment details
        3. If not found → say not found"

        Return ONLY this JSON:
        {{
            "found": true/false,
            "payment_id": "PAY-xxx or null",
            "amount": "amount or null",
            "date": "date or null",
            "status": "received or not found",
            "method": "bank transfer or null",
            "message": "professional message"
        }}
        """,
        expected_output="JSON with invoice details",
        agent=payment_agent
    )
    



def check_payment_status(
        parsed_email: dict,
        intent: dict
) -> str:
    
    task = payment_confirmation_task(
        parsed_email,
        intent
    )
    crew = Crew(
        agents=[payment_agent],
        tasks=[task],
        verbose=True
    )
    result = crew.kickoff()
    return str(result)



# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":

    test_parsed = {
        "sender": "haristerz97@gmail.com",
        "subject": "Confirm the payment receival",
        "core_message": "Payment of £50 made yesterday.Please confirm received.",
        "account_number": "BT12345"
    }

    test_intent = {
        "primary_intent": "Confirm the payment receival",
        "confidence": 0.98,
        "urgency": "high"
    }

    print("Testing Payment Agent...")
    result = check_payment_status(
        test_parsed,
        test_intent
    )
    print(f"\nPayment Confirmation Result:\n{result}")