from app.ai.gateway import AIGateway


def test_event_to_ai_to_approval_to_crm_flow(client, auth, monkeypatch):
    def fake_structured(self, operation, prompt, schema):
        return {
            'provider':'gemini',
            'model':'test-free-model',
            'fallback':False,
            'output':{
                'score':88,
                'fit':'high',
                'buying_signal':'high',
                'signals':['Event interest'],
                'facts':['Live test lead'],
                'inferences':[],
                'unknowns':[],
                'reasoning':'Strong supplied fit for the test flow.',
                'recommended_action':'Prepare a human-reviewed follow-up',
            },
        }
    monkeypatch.setattr(AIGateway,'generate_structured',fake_structured)

    event = client.post('/api/v1/events', headers=auth, json={
        'name': 'Growth Workshop',
        'target_persona': 'Revenue Leader',
        'objective': 'Identify automation opportunities',
        'status': 'active',
    })
    assert event.status_code == 201

    lead = client.post('/api/v1/leads', headers=auth, json={
        'name': 'Taylor Prospect',
        'email': 'taylor@example.com',
        'company': 'Example Co',
        'persona': 'Revenue Leader',
        'status': 'new',
    })
    assert lead.status_code == 201
    lead_id = lead.json()['id']

    qualified = client.post(f'/api/v1/leads/{lead_id}/qualify', headers=auth)
    assert qualified.status_code == 200
    assert qualified.json()['ai']['provider'] == 'gemini'
    assert qualified.json()['lead']['score'] == 88

    definition = {
        'steps': [
            {'type': 'trigger', 'config': {'event': 'event.attendee_captured'}},
            {'type': 'human_approval', 'config': {'action_type': 'outreach', 'risk_level': 'medium'}},
            {'type': 'crm_update', 'config': {'fields': {'workflow_status': 'approved_for_outreach'}}},
        ]
    }
    workflow = client.post('/api/v1/workflows', headers=auth, json={'name': 'E2E Growth Flow', 'definition': definition})
    assert workflow.status_code == 201

    run = client.post(f"/api/v1/workflows/{workflow.json()['id']}/run", headers=auth, json={
        'input': {'contact_id': lead_id, 'event': event.json()},
        'idempotency_key': 'e2e-growth-flow-001',
    })
    assert run.status_code == 200
    assert run.json()['status'] == 'waiting_approval'

    approval = client.get('/api/v1/approvals', headers=auth).json()[0]
    approved = client.post(f"/api/v1/approvals/{approval['id']}/approve", headers=auth, json={'execute': True})
    assert approved.status_code == 200
    assert approved.json()['run_status'] == 'completed'

    final_lead = client.get(f'/api/v1/leads/{lead_id}', headers=auth).json()
    assert final_lead['workflow_status'] == 'approved_for_outreach'
