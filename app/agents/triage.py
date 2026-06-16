# app/agents/triage.py
from langfuse import observe
from crewai import Agent, Task, Crew, LLM
from app.core.config import settings


# ─────────────────────────────────────────
# LLM
# ─────────────────────────────────────────

llm = LLM(
    model=f"bedrock/{settings.claude_model}",
    aws_region_name=settings.aws_region,
    guardrailConfig={
        "guardrailIdentifier": settings.bedrock_guardrail_id,
        "guardrailVersion": settings.bedrock_guardrail_version,
        "trace": "enabled"
    }
)


# ─────────────────────────────────────────
# MOCK CUSTOMER DATABASE
# In production → real database query
# ─────────────────────────────────────────

REGISTERED_CUSTOMERS = [
    "haristerz97@gmail.com",
    "john@gmail.com",
    "customer@bt.com",
    "test@gmail.com"
]

INTENT_TO_AGENT = {
    "invoice_not_received": "invoice_agent",
    "payment_confirmation": "payment_agent",
    "bill_copy_request":    "bill_copy_agent",
    "billing_dispute":      "servicenow_agent",
    "service_complaint":    "servicenow_agent",
    "account_inquiry":      "rag_agent",
    "general_inquiry":      "rag_agent",
    "unknown":              "rag_agent"
}


# ─────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────

triage_agent = Agent(
    role="Email Triage Specialist",
    goal="""Validate customer emails and
            route them to correct agent.""",
    backstory="""You are a senior BT customer
                 service manager. You validate
                 requests and route them correctly.
                 You are strict about authorization.""",
    llm=llm,
    verbose=True
)


# ─────────────────────────────────────────
# TASK
# ─────────────────────────────────────────

def create_triage_task(
    parsed_email: dict,
    intent_result: dict
) -> Task:
    sender = parsed_email.get("sender", "")
    is_customer = sender in REGISTERED_CUSTOMERS
    assigned = INTENT_TO_AGENT.get(
        intent_result.get("primary_intent", "unknown"),
        "rag_agent"
    )

    return Task(
        description=f"""
        Triage this customer email request.

        SENDER: {sender}
        IS REGISTERED CUSTOMER: {is_customer}
        INTENT: {intent_result.get('primary_intent')}
        CONFIDENCE: {intent_result.get('confidence')}
        URGENCY: {intent_result.get('urgency')}
        ASSIGNED AGENT: {assigned}

        Rules:
        → If not registered customer → not authorized
        → If confidence < 0.7 → requires human review
        → If authorized and valid → assign to agent

        Return ONLY this JSON:
        {{
            "is_authorized": true/false,
            "is_valid": true/false,
            "assigned_agent": "{assigned}",
            "priority": "high/medium/low",
            "requires_human_review": true/false,
            "reason": "brief reason here"
        }}
        """,
        expected_output="JSON triage decision",
        agent=triage_agent
    )


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────
@observe
def triage_email(
    parsed_email: dict,
    intent_result: dict
) -> str:

    task = create_triage_task(
        parsed_email,
        intent_result
    )

    crew = Crew(
        agents=[triage_agent],
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
        "core_message": "Invoice for March 2026 not received.",
        "account_number": "BT12345"
    }

    test_intent = {
        "primary_intent": "invoice_not_received",
        "confidence": 0.98,
        "urgency": "high",
        "sentiment": "frustrated"
    }

    print("Testing Triage Agent...")
    result = triage_email(test_parsed, test_intent)
    print(f"\nTriage Result:\n{result}")