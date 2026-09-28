import os,tempfile
os.environ['ENVIRONMENT']='test'
os.environ['DATABASE_URL']='sqlite:///'+tempfile.gettempdir()+'/ai_growth_test.db'
os.environ['SUPABASE_DB_URL']=''
os.environ['SECRET_KEY']='test-secret-key-that-is-long-enough'
os.environ['AUTO_CREATE_TABLES']='true'
os.environ['GEMINI_API_KEY']=''
os.environ['GROQ_API_KEY']=''
os.environ['AI_PROVIDER']='auto'
os.environ['AI_FALLBACK_TO_SECONDARY']='true'

import pytest
from fastapi.testclient import TestClient
from app.core.database import Base,engine
from app.main import app

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); yield

@pytest.fixture
def client():
    with TestClient(app) as c: yield c

@pytest.fixture
def auth(client):
    payload={'organization_name':'Acme Growth','name':'Owner','email':'owner@acme.example.com','password':'StrongPass123!'}
    r=client.post('/api/v1/auth/register',json=payload); assert r.status_code==201
    token=r.json()['access_token']; return {'Authorization':f'Bearer {token}'}
