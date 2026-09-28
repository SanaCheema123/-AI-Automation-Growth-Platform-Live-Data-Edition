from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime()
    if settings.AUTO_CREATE_TABLES:
        init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Multi-tenant AI growth automation control plane",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", settings.REQUEST_ID_HEADER],
    expose_headers=[settings.REQUEST_ID_HEADER],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get(settings.REQUEST_ID_HEADER) or str(uuid.uuid4())
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={"request_id": request_id})
        response = JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred", "request_id": request_id},
        )
    response.headers[settings.REQUEST_ID_HEADER] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        database = "sqlite-local" if settings.database_url.startswith("sqlite") else "postgresql"
        return {"status": "ok", "database": database, "service": settings.APP_NAME, "version": "2.0.0"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unavailable", "service": settings.APP_NAME},
        )
