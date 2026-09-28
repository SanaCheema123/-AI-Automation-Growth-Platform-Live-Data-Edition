from app.models.contact import Contact
class CRMUpdateNode:
    ALLOWED_FIELDS={'name','email','company','role','persona','industry','notes','score','workflow_status','next_action','follow_up_date','buying_signal_score','engagement_score','status','qualification_reason'}
    def __init__(self,db,organization_id): self.db=db; self.organization_id=organization_id
    def run(self,context,config,run,step_index):
        contact_id=config.get('contact_id') or context.get('contact_id'); fields=dict(config.get('fields',{}))
        if not contact_id:
            context.set('crm_update',{'provider':'supabase','status':'skipped','reason':'No contact_id supplied'}); return {'pause':False}
        contact=self.db.query(Contact).filter(Contact.id==contact_id,Contact.organization_id==self.organization_id).first()
        if not contact: raise ValueError('Contact not found for current organization')
        updated={}
        for k,v in fields.items():
            if k in self.ALLOWED_FIELDS: setattr(contact,k,v); updated[k]=v
        self.db.flush(); context.set('crm_update',{'provider':'supabase','status':'completed','contact_id':contact.id,'fields':updated}); return {'pause':False}
