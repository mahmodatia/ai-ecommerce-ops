from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import Intent, RecommendedAction


class Customer(BaseModel):
    name: str
    email: str


class OrderItem(BaseModel):
    sku: str
    title: str
    quantity: int = Field(gt=0)


class Order(BaseModel):
    id: str
    order_number: str
    customer: Customer
    financial_status: str
    fulfillment_status: str
    placed_at: datetime
    delivered_at: datetime | None = None
    tracking_status: str | None = None
    tracking_last_update: datetime | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None
    items: list[OrderItem]
    total_amount: float
    currency: str


class CustomerMessage(BaseModel):
    id: str
    sender_email: str
    subject: str
    body: str
    expected_intent: Intent | None = None
    expected_order_number: str | None = None


class EmailUnderstanding(BaseModel):
    intent: Intent
    order_number: str | None = None
    customer_email: str | None = None
    customer_name: str | None = None
    confidence: float = Field(ge=0, le=1)
    facts: list[str] = Field(default_factory=list)
    requires_policy_lookup: bool = False


class DecisionResult(BaseModel):
    recommended_action: RecommendedAction
    requires_human_approval: bool
    reason: str


class DecisionTraceStep(BaseModel):
    key: str
    label: str
    source: str
    status: str = "complete"
    value: str | None = None
    detail: str | None = None


class CaseResult(BaseModel):
    case_id: str | None = None
    message_id: str
    analysis: EmailUnderstanding
    order: Order | None
    policy_excerpt: str | None
    decision: DecisionResult
    draft_reply: str
    status: str = "awaiting_approval"
    source: str = "unknown"
    trace: list[DecisionTraceStep] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)
    request_body: str | None = None
    request_subject: str | None = None
    request_sender: str | None = None
