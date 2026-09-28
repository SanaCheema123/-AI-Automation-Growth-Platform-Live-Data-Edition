from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

LEAD_STATUSES = {"new","qualified","engaged","needs_review","contacted","converted","disqualified"}

class LeadBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    company: str | None = Field(default=None, max_length=255)
    role: str | None = Field(default=None, max_length=255)
    persona: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    status: str = "new"
    notes: str | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    engagement_score: float | None = Field(default=None, ge=0, le=100)
    buying_signal_score: float | None = Field(default=None, ge=0, le=100)
    next_action: str | None = None
    follow_up_date: datetime | None = None
    qualification_reason: str | None = None

class LeadCreate(LeadBase): pass

class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    company: str | None = Field(default=None, max_length=255)
    role: str | None = Field(default=None, max_length=255)
    persona: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    status: str | None = None
    notes: str | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    engagement_score: float | None = Field(default=None, ge=0, le=100)
    buying_signal_score: float | None = Field(default=None, ge=0, le=100)
    next_action: str | None = None
    follow_up_date: datetime | None = None
    qualification_reason: str | None = None

class LeadResponse(LeadBase):
    id: str
    workflow_status: str | None = None
    last_activity_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
