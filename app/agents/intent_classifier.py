from crewai import Agent, Task, Crew, LLM
from app.core.config import settings
from app.core.models import EmailIntent, IntentType, UrgencyLevel, SentimentType

llm = LLM(
    model=f"bedrock/{settings.claude_model}",
    aws_region_name=settings.aws_region
)

classifier_agent = Agent(
    role="Intent Classification Specialist",
    goal="""Classify the intent of customer
            emails accurately.""",
    backstory="""You are an expert at understanding
                 what telecom customers want.
                 You classify intents with high accuracy.""",
    llm=llm,
    verbose=True
)

def create_classifier_task(parsed_email: dict) -> Task:
    return Task(
        description=f"""
        Classify the intent of this customer email.

        EMAIL CONTENT:
        {parsed_email['core_message']}

        Choose ONE primary intent from:
        - invoice_not_received
        - payment_confirmation
        - bill_copy_request
        - billing_dispute
        - service_complaint
        - account_inquiry
        - general_inquiry
        - unknown

        Return ONLY this JSON:
        {{
            "primary_intent": "intent_here",
            "confidence": 0.95,
            "urgency": "high/medium/low",
            "sentiment": "frustrated/neutral/positive"
        }}
        """,
        expected_output="JSON with intent classification",
        agent=classifier_agent
    )

def classify_intent(parsed_email: dict) -> dict:
    task = create_classifier_task(parsed_email)

    crew = Crew(
        agents=[classifier_agent],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()
    return str(result)

if __name__ == "__main__":
    test_parsed = {
        "core_message": "Invoice for March 2026 not received. Requires urgent assistance.",
        "account_number": "BT12345",
        "sender": "john@gmail.com"
    }

    print("Testing Intent Classifier Agent...")
    result = classify_intent(test_parsed)
    print(f"\nIntent Result: {result}")