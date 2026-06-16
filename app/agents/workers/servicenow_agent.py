# app/agents/workers/servicenow_agent.py

import random
from crewai import Agent, Task, Crew, LLM
from app.core.config import settings


# ─────────────────────────────────────────
# MOCK BILLING DATABASE
# In production → queries real billing system
# ─────────────────────────────────────────

BILLING_RECORDS = {
    "BT12345": {
        "March 2026": {
            "plan_charge": "£30.00",
            "call_charge": "£5.00",
            "data_charge": "£10.00",
            "extra_charge": "£25.00",
            "extra_charge_reason": "International roaming",
            "total": "£70.00",
            "expected_total": "£45.00"
        },
        "February 2026": {
            "plan_charge": "£30.00",
            "call_charge": "£4.00",
            "data_charge": "£10.00",
            "extra_charge": "£0.00",
            "extra_charge_reason": "None",
            "total": "£44.00",
            "expected_total": "£44.00"
        }
    },
    "BT99999": {
        "March 2026": {
            "plan_charge": "£50.00",
            "call_charge": "£8.00",
            "data_charge": "£12.00",
            "extra_charge": "£0.00",
            "extra_charge_reason": "None",
            "total": "£70.00",
            "expected_total": "£70.00"
        }
    }
}


# ─────────────────────────────────────────
# HELPER — Generate Ticket Number
# ─────────────────────────────────────────

def generate_ticket_number() -> str:
    return "TKT-" + str(
        random.randint(100000, 999999)
    )


# ─────────────────────────────────────────
# HELPER — Get Billing Record
# ─────────────────────────────────────────

def get_billing_record(
    account_number: str,
    month: str = "March 2026"
) -> dict:
    """
    Gets billing record for customer.
    In production → queries real billing system.
    """
    account = BILLING_RECORDS.get(
        account_number, {}
    )
    return account.get(month, {})


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
# AGENT
# ─────────────────────────────────────────

servicenow_agent = Agent(
    role="Billing Dispute Specialist",
    goal="""Investigate billing disputes accurately.
            Check billing records and create
            ServiceNow tickets for valid disputes.""",
    backstory="""You are a senior BT billing
                 dispute specialist. You check
                 billing records carefully and
                 raise tickets for valid disputes.
                 You are fair and thorough.""",
    llm=llm,
    verbose=True
)


# ─────────────────────────────────────────
# TASK
# ─────────────────────────────────────────

def create_servicenow_task(
    parsed_email: dict,
    intent: dict
) -> Task:

    account = parsed_email.get(
        "account_number", "unknown"
    )
    billing = get_billing_record(account)
    ticket_id = generate_ticket_number()

    return Task(
        description=f"""
        Customer is disputing a charge
        on their bill.

        CUSTOMER DETAILS:
        Account Number: {account}
        Core Complaint: {parsed_email.get('core_message')}
        Urgency: {intent.get('urgency')}

        BILLING RECORD FROM SYSTEM:
        {billing}

        Your job:
        1. Check if extra charge exists
        2. Compare total vs expected total
        3. If dispute is valid → create ticket
        4. If no extra charge → explain clearly

        Ticket ID to use if creating: {ticket_id}

        Return ONLY this JSON:
        {{
            "ticket_created": true/false,
            "ticket_id": "{ticket_id} or null",
            "dispute_valid": true/false,
            "extra_charge_found": "amount or none",
            "priority": "high/medium/low",
            "status": "open or no_dispute_found",
            "estimated_resolution": "48 hours or null",
            "message": "professional message to customer"
        }}
        """,
        expected_output="JSON with ticket details",
        agent=servicenow_agent
    )


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def process_dispute(
    parsed_email: dict,
    intent: dict
) -> str:

    task = create_servicenow_task(
        parsed_email,
        intent
    )

    crew = Crew(
        agents=[servicenow_agent],
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
        "subject": "Wrong charge on bill",
        "core_message": "I was charged £25 extra on March 2026 bill. This seems wrong.",
        "account_number": "BT12345"
    }

    test_intent = {
        "primary_intent": "billing_dispute",
        "confidence": 0.97,
        "urgency": "high",
        "sentiment": "frustrated"
    }

    print("Testing ServiceNow Agent...")
    result = process_dispute(
        test_parsed,
        test_intent
    )
    print(f"\nServiceNow Result:\n{result}")