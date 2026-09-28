from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def add_audit_log(
    db: Session,
    *,
    organization_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    row = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=json.dumps(metadata or {}, default=str),
    )
    db.add(row)
    return row
