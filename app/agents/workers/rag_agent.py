# app/agents/workers/rag_agent.py

from crewai import Agent, Task, Crew, LLM
from app.core.config import settings


# ─────────────────────────────────────────
# KNOWLEDGE BASE
# ─────────────────────────────────────────

KNOWLEDGE_BASE = [
    {
        "topic": "BT Unlimited Plan",
        "content": "BT Unlimited plan includes unlimited data, unlimited calls and unlimited texts for £30 per month. No fair usage policy applies."
    },
    {
        "topic": "Payment Methods",
        "content": "BT accepts payment via direct debit, credit card, debit card and bank transfer. Payments are due on 1st of every month."
    },
    {
        "topic": "Contract Period",
        "content": "Standard BT contracts are 24 months. Early termination fee applies if you leave before contract end date."
    },
    {
        "topic": "Data Allowance",
        "content": "BT Unlimited plan has no data cap. BT Basic plan includes 10GB data per month. BT Standard plan includes 50GB data per month."
    },
    {
        "topic": "Roaming Charges",
        "content": "BT charges £5 per day for international roaming in EU countries. Outside EU standard international rates apply."
    },
    {
        "topic": "Bill Due Date",
        "content": "BT bills are generated on the 1st of every month and payment is due within 14 days."
    },
    {
        "topic": "Customer Support",
        "content": "BT customer support is available 24/7 via phone at 0800-800-150 or online at bt.com/support"
    }
]


# ─────────────────────────────────────────
# HELPER — Search Knowledge Base
# ─────────────────────────────────────────

def search_knowledge(question: str) -> str:
    """
    Simple keyword search.
    Finds most relevant content
    for the customer question.
    """
    question_lower = question.lower()

    for item in KNOWLEDGE_BASE:
        topic_words = item['topic'].lower().split()
        if any(word in question_lower
               for word in topic_words):
            return item['content']

    return "Please contact BT support at 0800-800-150"


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

rag_agent = Agent(
    role="RAG Specialist",
    goal="""Answer customer questions accurately
            using only the provided knowledge base.
            Never make up information.""",
    backstory="""You are a BT telecom support
                 specialist with deep knowledge
                 of BT products and policies.
                 You only answer from verified
                 knowledge base content.""",
    llm=llm,
    verbose=True
)


# ─────────────────────────────────────────
# TASK
# ─────────────────────────────────────────

def create_rag_task(
    parsed_email: dict,
    intent: dict
) -> Task:

    # Find relevant content first
    relevant_content = search_knowledge(
        parsed_email.get('core_message', '')
    )

    return Task(
        description=f"""
        Customer has sent this question:

        Sender: {parsed_email.get('sender')}
        Subject: {parsed_email.get('subject')}
        Message: {parsed_email.get('core_message')}
        Account: {parsed_email.get('account_number')}

        RELEVANT KNOWLEDGE BASE:
        {relevant_content}

        Answer using ONLY the content above.
        Do not make up any information.
        Be friendly and professional.
        """,
        expected_output="Clear professional answer from knowledge base",
        agent=rag_agent
    )


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def answer_general_query(
    parsed_email: dict,
    intent: dict
) -> str:

    task = create_rag_task(parsed_email, intent)

    crew = Crew(
        agents=[rag_agent],
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
        "subject": "Data allowance query",
        "core_message": "What is my data allowance?",
        "account_number": "BT12345"
    }

    test_intent = {
        "primary_intent": "general_inquiry",
        "confidence": 0.98,
        "urgency": "low"
    }

    print("Testing RAG Agent...")
    result = answer_general_query(
        test_parsed,
        test_intent
    )
    print(f"\nRAG Result:\n{result}")