from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import add_audit_log
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter()


def _token(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id, user.organization_id, user.role), organization_id=user.organization_id, user_id=user.id, user_name=user.name, role=user.role)


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email already registered")
    org = Organization(name=data.organization_name.strip())
    db.add(org)
    db.flush()
    user = User(organization_id=org.id, email=email, password_hash=hash_password(data.password), name=data.name.strip(), role="owner")
    db.add(user)
    db.flush()
    add_audit_log(db, organization_id=org.id, user_id=user.id, action="auth.register", resource_type="user", resource_id=user.id)
    db.commit()
    db.refresh(user)
    return _token(user)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return _token(user)


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return user
