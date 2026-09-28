import json
from app.models.approval import Approval
class ApprovalNode:
    def __init__(self,db,organization_id): self.db=db; self.organization_id=organization_id
    def run(self,context,config,run,step_index):
        key=config.get('editable_context_key') or ('outreach_draft' if 'outreach_draft' in context.data else None)
        existing=self.db.query(Approval).filter(Approval.workflow_run_id==run.id,Approval.step_index==step_index).first()
        if not existing:
            payload={'message':config.get('message','Review this action before execution.'),'context':context.data,'editable_value':context.get(key) if key else None}
            self.db.add(Approval(organization_id=self.organization_id,workflow_run_id=run.id,step_index=step_index,action_type=config.get('action_type','external_action'),risk_level=config.get('risk_level','medium'),payload_json=json.dumps(payload,default=str),editable_context_key=key,status='pending'))
        return {'pause':True}
