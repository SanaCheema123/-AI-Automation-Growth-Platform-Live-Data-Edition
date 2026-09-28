from fastapi import APIRouter
from app.api.v1 import ai,analytics,approvals,audit,auth,events,leads,system,workflows
api_router=APIRouter()
api_router.include_router(auth.router,prefix='/auth',tags=['auth'])
api_router.include_router(leads.router,prefix='/leads',tags=['leads'])
api_router.include_router(events.router,prefix='/events',tags=['events'])
api_router.include_router(workflows.router,prefix='/workflows',tags=['workflows'])
api_router.include_router(approvals.router,prefix='/approvals',tags=['approvals'])
api_router.include_router(ai.router,prefix='/ai',tags=['ai'])
api_router.include_router(analytics.router,prefix='/analytics',tags=['analytics'])
api_router.include_router(audit.router,prefix='/audit-logs',tags=['audit'])
api_router.include_router(system.router,prefix='/system',tags=['system'])
