from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.audit import add_audit_log
from app.core.database import get_db
from app.models.event import Event
from app.schemas.events import EventCreate, EventUpdate
router=APIRouter()

def ser(e): return {k:getattr(e,k) for k in ['id','name','target_persona','offer','objective','event_date','status','created_at','updated_at']}

@router.get('')
def list_events(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return [ser(e) for e in db.query(Event).filter(Event.organization_id==user.organization_id).order_by(Event.event_date.desc(),Event.created_at.desc()).all()]
@router.post('',status_code=201)
def create_event(data:EventCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    e=Event(organization_id=user.organization_id,**data.model_dump());db.add(e);db.flush();add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='event.created',resource_type='event',resource_id=e.id);db.commit();db.refresh(e);return ser(e)
@router.get('/{event_id}')
def get_event(event_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    e=db.query(Event).filter(Event.id==event_id,Event.organization_id==user.organization_id).first();
    if not e: raise HTTPException(404,'Event not found')
    return ser(e)
@router.patch('/{event_id}')
def update_event(event_id:str,data:EventUpdate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    e=db.query(Event).filter(Event.id==event_id,Event.organization_id==user.organization_id).first();
    if not e: raise HTTPException(404,'Event not found')
    changes=data.model_dump(exclude_unset=True)
    for k,v in changes.items(): setattr(e,k,v)
    add_audit_log(db,organization_id=user.organization_id,user_id=user.id,action='event.updated',resource_type='event',resource_id=e.id,metadata={'fields':sorted(changes.keys())});db.commit();db.refresh(e);return ser(e)
