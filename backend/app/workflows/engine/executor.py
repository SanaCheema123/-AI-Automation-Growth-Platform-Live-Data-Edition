from __future__ import annotations
import json,uuid
from app.core.time import utcnow
from app.models.workflow_run import WorkflowRun
from app.models.workflow_step_run import WorkflowStepRun
from app.workflows.engine.context import WorkflowContext
from app.workflows.engine.registry import NODE_REGISTRY

class WorkflowExecutor:
    def __init__(self,db): self.db=db
    def execute(self,workflow,organization_id,input_data,idempotency_key=None,trigger_type='manual'):
        key=idempotency_key or str(uuid.uuid4())
        existing=self.db.query(WorkflowRun).filter(WorkflowRun.organization_id==organization_id,WorkflowRun.workflow_id==workflow.id,WorkflowRun.idempotency_key==key).first()
        if existing: return existing
        run=WorkflowRun(workflow_id=workflow.id,organization_id=organization_id,idempotency_key=key,status='running',trigger_type=trigger_type,context_json=json.dumps(input_data,default=str))
        self.db.add(run); self.db.commit(); self.db.refresh(run); return self._continue(workflow,run)
    def resume(self,workflow,run):
        if run.status not in {'waiting_approval','failed','running'}: return run
        run.status='running'; run.error=None; self.db.commit(); return self._continue(workflow,run)
    def _continue(self,workflow,run):
        context=WorkflowContext(run.context()); steps=workflow.definition().get('steps',[])
        sr = None
        try:
            for idx in range(run.current_step,len(steps)):
                step=steps[idx]; typ=step['type']; cls=NODE_REGISTRY.get(typ)
                if not cls: raise ValueError(f'Unsupported workflow node: {typ}')
                prior=self.db.query(WorkflowStepRun).filter(WorkflowStepRun.workflow_run_id==run.id,WorkflowStepRun.step_index==idx,WorkflowStepRun.status=='completed').first()
                if prior: run.current_step=idx+1; continue
                sr=self.db.query(WorkflowStepRun).filter(WorkflowStepRun.workflow_run_id==run.id,WorkflowStepRun.step_index==idx).first()
                if not sr:
                    sr=WorkflowStepRun(organization_id=run.organization_id,workflow_run_id=run.id,step_index=idx,node_type=typ,status='running',input_json=json.dumps(context.data,default=str)); self.db.add(sr)
                else: sr.status='running'; sr.error=None
                run.current_node=typ; run.status='running'; self.db.flush()
                result=cls(self.db,run.organization_id).run(context,step.get('config',{}),run,idx) or {}
                sr.status='completed'; sr.output_json=json.dumps(context.data,default=str); sr.completed_at=utcnow()
                run.context_json=json.dumps(context.data,default=str); run.current_step=idx+1
                if result.get('pause'):
                    run.status='waiting_approval'; self.db.commit(); return run
                self.db.commit()
            run.status='completed'; run.current_node=None; run.completed_at=utcnow(); run.context_json=json.dumps(context.data,default=str); self.db.commit(); return run
        except Exception as exc:
            message=f'{type(exc).__name__}: {str(exc)[:1000]}'
            try:
                if sr is not None:
                    sr.status='failed'; sr.error=message; sr.completed_at=utcnow()
                run.status='failed'; run.error=message; run.context_json=json.dumps(context.data,default=str); run.current_node=None
                self.db.commit(); return run
            except Exception:
                self.db.rollback(); run=self.db.get(WorkflowRun,run.id); run.status='failed'; run.error=message; run.context_json=json.dumps(context.data,default=str); run.current_node=None; self.db.commit(); return run
