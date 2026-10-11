"""Counterfactuals are read-only; all solver plans satisfy hard constraints."""
import copy
import pytest
from fastapi.testclient import TestClient
import app.main as backend
from app.scenario import PRESETS, analyze_scenario
from app.engine import DEMO_MESSAGES, VOLUNTEERS, INITIAL_STOCK, match_score
from app.optimizer import optimize_assignments
from app.main import empty_state, add_case

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, 'DB', tmp_path / 'isolated.sqlite')
    backend.store_init()
    with TestClient(backend.app) as c:
        yield c

@pytest.mark.parametrize('preset', list(PRESETS))
def test_scenarios_are_immutable_and_consistent(client, preset):
    client.post('/api/import-demo')
    client.post('/api/match')
    before = client.get('/api/state').json()
    response = client.post('/api/scenario', json={'preset': preset})
    assert response.status_code == 200
    result = response.json()
    after = client.get('/api/state').json()
    # A what-if run must leave everything including timestamps and audit unchanged.
    assert after == before
    assert result['baseline']['optimal'] and result['counterfactual']['optimal']
    assert result['impact']['delta_coverage'] == result['counterfactual']['selected'] - result['baseline']['selected']
    assert result['effective_resources']['after']['stock'].keys() == INITIAL_STOCK.keys()
    assert len(result['assignments']['counterfactual']) == result['counterfactual']['selected']


def test_resource_shock_never_increases_available_supply(client):
    client.post('/api/import-demo')
    for preset, key in [('water_shortage','litres'),('food_shortage','meals')]:
        d = client.post('/api/scenario', json={'preset':preset}).json()
        assert d['effective_resources']['after']['stock'][key] < d['effective_resources']['before']['stock'][key]
    d = client.post('/api/scenario', json={'preset':'supply_boost'}).json()
    assert d['effective_resources']['after']['stock']['litres'] > d['effective_resources']['before']['stock']['litres']


def test_invalid_scenario_fails_without_side_effect(client):
    client.post('/api/import-demo')
    before = client.get('/api/state').json()
    assert client.post('/api/scenario', json={'preset':'delete_all'}).status_code == 422
    assert client.get('/api/state').json() == before


def test_empty_plan_what_if_is_safe(client):
    d = client.post('/api/scenario', json={'preset':'combined_shock'}).json()
    assert d['baseline']['selected'] == 0 and d['counterfactual']['selected'] == 0


def test_approved_inventory_protected_from_hypothetical_changes(client):
    client.post('/api/import-demo')
    s = client.post('/api/match').json()
    m = next(c for c in s['cases'] if c['status']=='MATCHED')
    s = client.post('/api/approve/'+m['id']).json()
    before = copy.deepcopy(s)
    for preset in PRESETS:
        d = client.post('/api/scenario', json={'preset':preset}).json()
        assert m['id'] not in d['assignments']['baseline']
        assert m['id'] not in d['assignments']['counterfactual']
    assert client.get('/api/state').json() == before


def test_scenarios_use_same_input_in_all_runs(client):
    client.post('/api/import-demo')
    a = client.post('/api/scenario', json={'preset':'combined_shock'}).json()
    b = client.post('/api/scenario', json={'preset':'combined_shock'}).json()
    assert a['assignments'] == b['assignments']
    assert a['impact'] == b['impact']
