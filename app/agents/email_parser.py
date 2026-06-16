# app/agents/email_parser.py
from langfuse import observe
from dotenv import load_dotenv
load_dotenv()  # loads .env into OS env first
from crewai import Agent, Task, Crew, LLM
from app.core.models import ParsedEmail
from app.core.config import settings


# ─────────────────────────────────────────
# LLM — Connect to AWS Bedrock
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
# AGENT — Email Parser
# ─────────────────────────────────────────

parser_agent = Agent(
    role="Email Parser Specialist",
    goal="""Extract the core message from
            customer emails. Remove greetings,
            signatures and noise.""",
    backstory="""You are an expert at reading
                 customer emails and extracting
                 only the important information.""",
    llm=llm,
    verbose=True
)


# ─────────────────────────────────────────
# TASK — Parse Email
# ─────────────────────────────────────────

def create_parser_task(email: dict) -> Task:
    return Task(
        description=f"""
        You are an email parser.
        
        Parse this customer email and extract:
        1. Core message - remove greetings and signatures
        2. Account number - find if mentioned

        EMAIL TO PARSE:
        From: {email['sender']}
        Subject: {email['subject']}
        Body: {email['body']}

        Return ONLY valid JSON like this:
        {{
            "core_message": "<actual core issue from email>",
            "account_number": "<account number or null>"
        }}

        Do NOT copy the format literally.
        Extract REAL values from the email above.
        """,
        expected_output="Valid JSON with core_message and account_number extracted from the email",
        agent=parser_agent
    )


# ─────────────────────────────────────────
# MAIN FUNCTION — Parse One Email
# ─────────────────────────────────────────
@observe
def parse_email(email: dict) -> dict:
    task = create_parser_task(email)

    crew = Crew(
        agents=[parser_agent],
        tasks=[task],
        verbose=False  # ← less noise
    )

    result = crew.kickoff()
    
    # Extract JSON from result
    import json
    result_str = str(result)
    
    try:
        # Remove markdown if present
        if "```json" in result_str:
            result_str = result_str.split("```json")[1]
            result_str = result_str.split("```")[0]
        
        parsed = json.loads(result_str.strip())
        
        return {
            "sender": email["sender"],
            "subject": email["subject"],
            "core_message": parsed.get("core_message", ""),
            "account_number": parsed.get("account_number", None),
            "attachments": []
        }
    except:
        # If JSON parsing fails
        return {
            "sender": email["sender"],
            "subject": email["subject"],
            "core_message": result_str,
            "account_number": None,
            "attachments": []
        }


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    test_email = {
        "sender": "haristerz97@gmail.com",
        "subject": "Invoice not received",
        "body": """Hi team,
        I haven't received my invoice
        for March 2026.
        My account number is BT12345.
        Please help urgently.
        Thanks, Hari"""
    }

    print("Testing Email Parser Agent...")
    result = parse_email(test_email)
    print("\nResult:")
    print(f"Sender: {result['sender']}")
    print(f"Subject: {result['subject']}")
    print(f"Core Message: {result['core_message']}")