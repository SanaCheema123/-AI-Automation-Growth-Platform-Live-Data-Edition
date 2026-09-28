import json,uuid
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.audit import add_audit_log
from app.core.database import get_db
from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun
from app.models.workflow_step_run import WorkflowStepRun
from app.schemas.workflows import WorkflowCreate,WorkflowRunRequest,WorkflowUpdate
from app.workflows.engine.executor import WorkflowExecutor
from app.workflows.engine.validation import validate_definition
router=APIRouter()

def sw(w): return {'id':w.id,'name':w.name,'description':w.description,'active':w.active,'version':w.version,'definition':w.definition(),'created_at':w.created_at,'updated_at':w.updated_at}
def sr(r): return {'id':r.id,'workflow_id':r.workflow_id,'status':r.status,'trigger_type':r.trigger_type,'current_step':r.current_step,'current_node':r.current_node,'context':r.context(),'error':r.error,'started_at':r.started_at,'updated_at':r.updated_at,'completed_at':r.completed_at,'cancelled_at':r.cancelled_at}
@router.get('')
def list_workflows(user=Depends(get_current_user),db:Session=Depends(get_db)): return [sw(w) for w in db.query(Workflow).filter(Workflow.organization_id==user.organization_id).order_by(Workflow.updated_at.desc()).all()]
@router.post('',status_code=201)
def create(data:WorkflowCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    errors=validate_definition(data.definition)
    if errors: raise HTTPException(422,detail=errors)
    w=Workflow(organization_id=user.organization_id,name=data.name,description=data.description,definition_json=json.dumps(data.definition));db.add(w);db.flush();add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='workflow.created',resource_type='workflow',resource_id=w.id);db.commit();db.refresh(w);return sw(w)
@router.get('/runs')
def runs(status:str|None=None,limit:int=Query(100,ge=1,le=500),user=Depends(get_current_user),db:Session=Depends(get_db)):
    q=db.query(WorkflowRun).filter(WorkflowRun.organization_id==user.organization_id)
    if status:q=q.filter(WorkflowRun.status==status)
    return [sr(r) for r in q.order_by(WorkflowRun.started_at.desc()).limit(limit).all()]
@router.get('/runs/{run_id}')
def run_detail(run_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.query(WorkflowRun).filter(WorkflowRun.id==run_id,WorkflowRun.organization_id==user.organization_id).first()
    if not r: raise HTTPException(404,'Run not found')
    steps=db.query(WorkflowStepRun).filter(WorkflowStepRun.workflow_run_id==r.id).order_by(WorkflowStepRun.step_index).all(); out=sr(r);out['steps']=[{'step_index':s.step_index,'node_type':s.node_type,'status':s.status,'error':s.error,'input':json.loads(s.input_json or '{}'),'output':json.loads(s.output_json or '{}'),'started_at':s.started_at,'completed_at':s.completed_at} for s in steps];return out

@router.post('/runs/{run_id}/retry')
def retry_run(run_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.query(WorkflowRun).filter(WorkflowRun.id==run_id,WorkflowRun.organization_id==user.organization_id).first()
    if not r: raise HTTPException(404,'Run not found')
    if r.status!='failed': raise HTTPException(409,'Only failed runs can be retried')
    w=db.query(Workflow).filter(Workflow.id==r.workflow_id,Workflow.organization_id==user.organization_id).first()
    if not w: raise HTTPException(404,'Workflow not found')
    r=WorkflowExecutor(db).resume(w,r)
    add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='workflow.run_retried',resource_type='workflow_run',resource_id=r.id)
    db.commit(); return sr(r)

@router.get('/{workflow_id}')
def get(workflow_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    w=db.query(Workflow).filter(Workflow.id==workflow_id,Workflow.organization_id==user.organization_id).first()
    if not w: raise HTTPException(404,'Workflow not found')
    return sw(w)
@router.patch('/{workflow_id}')
def update(workflow_id:str,data:WorkflowUpdate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    w=db.query(Workflow).filter(Workflow.id==workflow_id,Workflow.organization_id==user.organization_id).first()
    if not w: raise HTTPException(404,'Workflow not found')
    changes=data.model_dump(exclude_unset=True)
    if changes.get('definition') is not None:
        errors=validate_definition(changes['definition'])
        if errors: raise HTTPException(422,detail=errors)
        w.definition_json=json.dumps(changes.pop('definition'));w.version+=1
    for k,v in changes.items():setattr(w,k,v)
    add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='workflow.updated',resource_type='workflow',resource_id=w.id);db.commit();db.refresh(w);return sw(w)
@router.post('/{workflow_id}/activate')
def activate(workflow_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)): return _set_active(workflow_id,True,user,db)
@router.post('/{workflow_id}/deactivate')
def deactivate(workflow_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)): return _set_active(workflow_id,False,user,db)
def _set_active(workflow_id,value,user,db):
    w=db.query(Workflow).filter(Workflow.id==workflow_id,Workflow.organization_id==user.organization_id).first()
    if not w: raise HTTPException(404,'Workflow not found')
    w.active=value;add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='workflow.activated' if value else 'workflow.deactivated',resource_type='workflow',resource_id=w.id);db.commit();return {'id':w.id,'active':w.active}
@router.post('/{workflow_id}/run')
def run(workflow_id:str,data:WorkflowRunRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    w=db.query(Workflow).filter(Workflow.id==workflow_id,Workflow.organization_id==user.organization_id).first()
    if not w: raise HTTPException(404,'Workflow not found')
    key=data.idempotency_key or str(uuid.uuid4());r=WorkflowExecutor(db).execute(w,user.organization_id,data.input,key);add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='workflow.run_started',resource_type='workflow_run',resource_id=r.id,metadata={'workflow_id':w.id});db.commit();return sr(r)
