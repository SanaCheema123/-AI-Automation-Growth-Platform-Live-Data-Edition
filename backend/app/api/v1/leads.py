from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.ai.gateway import AIGateway
from app.api.deps import get_current_user
from app.core.audit import add_audit_log
from app.core.database import get_db
from app.core.time import utcnow
from app.models.contact import Contact
from app.schemas.ai import LeadQualificationResult
from app.schemas.leads import LEAD_STATUSES, LeadCreate, LeadUpdate

router = APIRouter()

def serialize(c: Contact):
    return {k:getattr(c,k) for k in ['id','name','email','company','role','persona','industry','source','status','notes','qualification_reason','score','engagement_score','buying_signal_score','workflow_status','next_action','follow_up_date','last_activity_at','created_at','updated_at']}

@router.get('')
def list_leads(q: str | None=None, status: str | None=None, min_score: float | None=Query(default=None, ge=0, le=100), page:int=Query(1,ge=1), page_size:int=Query(25,ge=1,le=100), user=Depends(get_current_user), db:Session=Depends(get_db)):
    query=db.query(Contact).filter(Contact.organization_id==user.organization_id)
    if q:
        like=f'%{q.strip()}%'; query=query.filter(or_(Contact.name.ilike(like),Contact.email.ilike(like),Contact.company.ilike(like),Contact.persona.ilike(like)))
    if status: query=query.filter(Contact.status==status)
    if min_score is not None: query=query.filter(Contact.score>=min_score)
    total=query.count(); rows=query.order_by(Contact.updated_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {'items':[serialize(x) for x in rows],'total':total,'page':page,'page_size':page_size}

@router.post('', status_code=201)
def create_lead(data:LeadCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    if data.status not in LEAD_STATUSES: raise HTTPException(422,'Unsupported lead status')
    row=Contact(organization_id=user.organization_id, **data.model_dump()); db.add(row); db.flush(); add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='lead.created',resource_type='lead',resource_id=row.id); db.commit(); db.refresh(row); return serialize(row)

@router.get('/{lead_id}')
def get_lead(lead_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=db.query(Contact).filter(Contact.id==lead_id,Contact.organization_id==user.organization_id).first()
    if not row: raise HTTPException(404,'Lead not found')
    return serialize(row)

@router.patch('/{lead_id}')
def update_lead(lead_id:str,data:LeadUpdate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=db.query(Contact).filter(Contact.id==lead_id,Contact.organization_id==user.organization_id).first()
    if not row: raise HTTPException(404,'Lead not found')
    changes=data.model_dump(exclude_unset=True)
    if changes.get('status') and changes['status'] not in LEAD_STATUSES: raise HTTPException(422,'Unsupported lead status')
    for k,v in changes.items(): setattr(row,k,v)
    if changes: row.last_activity_at=utcnow()
    if changes.get('status')=='converted' and not row.converted_at: row.converted_at=utcnow()
    add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='lead.updated',resource_type='lead',resource_id=row.id,metadata={'fields':sorted(changes.keys())}); db.commit(); db.refresh(row); return serialize(row)

@router.delete('/{lead_id}', status_code=204)
def delete_lead(lead_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=db.query(Contact).filter(Contact.id==lead_id,Contact.organization_id==user.organization_id).first()
    if not row: raise HTTPException(404,'Lead not found')
    add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='lead.deleted',resource_type='lead',resource_id=row.id); db.delete(row); db.commit()


@router.post('/{lead_id}/qualify')
def qualify_lead(lead_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=db.query(Contact).filter(Contact.id==lead_id,Contact.organization_id==user.organization_id).first()
    if not row: raise HTTPException(404,'Lead not found')
    prospect=serialize(row)
    prompt=("Evaluate this CRM lead using only supplied context. Return JSON with score, fit, buying_signal, signals, facts, inferences, unknowns, reasoning, recommended_action.\nPROSPECT:\n"+str(prospect))
    try:
        result=AIGateway(db,user.organization_id).generate_structured('lead_qualification',prompt,LeadQualificationResult)
    except RuntimeError as exc:
        db.commit()
        raise HTTPException(503, str(exc))
    output=result['output']
    row.score=float(output['score']); row.buying_signal_score={'high':90,'medium':65,'low':30,'unknown':0}.get(output.get('buying_signal'),0)
    row.qualification_reason=output.get('reasoning'); row.next_action=output.get('recommended_action'); row.last_activity_at=utcnow()
    if row.status=='new' and row.score>=75: row.status='qualified'
    add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='lead.ai_qualified',resource_type='lead',resource_id=row.id,metadata={'provider':result['provider'],'secondary_fallback':result.get('fallback',False)})
    db.commit(); db.refresh(row)
    return {'lead':serialize(row),'ai':result}
