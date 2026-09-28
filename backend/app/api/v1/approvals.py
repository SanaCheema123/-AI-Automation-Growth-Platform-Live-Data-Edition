import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import add_audit_log
from app.core.database import get_db
from app.core.time import utcnow
from app.models.approval import Approval
from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun
from app.schemas.workflows import ApprovalDecision, ApprovalEdit, ManualApprovalCreate
from app.workflows.engine.executor import WorkflowExecutor

router = APIRouter()


def ser(a):
    return {
        "id": a.id,
        "workflow_run_id": a.workflow_run_id,
        "step_index": a.step_index,
        "action_type": a.action_type,
        "risk_level": a.risk_level,
        "payload": json.loads(a.payload_json),
        "editable_context_key": a.editable_context_key,
        "status": a.status,
        "review_comment": a.review_comment,
        "created_at": a.created_at,
        "reviewed_at": a.reviewed_at,
    }


@router.get("")
def list_(status: str = "pending", user=Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Approval).filter(Approval.organization_id == user.organization_id)
    if status != "all":
        query = query.filter(Approval.status == status)
    return [ser(item) for item in query.order_by(Approval.created_at.desc()).all()]


@router.post("/manual", status_code=201)
def create_manual(data: ManualApprovalCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    name = "Manual AI Draft Review"
    workflow = db.query(Workflow).filter(Workflow.organization_id == user.organization_id, Workflow.name == name).first()
    if not workflow:
        definition = {
            "steps": [
                {"type": "trigger", "config": {"event": "manual.review_requested"}},
                {
                    "type": "human_approval",
                    "config": {
                        "action_type": "external_draft",
                        "risk_level": "medium",
                        "editable_context_key": "draft",
                        "message": "Review this AI-generated draft before continuing.",
                    },
                },
            ]
        }
        workflow = Workflow(organization_id=user.organization_id, name=name, description="System workflow for human review of AI-generated drafts. Approval does not send externally.", definition_json=json.dumps(definition), active=True)
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
    payload = {**data.context, "draft": data.value, "manual_review": True}
    run = WorkflowExecutor(db).execute(workflow, user.organization_id, payload, f"manual-{uuid.uuid4()}", trigger_type="manual_review")
    approval = db.query(Approval).filter(Approval.workflow_run_id == run.id, Approval.organization_id == user.organization_id).first()
    if not approval:
        raise HTTPException(500, "Could not create approval")
    approval.action_type = data.action_type
    approval.risk_level = data.risk_level
    approval_payload = json.loads(approval.payload_json)
    approval_payload["message"] = data.title
    approval.payload_json = json.dumps(approval_payload, default=str)
    add_audit_log(db, organization_id=user.organization_id, user_id=user.id, action="approval.manual_created", resource_type="approval", resource_id=approval.id)
    db.commit()
    db.refresh(approval)
    return ser(approval)


@router.patch("/{approval_id}")
def edit(approval_id: str, data: ApprovalEdit, user=Depends(get_current_user), db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id, Approval.organization_id == user.organization_id).first()
    if not approval:
        raise HTTPException(404, "Approval not found")
    if approval.status != "pending":
        raise HTTPException(409, "Approval already reviewed")
    payload = json.loads(approval.payload_json)
    payload["editable_value"] = data.edited_value
    approval.payload_json = json.dumps(payload, default=str)
    db.commit()
    return ser(approval)


@router.post("/{approval_id}/approve")
def approve(approval_id: str, data: ApprovalDecision, user=Depends(get_current_user), db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id, Approval.organization_id == user.organization_id).with_for_update().first()
    if not approval:
        raise HTTPException(404, "Approval not found")
    if approval.status != "pending":
        raise HTTPException(409, "Approval already reviewed")
    run = db.query(WorkflowRun).filter(WorkflowRun.id == approval.workflow_run_id, WorkflowRun.organization_id == user.organization_id).first()
    if not run:
        raise HTTPException(404, "Workflow run not found")
    payload = json.loads(approval.payload_json)
    effective_value = data.edited_value if data.edited_value is not None else payload.get("editable_value")
    if effective_value is not None and approval.editable_context_key:
        context = run.context()
        context[approval.editable_context_key] = effective_value
        run.context_json = json.dumps(context, default=str)
    approval.status = "approved"
    approval.reviewer_id = user.id
    approval.review_comment = data.comment
    approval.reviewed_at = utcnow()
    add_audit_log(db, organization_id=user.organization_id, user_id=user.id, action="approval.approved", resource_type="approval", resource_id=approval.id)
    db.commit()
    if data.execute:
        workflow = db.query(Workflow).filter(Workflow.id == run.workflow_id, Workflow.organization_id == user.organization_id).first()
        if workflow:
            run = WorkflowExecutor(db).resume(workflow, run)
    return {"approval": ser(approval), "run_status": run.status}


@router.post("/{approval_id}/reject")
def reject(approval_id: str, data: ApprovalDecision, user=Depends(get_current_user), db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id, Approval.organization_id == user.organization_id).with_for_update().first()
    if not approval:
        raise HTTPException(404, "Approval not found")
    if approval.status != "pending":
        raise HTTPException(409, "Approval already reviewed")
    run = db.query(WorkflowRun).filter(WorkflowRun.id == approval.workflow_run_id, WorkflowRun.organization_id == user.organization_id).first()
    approval.status = "rejected"
    approval.reviewer_id = user.id
    approval.review_comment = data.comment
    approval.reviewed_at = utcnow()
    if run:
        run.status = "cancelled"
        run.cancelled_at = utcnow()
        run.current_node = None
    add_audit_log(db, organization_id=user.organization_id, user_id=user.id, action="approval.rejected", resource_type="approval", resource_id=approval.id)
    db.commit()
    return {"approval": ser(approval), "run_status": run.status if run else "cancelled"}
