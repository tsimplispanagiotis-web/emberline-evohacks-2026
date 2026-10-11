import os
import tempfile
import pytest
from fastapi.testclient import TestClient
import app.main as backend

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(backend,'DB',tmp_path/'test.sqlite3')
    backend.store_init()
    with TestClient(backend.app) as c:yield c

def test_end_to_end(client):
    assert client.get('/api/health').status_code==200
    assert len(client.get('/api/state').json()['inbox'])==11
    r=client.post('/api/import-demo');assert r.status_code==200
    state=r.json();assert state['metrics']['processed']==11
    assert state['metrics']['critical']>=1
    assert state['metrics']['duplicates']>=1
    assert len(state['inbox'])==0
    r=client.post('/api/match');assert r.status_code==200
    state=r.json();assert state['metrics']['matched']>=1
    matched=next(c for c in state['cases'] if c['status']=='MATCHED')
    r=client.get('/api/dispatch-draft/'+matched['id']);assert 'NOT SENT' in r.json()['draft']
    r=client.post('/api/approve/'+matched['id']);assert r.status_code==200
    state=r.json();assert state['metrics']['approved']>=1
    assert client.post('/api/approve/'+matched['id']).status_code==409
    assert client.post('/api/reset').json()['metrics']['processed']==0

def test_input_validation(client):
    assert client.post('/api/intake',json={'message':'hi'}).status_code==422
    assert client.post('/api/intake',json={'message':'need water near Lindos for the family'}).status_code==200

def test_no_repeated_demo_import(client):
    first=client.post('/api/import-demo').json()
    second=client.post('/api/import-demo').json()
    assert first['metrics']['processed']==second['metrics']['processed']==11

def test_emergency_case_cannot_be_approved(client):
    client.post('/api/import-demo')
    state=client.post('/api/match').json()
    emergency=next(x for x in state['cases'] if x['emergency_flag'])
    assert emergency['status']=='CRITICAL'
    assert client.post('/api/approve/'+emergency['id']).status_code==409

def test_approval_deducts_exact_inventory(client):
    client.post('/api/import-demo')
    s=client.post('/api/match').json()
    original=dict(s['stock'])
    c=next(c for c in s['cases'] if c['status']=='MATCHED' and c['resource'] in original)
    approved=client.post('/api/approve/'+c['id']).json()
    assert approved['stock'][c['resource']]==original[c['resource']]-c['demand']
    v1=next(v for v in s['volunteers'] if v['id']==c['assigned_volunteer'])
    v2=next(v for v in approved['volunteers'] if v['id']==c['assigned_volunteer'])
    assert v1['available']==v2['available']+1

def test_different_zone_not_deduplicated(client):
    a=client.post('/api/intake',json={'message':'Need 12 litres of water in Faliraki'}).json()['case']
    b=client.post('/api/intake',json={'message':'Need 12 litres of water in Ialyssos'}).json()['case']
    assert a['zone']!=b['zone']
    assert b['duplicate_of'] is None

def test_invalid_body(client):
    assert client.post('/api/intake',json={'message':'x'*1601}).status_code==422
    assert client.post('/api/approve/R-9999').status_code==404
