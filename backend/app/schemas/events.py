from datetime import datetime
from pydantic import BaseModel, Field

class EventCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    target_persona: str | None = Field(default=None, max_length=255)
    offer: str | None = None
    objective: str | None = None
    event_date: datetime | None = None
    status: str = Field(default="draft", max_length=50)

class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    target_persona: str | None = Field(default=None, max_length=255)
    offer: str | None = None
    objective: str | None = None
    event_date: datetime | None = None
    status: str | None = Field(default=None, max_length=50)
