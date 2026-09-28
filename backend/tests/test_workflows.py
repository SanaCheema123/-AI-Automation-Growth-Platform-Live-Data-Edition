from app.ai.gateway import AIGateway

def make_workflow(client,auth,steps):
    r=client.post('/api/v1/workflows',headers=auth,json={'name':'Test Flow','definition':{'steps':steps}}); assert r.status_code==201; return r.json()

def test_workflow_approval_resume_and_idempotency(client,auth):
    lead=client.post('/api/v1/leads',headers=auth,json={'name':'Lead'}).json()
    wf=make_workflow(client,auth,[{'type':'trigger','config':{}},{'type':'human_approval','config':{'action_type':'crm_change'}},{'type':'crm_update','config':{'fields':{'workflow_status':'approved'}}}])
    body={'input':{'contact_id':lead['id']},'idempotency_key':'same-request-001'}
    r1=client.post(f"/api/v1/workflows/{wf['id']}/run",headers=auth,json=body); assert r1.status_code==200; assert r1.json()['status']=='waiting_approval'
    r2=client.post(f"/api/v1/workflows/{wf['id']}/run",headers=auth,json=body); assert r2.json()['id']==r1.json()['id']
    approvals=client.get('/api/v1/approvals',headers=auth).json(); assert len(approvals)==1
    approved=client.post(f"/api/v1/approvals/{approvals[0]['id']}/approve",headers=auth,json={'execute':True}); assert approved.status_code==200; assert approved.json()['run_status']=='completed'
    detail=client.get(f"/api/v1/workflows/runs/{r1.json()['id']}",headers=auth).json(); assert [s['status'] for s in detail['steps']]==['completed','completed','completed']

def test_rejection_cancels_run(client,auth):
    wf=make_workflow(client,auth,[{'type':'trigger','config':{}},{'type':'human_approval','config':{}}])
    run=client.post(f"/api/v1/workflows/{wf['id']}/run",headers=auth,json={'input':{}}).json(); approval=client.get('/api/v1/approvals',headers=auth).json()[0]
    r=client.post(f"/api/v1/approvals/{approval['id']}/reject",headers=auth,json={'comment':'Not safe'}); assert r.json()['run_status']=='cancelled'

def test_ai_template_and_failure_are_contained(client,auth,monkeypatch):
    seen={}
    def fake(self,operation,prompt,json_mode=False): seen['prompt']=prompt; return {'provider':'gemini','model':'fake','output':{'score':90}}
    monkeypatch.setattr(AIGateway,'generate',fake)
    wf=make_workflow(client,auth,[{'type':'ai_classify','config':{'prompt':'Inspect {{context}}','output_key':'qualification'}}])
    r=client.post(f"/api/v1/workflows/{wf['id']}/run",headers=auth,json={'input':{'company':'Acme'}}); assert r.json()['status']=='completed'; assert 'Acme' in seen['prompt']; assert '{{context}}' not in seen['prompt']
    def fail(self,operation,prompt,json_mode=False): raise RuntimeError('provider down')
    monkeypatch.setattr(AIGateway,'generate',fail)
    wf2=make_workflow(client,auth,[{'type':'ai_generate','config':{'prompt':'Do work'}}])
    failed=client.post(f"/api/v1/workflows/{wf2['id']}/run",headers=auth,json={'input':{}}).json(); assert failed['status']=='failed'; assert 'provider down' in failed['error']
