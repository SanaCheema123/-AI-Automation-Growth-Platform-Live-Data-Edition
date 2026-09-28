from datetime import timedelta
from fastapi import APIRouter,Depends,Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.time import utcnow
from app.models.ai_request import AIRequest
from app.models.approval import Approval
from app.models.contact import Contact
from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun
router=APIRouter()

def metric(value,previous=None,connected=True,note=None):
    change=None
    if previous not in (None,0): change=round((value-previous)/previous*100,1)
    return {'value':value,'previous':previous,'change_pct':change,'connected':connected,'note':note}

@router.get('/overview')
def overview(days:int=Query(30,ge=1,le=365),user=Depends(get_current_user),db:Session=Depends(get_db)):
    org=user.organization_id; now=utcnow(); start=now-timedelta(days=days); prev=start-timedelta(days=days)
    def count(model,*filters): return db.query(func.count(model.id)).filter(model.organization_id==org,*filters).scalar() or 0
    total=count(Contact); qualified=count(Contact,Contact.status=='qualified'); converted=count(Contact,Contact.status=='converted'); active=count(Workflow,Workflow.active.is_(True)); pending=count(Approval,Approval.status=='pending'); runs=count(WorkflowRun); completed=count(WorkflowRun,WorkflowRun.status=='completed'); failed=count(WorkflowRun,WorkflowRun.status=='failed'); ai=count(AIRequest)
    cur_leads=count(Contact,Contact.created_at>=start); prev_leads=count(Contact,Contact.created_at>=prev,Contact.created_at<start)
    cur_runs=count(WorkflowRun,WorkflowRun.started_at>=start); prev_runs=count(WorkflowRun,WorkflowRun.started_at>=prev,WorkflowRun.started_at<start)
    success_rate=round(completed/runs*100,1) if runs else 0
    conversion_rate=round(converted/total*100,1) if total else 0
    qualification_rate=round(qualified/total*100,1) if total else 0
    turnaround=db.query(func.avg(func.extract('epoch',Approval.reviewed_at-Approval.created_at))).filter(Approval.organization_id==org,Approval.reviewed_at.isnot(None)).scalar() if not db.bind.dialect.name=='sqlite' else None
    return {'period_days':days,'metrics':{
      'total_leads':metric(total,connected=True),'new_leads_period':metric(cur_leads,prev_leads),'qualified_leads':metric(qualified),'active_workflows':metric(active),'pending_approvals':metric(pending),'workflow_runs':metric(runs),'runs_period':metric(cur_runs,prev_runs),'automation_success_rate':metric(success_rate),'conversion_rate':metric(conversion_rate),'qualification_rate':metric(qualification_rate),'failed_workflows':metric(failed),'ai_requests':metric(ai),'outreach_sent':metric(None,connected=False,note='No outbound sending integration is connected'),'engagement_rate':metric(None,connected=False,note='No engagement tracking integration is connected'),'approval_turnaround_seconds':metric(round(turnaround,1) if turnaround else None,connected=turnaround is not None,note=None if turnaround else 'Available after reviewed approvals on PostgreSQL')},
      'funnel':{s:count(Contact,Contact.status==s) for s in ['new','qualified','engaged','needs_review','contacted','converted','disqualified']},
      'run_status':{s:count(WorkflowRun,WorkflowRun.status==s) for s in ['running','waiting_approval','completed','failed','cancelled']}}
