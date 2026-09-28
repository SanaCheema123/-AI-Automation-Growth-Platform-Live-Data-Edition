from __future__ import annotations

import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.ai.gateway import AIGateway

from app.ai.services.meeting_analysis import (
    build_prompt as meeting_prompt,
)

from app.ai.services.outreach import (
    build_prompt as outreach_prompt,
)

from app.api.deps import (
    get_current_user,
)

from app.core.database import (
    get_db,
)

from app.schemas.ai import (
    AIRequestSchema,
    AIResponseSchema,
    ContentRequest,
    ContentResult,
    CopilotRequest,
    CopilotResult,
    LeadQualificationRequest,
    LeadQualificationResult,
    MeetingAnalysisRequest,
    MeetingAnalysisResult,
    OutreachRequest,
    OutreachResult,
)


router = APIRouter()


def _commit_failure_log(
    db: Session,
) -> None:
    """
    Try to persist the failed AI-request
    audit record without hiding the actual
    provider error.
    """

    try:
        db.commit()

    except Exception:
        db.rollback()


def _run_structured(
    db: Session,
    organization_id: str,
    operation: str,
    prompt: str,
    schema,
):

    try:
        result = AIGateway(
            db,
            organization_id,
        ).generate_structured(
            operation,
            prompt,
            schema,
        )

        db.commit()

        return result

    except RuntimeError as exc:
        _commit_failure_log(db)

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


# =========================================================
# Generic AI
# =========================================================


@router.post(
    "/generate",
    response_model=AIResponseSchema,
)
def generate(
    data: AIRequestSchema,
    user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    try:
        result = AIGateway(
            db,
            user.organization_id,
        ).generate(
            data.operation,
            data.prompt,
            data.json_mode,
        )

        db.commit()

        return result

    except RuntimeError as exc:
        _commit_failure_log(db)

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


# =========================================================
# Lead qualification
# =========================================================


@router.post(
    "/lead-qualification",
    response_model=AIResponseSchema,
)
def lead_qualification(
    data: LeadQualificationRequest,
    user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    prompt = (
        "Evaluate this lead using ONLY "
        "the supplied context. "
        "Do not invent facts.\n"

        "score must be 0-100.\n"

        "fit must be exactly one of: "
        "high, medium, low, unknown.\n"

        "buying_signal must be exactly "
        "one of: high, medium, low, unknown.\n"

        "facts must contain only explicit "
        "supplied facts.\n"

        "inferences must contain supported "
        "interpretations only.\n"

        "unknowns must list important "
        "missing information.\n"

        "signals must list relevant "
        "engagement or intent signals.\n"

        "reasoning must briefly explain "
        "the qualification result.\n"

        "recommended_action must be a safe "
        "next action and must not claim an "
        "external action already occurred.\n\n"

        "PROSPECT:\n"

        + json.dumps(
            data.prospect,
            default=str,
            ensure_ascii=False,
        )

        + "\n\nEVENT:\n"

        + json.dumps(
            data.event,
            default=str,
            ensure_ascii=False,
        )
    )

    return _run_structured(
        db,
        user.organization_id,
        "lead_qualification",
        prompt,
        LeadQualificationResult,
    )


# =========================================================
# Outreach
# =========================================================


@router.post(
    "/outreach",
    response_model=AIResponseSchema,
)
def outreach(
    data: OutreachRequest,
    user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    prompt = outreach_prompt(
        data.prospect,
        data.event,
    )

    if data.instruction:
        prompt += (
            "\n\n"
            "ADDITIONAL INSTRUCTION:\n"
            f"{data.instruction.strip()}"
        )

    return _run_structured(
        db,
        user.organization_id,
        "outreach",
        prompt,
        OutreachResult,
    )


# =========================================================
# Meeting Intelligence
# =========================================================


@router.post(
    "/meeting-analysis",
    response_model=AIResponseSchema,
)
def meeting_analysis(
    data: MeetingAnalysisRequest,
    user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    # IMPORTANT:
    # Do not append another field definition.
    # meeting_prompt already contains the
    # canonical output contract.

    prompt = meeting_prompt(
        data.notes
    )

    return _run_structured(
        db,
        user.organization_id,
        "meeting_analysis",
        prompt,
        MeetingAnalysisResult,
    )


# =========================================================
# Content Studio
# =========================================================


@router.post(
    "/content",
    response_model=AIResponseSchema,
)
def content(
    data: ContentRequest,
    user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    prompt = (
        "Create polished business content "
        "using ONLY the supplied source. "

        "Do not invent statistics, customer "
        "claims, results, quotations, or facts.\n"

        "linkedin_post: professional "
        "LinkedIn-ready post.\n"

        "short_post: concise social version.\n"

        "long_form_post: expanded "
        "professional version.\n"

        "newsletter: email/newsletter-style "
        "version.\n"

        "campaign_idea: one practical "
        "campaign concept.\n"

        f"TONE: {data.tone.strip()}\n\n"

        f"SOURCE:\n"
        f"{data.source.strip()}"
    )

    if data.instruction:
        prompt += (
            "\n\n"
            "ADDITIONAL INSTRUCTION:\n"
            f"{data.instruction.strip()}"
        )

    return _run_structured(
        db,
        user.organization_id,
        "content",
        prompt,
        ContentResult,
    )


# =========================================================
# Growth Copilot
# =========================================================


@router.post(
    "/copilot",
    response_model=AIResponseSchema,
)
def copilot(
    data: CopilotRequest,
    user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    prompt = (
        "You are a growth operations copilot. "

        "Use ONLY the supplied workspace context. "

        "If the context does not contain enough "
        "information, say so. "

        "Do not claim an email, CRM update, "
        "workflow action, publication, or other "
        "external action occurred unless the "
        "context explicitly proves it.\n\n"

        "QUESTION:\n"

        + data.question.strip()

        + "\n\nWORKSPACE CONTEXT:\n"

        + json.dumps(
            data.context,
            default=str,
            ensure_ascii=False,
        )
    )

    return _run_structured(
        db,
        user.organization_id,
        "copilot",
        prompt,
        CopilotResult,
    )