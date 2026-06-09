from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────
# ENUMS — Fixed list of allowed values
# ─────────────────────────────────────────

class IntentType(str, Enum):
    INVOICE_NOT_RECEIVED    = "invoice_not_received"
    PAYMENT_CONFIRMATION    = "payment_confirmation"
    BILL_COPY_REQUEST       = "bill_copy_request"
    BILLING_DISPUTE         = "billing_dispute"
    SERVICE_COMPLAINT       = "service_complaint"
    ACCOUNT_INQUIRY         = "account_inquiry"
    GENERAL_INQUIRY         = "general_inquiry"
    UNKNOWN                 = "unknown"


class UrgencyLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    URGENT = "urgent"


class SentimentType(str, Enum):
    POSITIVE  = "positive"
    NEUTRAL   = "neutral"
    NEGATIVE  = "negative"
    FRUSTRATED = "frustrated"
    ANGRY     = "angry"


class WorkerAgent(str, Enum):
    INVOICE_AGENT    = "invoice_agent"
    BILL_COPY_AGENT  = "bill_copy_agent"
    PAYMENT_AGENT    = "payment_agent"
    SERVICENOW_AGENT = "servicenow_agent"
    RAG_AGENT        = "rag_agent"
    UNKNOWN          = "unknown"


# ─────────────────────────────────────────
# STEP 1 — Output of Email Parser Agent
# ─────────────────────────────────────────

class ParsedEmail(BaseModel):
    # Who sent the email
    sender: str

    # Email subject line
    subject: str

    # Clean core message (noise removed)
    core_message: str

    # List of attachment filenames
    attachments: List[str] = []

    # Customer account number if mentioned
    account_number: Optional[str] = None

    # When email was received
    timestamp: datetime = datetime.now()

    # Original raw email (kept for reference)
    raw_email: Optional[str] = None


# ─────────────────────────────────────────
# STEP 2 — Output of Intent Classifier
# ─────────────────────────────────────────

class EmailIntent(BaseModel):
    # Primary intent of the email
    primary_intent: IntentType

    # How confident Claude is (0.0 to 1.0)
    confidence: float

    # Is there a second intent?
    secondary_intent: Optional[IntentType] = None

    # How urgent is this?
    urgency: UrgencyLevel

    # How is customer feeling?
    sentiment: SentimentType

    # Key details extracted
    # Example: {"month": "March", "amount": "£25"}
    entities: dict = {}


# ─────────────────────────────────────────
# STEP 3 — Output of Triage Agent
# ─────────────────────────────────────────

class TriageResult(BaseModel):
    # Is this a real registered customer?
    is_authorized: bool

    # Is this a valid request?
    is_valid: bool

    # Which worker agent should handle this?
    assigned_agent: WorkerAgent

    # Priority level
    priority: UrgencyLevel

    # Why was this decision made?
    reason: str

    # Should human review this?
    requires_human_review: bool = False


# ─────────────────────────────────────────
# STEP 4 — Output of Worker Agents
# ─────────────────────────────────────────

class AgentResponse(BaseModel):
    # Did the agent succeed?
    success: bool

    # What action did agent take?
    action_taken: str

    # Message to send back to customer
    response_message: str

    # ServiceNow ticket if created
    ticket_id: Optional[str] = None

    # Files to attach to reply email
    attachments: List[str] = []

    # Any error message
    error: Optional[str] = None


# ─────────────────────────────────────────
# STEP 5 — Complete Email Processing Result
# ─────────────────────────────────────────

class EmailProcessingResult(BaseModel):
    # Original email
    parsed_email: ParsedEmail

    # What customer wants
    intent: EmailIntent

    # Triage decision
    triage: TriageResult

    # Worker agent result
    agent_response: AgentResponse

    # Was everything successful?
    overall_success: bool

    # Total processing time in seconds
    processing_time: float = 0.0