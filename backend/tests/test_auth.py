def test_register_login_and_me(client):
    p={'organization_name':'Test Org','name':'Admin','email':'admin@example.com','password':'StrongPass123!'}
    r=client.post('/api/v1/auth/register',json=p); assert r.status_code==201
    token=r.json()['access_token']
    me=client.get('/api/v1/auth/me',headers={'Authorization':f'Bearer {token}'}); assert me.status_code==200; assert me.json()['email']=='admin@example.com'
    login=client.post('/api/v1/auth/login',json={'email':p['email'],'password':p['password']}); assert login.status_code==200

def test_protected_route_requires_token(client): assert client.get('/api/v1/leads').status_code==401
