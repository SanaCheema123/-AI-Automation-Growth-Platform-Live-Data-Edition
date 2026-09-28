from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=200)
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    organization_id: str
    user_id: str
    user_name: str
    role: str

class UserResponse(BaseModel):
    id: str
    organization_id: str
    email: EmailStr
    name: str
    role: str
