import pytest
from fastapi.testclient import TestClient
import app.main as backend

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(backend, 'DB', tmp_path/'isolated.sqlite')
    backend.store_init()
    with TestClient(backend.app) as cli:
        yield cli

def test_every_approval_keeps_all_pending_proposals_feasible(client):
    client.post('/api/import-demo')
    state=client.post('/api/match').json()
    assert state['optimizer']['optimal']
    assert state['optimizer']['method'].startswith('0-1 mixed-integer')
    while True:
        pending=[c for c in state['cases'] if c['status']=='MATCHED']
        if not pending:break
        r=client.post('/api/approve/'+pending[0]['id'])
        assert r.status_code==200,r.text
        state=r.json()
        for k,v in state['stock'].items():
            assert v>=0
            assert sum(c['demand'] for c in state['cases'] if c['status']=='MATCHED' and c['resource']==k)<=v
        for volunteer in state['volunteers']:
            assert volunteer['available']>=0
            assert sum(c['status']=='MATCHED' and c['assigned_volunteer']==volunteer['id'] for c in state['cases'])<=volunteer['available']
    assert state['metrics']['approved']>0


def test_duplicate_override_review_and_reopen(client):
    client.post('/api/import-demo')
    s=client.post('/api/match').json()
    dup=next(c for c in s['cases'] if c['status']=='DUPLICATE')
    r=client.post('/api/resolve-duplicate/'+dup['id'])
    assert r.status_code==200
    s=r.json()
    updated=next(c for c in s['cases'] if c['id']==dup['id'])
    assert updated['duplicate_of'] is None and updated['duplicate_override']
    # The manual override stays in place after subsequent imports.
    s=client.post('/api/intake',json={'message':'we need a ride for 2 passengers in Kremasti'}).json()['state']
    updated=next(c for c in s['cases'] if c['id']==dup['id'])
    assert updated['duplicate_of'] is None
    match=next(c for c in s['cases'] if c['status']=='MATCHED')
    before=dict(s['stock'])
    s=client.post('/api/reject/'+match['id']).json()
    assert s['stock']==before
    case=next(c for c in s['cases'] if c['id']==match['id'])
    assert case['status']=='REJECTED'
    s=client.post('/api/reopen/'+case['id']).json()
    assert next(c for c in s['cases'] if c['id']==case['id'])['status'] in ('OPEN','MATCHED')


def test_critical_escalation_cannot_claim_contact_without_attestation(client):
    client.post('/api/import-demo')
    s=client.post('/api/match').json()
    case=next(c for c in s['cases'] if c['status']=='CRITICAL')
    assert client.post('/api/approve/'+case['id']).status_code==409
    assert client.post('/api/review/'+case['id'],json={'category':'Water','zone':'Lindos','demand':1}).status_code==409
    s=client.post('/api/escalate/'+case['id'],json={'confirmed_contacted':False}).json()
    changed=next(c for c in s['cases'] if c['id']==case['id'])
    assert changed['status']=='CRITICAL'  # acknowledgment is not completion
    assert changed['escalation_confirmed'] is False
    assert 'still necessary' in s['events'][0]['message']
    assert s['metrics']['needs_escalation'] >= 1
    complete=client.post('/api/escalate/'+case['id'], json={'confirmed_contacted':True}).json()
    done=next(c for c in complete['cases'] if c['id']==case['id'])
    assert done['status']=='ESCALATED' and done['escalation_confirmed'] is True
    assert complete['metrics']['needs_escalation']==0


def test_unknown_location_needs_human_review(client):
    s=client.post('/api/intake',json={'message':'We need 5 bottles of clean drinking water'}).json()['state']
    c=s['cases'][0]
    assert c['status']=='REVIEW'
    assert client.post('/api/match').json()['metrics']['matched']==0
    s=client.post('/api/review/'+c['id'],json={'category':'Water','zone':'Ialyssos','demand':5}).json()
    c=next(x for x in s['cases'] if x['id']==c['id'])
    assert c['status'] in ('OPEN','MATCHED')
    assert c['human_reviewed']


def test_approved_is_immutable_and_no_extra_stock(client):
    client.post('/api/import-demo')
    s=client.post('/api/match').json()
    c=next(c for c in s['cases'] if c['status']=='MATCHED')
    s=client.post('/api/approve/'+c['id']).json()
    assert client.post('/api/review/'+c['id'],json={'category':'Water','zone':'Lindos','demand':1}).status_code==409
    assert client.post('/api/approve/'+c['id']).status_code==409


def test_html_and_json_available_without_real_dispatch(client):
    assert client.get('/').status_code==200
    assert 'EMBERLINE' in client.get('/').text
    assert client.get('/api/health').json()['emergency_use'] is False
    assert 'DRAFT' in client.get('/api/health').text or client.get('/api/health').json()['mode']=='synthetic demo'
