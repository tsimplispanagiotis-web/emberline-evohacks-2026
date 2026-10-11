"""EMBERLINE 2: reproducible, synthetic-only, human-controlled relief workflow."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4
from typing import Any
import json, os, sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .engine import (classify, similarity, match_score, VOLUNTEERS, INITIAL_STOCK,
                     DEMO_MESSAGES, ZONES, RESOURCE_TYPES)
from .optimizer import optimize_assignments
from .scenario import analyze_scenario, PRESETS

ROOT = Path(__file__).parent.parent
DB = Path(os.getenv('EMBERLINE_DB', str(ROOT/'emberline.sqlite3')))
DB.parent.mkdir(parents=True, exist_ok=True)
LOCK = RLock()
app = FastAPI(title='EMBERLINE', version='2.0',
              description='Synthetic-only AI relief workflow demonstration — NOT an emergency service.')
app.mount('/static', StaticFiles(directory=ROOT/'app'/'static'), name='static')

class Intake(BaseModel):
    message: str = Field(min_length=8, max_length=1600)

class Review(BaseModel):
    category: str
    zone: str
    demand: int = Field(ge=1, le=30)

class Scenario(BaseModel):
    preset: str = Field(min_length=4, max_length=40)

class Escalation(BaseModel):
    confirmed_contacted: bool = False


def conn():
    c = sqlite3.connect(DB, check_same_thread=False, timeout=20)
    c.row_factory = sqlite3.Row
    return c


def empty_state():
    return {'cases': [], 'stock': dict(INITIAL_STOCK), 'volunteers': [dict(v) for v in VOLUNTEERS],
            'events': [], 'inbox': list(DEMO_MESSAGES), 'processed_count': 0,
            'optimizer': {'method': '0-1 mixed-integer linear programming (HiGHS)', 'selected': 0,
                          'objective': 0, 'optimal': None}}


def store_init():
    with conn() as c:
        c.execute('CREATE TABLE IF NOT EXISTS kv (name TEXT PRIMARY KEY, value TEXT NOT NULL)')
        if not c.execute('SELECT 1 FROM kv WHERE name="state"').fetchone():
            c.execute('INSERT INTO kv VALUES (?,?)', ('state', json.dumps(empty_state())))


def load():
    with conn() as c:
        row = c.execute('SELECT value FROM kv WHERE name="state"').fetchone()
        return json.loads(row['value'])


def save(s):
    # All mutating endpoints are serialized by LOCK in this demo process.
    with conn() as c:
        c.execute('UPDATE kv SET value=? WHERE name="state"', (json.dumps(s, ensure_ascii=False),))


def log(s, kind, message, case_id=None):
    s['events'].insert(0, {'id': str(uuid4())[:8], 'kind': kind, 'message': message,
                            'case_id': case_id, 'at': datetime.now(timezone.utc).isoformat()})
    s['events'] = s['events'][:250]


def case_by_id(s, case_id):
    case = next((c for c in s['cases'] if c['id'] == case_id), None)
    if case is None:
        raise HTTPException(status_code=404, detail='Unknown case')
    return case


def add_case(s, text):
    tags = classify(text)
    duplicate, maxscore = None, 0.0
    # Safety-sensitive reports must NEVER be suppressed as duplicates.
    if not tags['emergency_flag']:
        for old in s['cases']:
            if old['category'] != tags['category'] or old['zone'] != tags['zone'] or old.get('duplicate_of'):
                continue
            score = similarity(text, old['message'])
            if score > maxscore and score >= 0.56:
                duplicate, maxscore = old['id'], score
    status = 'CRITICAL' if tags['emergency_flag'] else 'DUPLICATE' if duplicate else 'REVIEW' if tags['needs_review'] else 'OPEN'
    case = {'id': f'R-{1001+s["processed_count"]}', 'message': text, 'status': status,
            'duplicate_of': duplicate, 'duplicate_similarity': round(maxscore, 3) if duplicate else None,
            'duplicate_override': False, 'assigned_volunteer': None, 'match_reason': None,
            'match_score': None, 'match_explanation': [], 'unmatched_reason': None,
            'human_reviewed': False, **tags}
    s['cases'].insert(0, case)
    s['processed_count'] += 1
    log(s, 'dedupe' if duplicate else 'classify',
        f'AI categorized {case["id"]}: {case["category"]} / {case["priority"]} / {case["zone"]}' +
        (f'; possible duplicate of {duplicate}' if duplicate else ''), case['id'])
    if status == 'CRITICAL':
        log(s, 'safety', f'{case["id"]}: possible life-threatening emergency; manual emergency-services escalation needed; no dispatch.', case['id'])
    if status == 'REVIEW':
        log(s, 'review', 'Uncertain or missing information: requires human correction before matching.', case['id'])
    return case


def result(s):
    cases = s['cases']
    count = lambda state: sum(x['status'] == state for x in cases)
    return {'cases': cases, 'volunteers': s['volunteers'], 'stock': s['stock'],
            'events': s['events'], 'inbox': s['inbox'], 'optimizer': s.get('optimizer', {}),
            'scenario': 'SYNTHETIC ONLY — NOT FOR EMERGENCY USE',
            'metrics': {'processed': s['processed_count'], 'open': count('OPEN'),
                        'matched': count('MATCHED'), 'approved': count('APPROVED'),
                        'duplicates': count('DUPLICATE'), 'review': count('REVIEW'),
                        'critical': sum(x['emergency_flag'] for x in cases),
                        'needs_escalation': count('CRITICAL'),
                        'auto_structured_pct': round(100*sum(not x['needs_review'] for x in cases)/len(cases)) if cases else 0}}


def check_invariants(s):
    if any(q < 0 for q in s['stock'].values()) or any(v['available'] < 0 for v in s['volunteers']):
        raise RuntimeError('Resource invariant violated')
    for c in s['cases']:
        if c['status'] in ('MATCHED', 'APPROVED') and (c['emergency_flag'] or c['duplicate_of']):
            raise RuntimeError(f'Unsafe case assignment detected: {c["id"]}')
    # Pending proposals collectively cannot consume more than remaining capacity.
    proposed = [c for c in s['cases'] if c['status'] == 'MATCHED']
    for k, qty in s['stock'].items():
        if sum(c['demand'] for c in proposed if c['resource'] == k) > qty:
            raise RuntimeError(f'Overcommitted inventory: {k}')
    for v in s['volunteers']:
        if sum(c['assigned_volunteer'] == v['id'] for c in proposed) > v['available']:
            raise RuntimeError(f'Overcommitted slots: {v["id"]}')


def recompute(s, *, log_action=True):
    for c in s['cases']:
        if c['status'] == 'MATCHED':
            c.update(status='OPEN', assigned_volunteer=None, match_score=None, match_reason=None,
                     match_explanation=[], unmatched_reason=None)
    chosen, stats = optimize_assignments(s['cases'], s['volunteers'], s['stock'], match_score)
    s['optimizer'] = stats
    for c in s['cases']:
        if c['id'] in chosen:
            a = chosen[c['id']]
            c.update(status='MATCHED', assigned_volunteer=a['volunteer'],
                     match_score=a['match_score'], match_reason=a['reason'],
                     match_explanation=a['why'])
        elif c['status'] == 'OPEN' and not c['needs_review'] and not c['emergency_flag']:
            # Distinguish "no feasible individual worker" from "globally feasible,
            # but outcompeted by more valuable jobs" in the optimization model.
            failures = stats.get('unmatched_reasons', {}).get(c['id'], [])
            any_candidate = any(match_score(c, v, s['stock'])[0] >= 0 for v in s['volunteers'])
            if any_candidate:
                c['unmatched_reason'] = (
                    'At least one volunteer could handle this request individually, '
                    'but the global plan used shared slots/stock for other higher-utility assignments. '
                    'Review the scenario or resources to explore alternatives.')
            elif failures:
                c['unmatched_reason'] = 'No feasible pair: ' + '; '.join(failures[:3])
            else:
                c['unmatched_reason'] = 'No eligible resources or volunteers under current constraints.'
    check_invariants(s)
    if log_action:
        log(s, 'optimizer', f'0–1 MILP: {stats["selected"]} feasible proposals, '
            f'objective {stats["objective"]}; optimal={stats["optimal"]}; '
            f'{stats["solve_ms"]}ms. No stock reserved without human approval.')
    return s


store_init()

@app.get('/')
def index():
    return FileResponse(ROOT/'app'/'static'/'index.html')

@app.get('/api/health')
def health():
    return {'status': 'ok', 'ai': 'locally trained TF-IDF classifier', 'optimization': 'integer programming',
            'mode': 'synthetic demo', 'emergency_use': False, 'version': '2.0'}

@app.get('/api/state')
def state():
    with LOCK:
        return result(load())

@app.post('/api/reset')
def reset():
    with LOCK:
        s = empty_state()
        log(s, 'system', 'Synthetic demo reset. No external services contacted.')
        save(s)
        return result(s)

@app.post('/api/import-demo')
def import_demo():
    with LOCK:
        s = load()
        messages = s['inbox']
        s['inbox'] = []
        for message in messages:
            add_case(s, message)
        log(s, 'batch', f'Processed {len(messages)} synthetic messages using locally trained ML.')
        save(s)
        return result(s)

@app.post('/api/intake')
def intake(p: Intake):
    with LOCK:
        if not p.message.strip() or len(p.message.strip()) < 8:
            raise HTTPException(status_code=422, detail='Enter a descriptive request of at least 8 characters.')
        s = load()
        if len(s['cases']) >= 200:
            raise HTTPException(status_code=413, detail='Synthetic demo case limit reached. Reset to start again.')
        case = add_case(s, p.message.strip())
        # New cases can change the optimization objective and must invalidate proposals.
        if any(c['status'] == 'MATCHED' for c in s['cases']):
            recompute(s)
        save(s)
        return {'case': case, 'state': result(s)}

@app.get('/api/scenarios')
def scenarios():
    return {'presets': PRESETS, 'disclaimer': 'Synthetic comparison, not a forecast or deployment recommendation.'}

@app.post('/api/scenario')
def scenario(p: Scenario):
    if p.preset not in PRESETS:
        raise HTTPException(status_code=422, detail='Select a supported simulation scenario.')
    with LOCK:
        snapshot = load()
    return analyze_scenario(snapshot, p.preset)

@app.post('/api/match')
def auto_match():
    with LOCK:
        s = load()
        recompute(s)
        save(s)
        return result(s)

@app.post('/api/approve/{case_id}')
def approve(case_id: str):
    with LOCK:
        s = load()
        c = case_by_id(s, case_id)
        if c['status'] != 'MATCHED' or not c['assigned_volunteer'] or c['emergency_flag'] or c['needs_review']:
            raise HTTPException(status_code=409, detail='Only non-critical, reviewed, matched cases can be approved.')
        v = next((x for x in s['volunteers'] if x['id'] == c['assigned_volunteer']), None)
        if not v or v['available'] < 1 or s['stock'].get(c['resource'], 0) < c['demand']:
            raise HTTPException(status_code=409, detail='Capacity or inventory changed. Re-run optimization.')
        v['available'] -= 1
        s['stock'][c['resource']] -= c['demand']
        c['status'] = 'APPROVED'
        log(s, 'approval', f'Human reserved {c["demand"]} {c["resource"]} for {case_id} with {v["name"]}. Dispatch NOT SENT.', case_id)
        recompute(s, log_action=True)  # refresh all other proposals against actual new capacity
        save(s)
        return result(s)

@app.post('/api/review/{case_id}')
def review(case_id: str, p: Review):
    with LOCK:
        s = load()
        c = case_by_id(s, case_id)
        if c['status'] in ('APPROVED', 'ESCALATED'):
            raise HTTPException(status_code=409, detail='Cannot change a finalized case.')
        if p.category not in RESOURCE_TYPES or p.zone not in ZONES:
            raise HTTPException(status_code=422, detail='Select a known category and zone.')
        if c['emergency_flag']:
            raise HTTPException(status_code=409, detail='Safety flag cannot be bypassed by editing classification.')
        if c['duplicate_of'] and not c.get('duplicate_override'):
            raise HTTPException(status_code=409, detail='Resolve duplicate status before human review.')
        c.update(category=p.category, zone=p.zone, demand=p.demand,
                 resource=RESOURCE_TYPES[p.category], needs_review=(p.category == 'Other'),
                 status='REVIEW' if p.category == 'Other' else 'OPEN', human_reviewed=True,
                 assigned_volunteer=None, match_reason=None, match_score=None,
                 match_explanation=[], unmatched_reason=None)
        log(s, 'review', f'Operator confirmed {p.category} / {p.zone} / {p.demand} units.', case_id)
        recompute(s)
        save(s)
        return result(s)

@app.post('/api/resolve-duplicate/{case_id}')
def resolve_duplicate(case_id: str):
    with LOCK:
        s = load()
        c = case_by_id(s, case_id)
        if c['status'] != 'DUPLICATE':
            raise HTTPException(status_code=409, detail='Case is not a duplicate candidate.')
        c.update(duplicate_of=None, duplicate_override=True, status='REVIEW' if c['needs_review'] else 'OPEN')
        log(s, 'override', f'Operator verified {case_id} is a distinct request; duplicate suppression removed.', case_id)
        recompute(s)
        save(s)
        return result(s)

@app.post('/api/reject/{case_id}')
def reject(case_id: str):
    with LOCK:
        s = load()
        c = case_by_id(s, case_id)
        if c['status'] != 'MATCHED':
            raise HTTPException(status_code=409, detail='Only proposed assignments can be rejected.')
        c.update(status='REJECTED', assigned_volunteer=None, match_explanation=[], match_reason=None)
        log(s, 'reject', 'Operator declined proposed assignment; no stock deducted.', case_id)
        recompute(s)
        save(s)
        return result(s)

@app.post('/api/reopen/{case_id}')
def reopen(case_id: str):
    with LOCK:
        s = load()
        c = case_by_id(s, case_id)
        if c['status'] != 'REJECTED':
            raise HTTPException(status_code=409, detail='Only rejected cases can be reopened.')
        c['status'] = 'REVIEW' if c['needs_review'] else 'OPEN'
        log(s, 'reopen', 'Human reopened declined case for re-optimization.', case_id)
        recompute(s)
        save(s)
        return result(s)

@app.post('/api/escalate/{case_id}')
def escalate(case_id: str, p: Escalation):
    with LOCK:
        s = load()
        c = case_by_id(s, case_id)
        if c['status'] != 'CRITICAL':
            raise HTTPException(status_code=409, detail='Only critical safety cases can be escalated.')
        # Acknowledgment is not an escalation. Keep a safety hold active until
        # the operator *affirmatively attests* manual contact. No call is made.
        if p.confirmed_contacted:
            c.update(status='ESCALATED', escalation_confirmed=True, safety_acknowledged=True)
            log(s, 'safety', 'Operator attests emergency services were contacted manually. App placed NO call.', case_id)
        else:
            c.update(status='CRITICAL', escalation_confirmed=False, safety_acknowledged=True)
            log(s, 'safety', 'Safety warning acknowledged. Critical hold remains OPEN; emergency-services contact still necessary.', case_id)
        save(s)
        return result(s)

@app.get('/api/dispatch-draft/{case_id}')
def dispatch_draft(case_id: str):
    with LOCK:
        s = load()
    c = case_by_id(s, case_id)
    if c['status'] not in ('MATCHED', 'APPROVED'):
        raise HTTPException(status_code=404, detail='No assignment available.')
    v = next(x for x in s['volunteers'] if x['id'] == c['assigned_volunteer'])
    return {'draft': f'DRAFT — NOT SENT — SYNTHETIC DEMO\nCase: {c["id"]}\nVolunteer: {v["name"]} ({v["zone"]})\nNeed: {c["demand"]} {c["resource"]} / {c["category"]}\nLocation: {c["zone"]}\nPriority: {c["priority"]}\nStatus: {c["status"]}\nNever use for a real emergency. Verify details before any real-world action.'}
