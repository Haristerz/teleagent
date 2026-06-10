# app/agents/email_parser.py
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
    aws_region_name=settings.aws_region
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
        Parse this customer email and extract:
        1. Core message (remove greetings/signatures)
        2. Account number if mentioned
        3. Key facts only

        EMAIL:
        From: {email['sender']}
        Subject: {email['subject']}
        Body: {email['body']}

        Return a clean summary of the core issue.
        """,
        expected_output="""
        A clean parsed version with:
        - core_message: main issue only
        - account_number: if found else null
        """,
        agent=parser_agent
    )


# ─────────────────────────────────────────
# MAIN FUNCTION — Parse One Email
# ─────────────────────────────────────────

def parse_email(email: dict) -> dict:
    task = create_parser_task(email)

    crew = Crew(
        agents=[parser_agent],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()

    return {
        "sender": email["sender"],
        "subject": email["subject"],
        "core_message": str(result),
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