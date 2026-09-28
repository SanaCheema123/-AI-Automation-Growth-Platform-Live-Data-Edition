from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/runtime")
def runtime(user=Depends(get_current_user)):
    provider = settings.effective_ai_provider
    model = settings.GEMINI_MODEL if provider == "gemini" else settings.GROQ_MODEL if provider == "groq" else None
    return {
        "environment": settings.ENVIRONMENT,
        "ai_provider": provider,
        "ai_model": model,
        "ai_ready": settings.ai_ready,
        "secondary_fallback": settings.AI_FALLBACK_TO_SECONDARY,
    }


@router.get("/integrations")
def integrations(user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("select 1"))
    except Exception:
        db_ok = False
    provider = settings.effective_ai_provider
    return {
        "items": [
            {
                "id": "database",
                "name": "Live Database",
                "category": "System of record",
                "status": "connected" if db_ok else "error",
                "detail": "PostgreSQL/Supabase is recommended for production. SQLite is for local development only.",
            },
            {
                "id": "ai",
                "name": "AI Provider",
                "category": "Gemini / Groq",
                "status": "configured" if settings.ai_ready else "not_configured",
                "detail": f"Provider: {provider}. Keys remain server-side." if settings.ai_ready else "Add GEMINI_API_KEY or GROQ_API_KEY to enable live AI features.",
            },
            {
                "id": "outreach",
                "name": "Outbound Messaging",
                "category": "Optional connector",
                "status": "not_connected",
                "detail": "Drafts and approvals work now. No message is sent until you implement and configure an outbound connector.",
            },
            {
                "id": "engagement",
                "name": "Engagement Tracking",
                "category": "Optional connector",
                "status": "not_connected",
                "detail": "Connect a real event/web/email source before using engagement metrics as live customer activity.",
            },
        ]
    }
