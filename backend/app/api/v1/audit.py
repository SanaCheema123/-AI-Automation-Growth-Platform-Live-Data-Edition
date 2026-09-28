import json
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.audit_log import AuditLog
router=APIRouter()
@router.get('')
def logs(limit:int=Query(100,ge=1,le=500),user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=db.query(AuditLog).filter(AuditLog.organization_id==user.organization_id).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [{'id':r.id,'user_id':r.user_id,'action':r.action,'resource_type':r.resource_type,'resource_id':r.resource_id,'metadata':json.loads(r.metadata_json or '{}'),'created_at':r.created_at} for r in rows]
