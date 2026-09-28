from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class AIRequestSchema(BaseModel):
    operation: str = Field(
        min_length=2,
        max_length=100,
    )

    prompt: str = Field(
        min_length=1,
        max_length=100_000,
    )

    json_mode: bool = False


class AIResponseSchema(BaseModel):
    provider: str
    model: str
    output: Any
    fallback: bool = False


class StrictAIResult(BaseModel):
    # Do not silently accept unexpected
    # fields from an AI model.
    model_config = ConfigDict(
        extra="forbid"
    )


# =========================================================
# Lead Qualification
# =========================================================


class LeadQualificationRequest(BaseModel):
    prospect: dict[str, Any]

    event: dict[str, Any] = Field(
        default_factory=dict
    )


class LeadQualificationResult(
    StrictAIResult
):
    score: float = Field(
        ge=0,
        le=100,
    )

    fit: Literal[
        "high",
        "medium",
        "low",
        "unknown",
    ]

    buying_signal: Literal[
        "high",
        "medium",
        "low",
        "unknown",
    ]

    signals: list[str]

    facts: list[str]

    inferences: list[str]

    unknowns: list[str]

    reasoning: str

    recommended_action: str


# =========================================================
# Outreach
# =========================================================


class OutreachRequest(BaseModel):
    prospect: dict[str, Any]

    event: dict[str, Any] = Field(
        default_factory=dict
    )

    instruction: str | None = Field(
        default=None,
        max_length=2000,
    )


class OutreachResult(
    StrictAIResult
):
    subject: str

    message: str

    personalization_points: list[str]

    unknowns: list[str]


# =========================================================
# Meeting
# =========================================================


class MeetingAnalysisRequest(
    BaseModel
):
    notes: str = Field(
        min_length=20,
        max_length=100_000,
    )


class MeetingAnalysisResult(
    StrictAIResult
):
    summary: str

    key_decisions: list[str]

    action_items: list[str]

    buying_signals: list[str]

    risks: list[str]

    crm_updates: list[str]

    follow_up_draft: str

    content_opportunities: list[str]

    confidence: float = Field(
        ge=0,
        le=1,
    )


# =========================================================
# Content
# =========================================================


class ContentRequest(BaseModel):
    source: str = Field(
        min_length=3,
        max_length=100_000,
    )

    tone: str = Field(
        default="professional",
        max_length=100,
    )

    instruction: str | None = Field(
        default=None,
        max_length=2000,
    )


class ContentResult(
    StrictAIResult
):
    linkedin_post: str

    short_post: str

    long_form_post: str

    newsletter: str

    campaign_idea: str


# =========================================================
# Copilot
# =========================================================


class CopilotRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=5000,
    )

    context: dict[str, Any] = Field(
        default_factory=dict
    )


class CopilotResult(
    StrictAIResult
):
    answer: str

    recommended_actions: list[str]