def test_new_workspace_starts_empty_and_demo_route_is_removed(client):
    payload={
        'organization_name':'Live Workspace',
        'name':'Owner',
        'email':'live-owner@example.com',
        'password':'StrongPass123!'
    }
    registered=client.post('/api/v1/auth/register',json=payload)
    assert registered.status_code==201
    headers={'Authorization':f"Bearer {registered.json()['access_token']}"}
    leads=client.get('/api/v1/leads',headers=headers)
    assert leads.status_code==200
    assert leads.json()['total']==0
    assert client.post('/api/v1/auth/demo').status_code==404


def test_runtime_reports_ai_unconfigured_without_keys(client,auth):
    runtime=client.get('/api/v1/system/runtime',headers=auth)
    assert runtime.status_code==200
    body=runtime.json()
    assert body['ai_provider']=='unconfigured'
    assert body['ai_ready'] is False


def test_ai_endpoint_requires_configured_live_provider(client,auth):
    response=client.post('/api/v1/ai/content',headers=auth,json={'source':'A real customer insight with enough text to analyze.','tone':'professional'})
    assert response.status_code==503
    assert 'GEMINI_API_KEY or GROQ_API_KEY' in response.json()['detail']
