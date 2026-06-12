# app/agents/workers/invoice_agent.py

from crewai import Agent, Task, Crew, LLM
from app.core.config import settings


# ─────────────────────────────────────────
# MOCK DATABASE
# In production → real database query
# ─────────────────────────────────────────

INVOICES = {
    "BT12345": [
        {
            "invoice_number": "INV-2026-03-001",
            "month": "March 2026",
            "amount": "£50.00",
            "status": "generated",
            "date": "March 1, 2026"
        },
        {
            "invoice_number": "INV-2026-02-001",
            "month": "February 2026",
            "amount": "£45.00",
            "status": "generated",
            "date": "February 1, 2026"
        }
    ],
    "BT99999": [
        {
            "invoice_number": "INV-2026-03-002",
            "month": "March 2026",
            "amount": "£75.00",
            "status": "generated",
            "date": "March 1, 2026"
        }
    ]
}


# ─────────────────────────────────────────
# HELPER — Find Invoice
# ─────────────────────────────────────────

def find_invoice(account_number: str) -> list:
    """
    Finds invoices for a customer.
    In production → queries real database.
    """
    return INVOICES.get(account_number, [])


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

invoice_agent = Agent(
    role="Invoice Retrieval Specialist",
    goal="""Find and retrieve customer invoices
            accurately and professionally.""",
    backstory="""You are a BT billing specialist
                 with access to invoice database.
                 You help customers find their
                 missing invoices.""",
    llm=llm,
    verbose=True
)


# ─────────────────────────────────────────
# TASK
# ─────────────────────────────────────────

def create_invoice_task(
    parsed_email: dict,
    intent: dict
) -> Task:

    account = parsed_email.get(
        "account_number", "unknown"
    )
    invoices = find_invoice(account)

    return Task(
        description=f"""
        Customer needs their invoice.

        CUSTOMER DETAILS:
        Account Number: {account}
        Core Request: {parsed_email.get('core_message')}

        AVAILABLE INVOICES FROM DATABASE:
        {invoices}

        Your job:
        1. Find the most relevant invoice
        2. If found → return invoice details
        3. If not found → say not found clearly

        Return ONLY this JSON:
        {{
            "found": true/false,
            "invoice_number": "INV-xxx or null",
            "month": "month year or null",
            "amount": "amount or null",
            "date": "date or null",
            "message": "professional message to customer"
        }}
        """,
        expected_output="JSON with invoice details",
        agent=invoice_agent
    )


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def process_invoice_request(
    parsed_email: dict,
    intent: dict
) -> str:

    task = create_invoice_task(
        parsed_email,
        intent
    )

    crew = Crew(
        agents=[invoice_agent],
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
        "subject": "Invoice not received",
        "core_message": "Invoice for March 2026 not received",
        "account_number": "BT12345"
    }

    test_intent = {
        "primary_intent": "invoice_not_received",
        "confidence": 0.98,
        "urgency": "high"
    }

    print("Testing Invoice Agent...")
    result = process_invoice_request(
        test_parsed,
        test_intent
    )
    print(f"\nInvoice Result:\n{result}")