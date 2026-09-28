from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    definition: dict[str, Any]


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    definition: dict[str, Any] | None = None


class WorkflowRunRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class ApprovalDecision(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)
    edited_value: Any | None = None
    execute: bool = True


class ApprovalEdit(BaseModel):
    edited_value: Any


class ManualApprovalCreate(BaseModel):
    action_type: str = Field(default="external_draft", min_length=2, max_length=100)
    risk_level: Literal["low", "medium", "high"] = "medium"
    title: str = Field(default="Review AI-generated draft", max_length=255)
    value: Any
    context: dict[str, Any] = Field(default_factory=dict)
