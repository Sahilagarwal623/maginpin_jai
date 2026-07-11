"""
Pydantic models for request/response schemas.

All API contracts between the judge harness and this bot are defined here.
Models are kept flat and explicit — no inheritance chains, no magic.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────
#  /v1/context
# ────────────────────────────────────────────────────

class ContextPushRequest(BaseModel):
    """Incoming context push from the judge."""
    scope: str = Field(..., description="category | merchant | customer | trigger")
    context_id: str
    version: int
    payload: dict[str, Any]
    delivered_at: str


class ContextPushAccepted(BaseModel):
    accepted: bool = True
    ack_id: str
    stored_at: str


class ContextPushRejected(BaseModel):
    accepted: bool = False
    reason: str
    current_version: Optional[int] = None
    details: Optional[str] = None


# ────────────────────────────────────────────────────
#  /v1/tick
# ────────────────────────────────────────────────────

class TickRequest(BaseModel):
    """Periodic wake-up call from the judge."""
    now: str
    available_triggers: list[str] = Field(default_factory=list)


class TickAction(BaseModel):
    """A single proactive message the bot wants to send."""
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    send_as: str = "vera"
    trigger_id: str
    template_name: str = "vera_generic_v1"
    template_params: list[str] = Field(default_factory=list)
    body: str
    cta: str = "open_ended"
    suppression_key: str = ""
    rationale: str = ""


class TickResponse(BaseModel):
    actions: list[TickAction] = Field(default_factory=list)


# ────────────────────────────────────────────────────
#  /v1/reply
# ────────────────────────────────────────────────────

class ReplyRequest(BaseModel):
    """Incoming reply from the merchant/customer, forwarded by the judge."""
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str = "merchant"
    message: str
    received_at: str
    turn_number: int


class ReplyResponse(BaseModel):
    """Bot's next move in the conversation."""
    action: str = "send"           # send | wait | end
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str = ""


# ────────────────────────────────────────────────────
#  /v1/healthz + /v1/metadata
# ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    uptime_seconds: int = 0
    contexts_loaded: dict[str, int] = Field(default_factory=dict)


class MetadataResponse(BaseModel):
    team_name: str = "Sahil Agarwal"
    team_members: list[str] = Field(default_factory=lambda: ["Sahil Agarwal"])
    model: str = "deterministic-rule-engine"
    approach: str = "Rule engine + scoring pipeline with category-aware template composition"
    contact_email: str = "sahil@example.com"
    version: str = "1.0.0"
    submitted_at: str = "2026-07-11T00:00:00Z"


# ────────────────────────────────────────────────────
#  Internal: composed message (output of compose())
# ────────────────────────────────────────────────────

class ComposedMessage(BaseModel):
    """Output of the compose() pipeline."""
    message: str
    cta: str
    send_as: str = "vera"
    suppression_key: str = ""
    rationale: str = ""
