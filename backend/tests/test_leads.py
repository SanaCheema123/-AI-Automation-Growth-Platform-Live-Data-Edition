def test_lead_crud(client,auth):
    r=client.post('/api/v1/leads',headers=auth,json={'name':'Jane Buyer','email':'jane@example.com','company':'Northstar','status':'qualified','score':92}); assert r.status_code==201
    lid=r.json()['id']; listing=client.get('/api/v1/leads',headers=auth); assert listing.json()['total']==1
    u=client.patch(f'/api/v1/leads/{lid}',headers=auth,json={'status':'contacted','next_action':'Send case study'}); assert u.status_code==200; assert u.json()['status']=='contacted'

def test_tenant_isolation(client,auth):
    lead=client.post('/api/v1/leads',headers=auth,json={'name':'Private Lead'}).json()
    p={'organization_name':'Other Org','name':'Other','email':'other@other.example.com','password':'StrongPass123!'}
    token=client.post('/api/v1/auth/register',json=p).json()['access_token']; other={'Authorization':f'Bearer {token}'}
    assert client.get(f"/api/v1/leads/{lead['id']}",headers=other).status_code==404
