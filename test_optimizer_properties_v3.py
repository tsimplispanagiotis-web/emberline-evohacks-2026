"""Independent oracle tests: brute force is deliberately NOT the production solver.

In 80 randomly generated small problems, verify that HiGHS matches a separate
exhaustive search implementation and never violates hard resource constraints.
"""
from __future__ import annotations
from random import Random
import pytest
from app.optimizer import optimize_assignments, candidate_utility
from app.engine import match_score, RESOURCE_TYPES

CATEGORIES=('Water','Food','Medical','Transport','Shelter')
STOCK_KEYS=('litres','meals','kits','seats','beds')
ZONES=('Faliraki','Kremasti','Ialyssos')


def brute_force(cases,volunteers,stock):
    best=0
    slots={v['id']:v['available'] for v in volunteers}
    left=dict(stock)
    def dfs(k,total):
        nonlocal best
        if k == len(cases):
            best=max(best,total);return
        c=cases[k]
        dfs(k+1,total)
        if c.get('duplicate_of') or c.get('emergency_flag') or c.get('needs_review'):
            return
        for v in volunteers:
            if slots[v['id']] < 1 or c['category'] not in v['skills'] or left[c['resource']] < c['demand']:
                continue
            slots[v['id']]-=1;left[c['resource']]-=c['demand']
            dfs(k+1,total+candidate_utility(c,v))
            slots[v['id']]+=1;left[c['resource']]+=c['demand']
    dfs(0,0)
    return best

@pytest.mark.parametrize('seed',range(80))
def test_milp_matches_independent_exhaustive_oracle(seed):
    r=Random(seed)
    volunteers=[{'id':f'V-{i}','name':f'V{i}','zone':r.choice(ZONES),
                 'available':r.randint(0,2),
                 'skills':r.sample(CATEGORIES,r.randint(1,3))} for i in range(3)]
    stock={key:r.randint(0,5) for key in STOCK_KEYS}
    cases=[]
    for i in range(5):
        category=r.choice(CATEGORIES)
        cases.append({'id':f'C-{i}','category':category,'resource':RESOURCE_TYPES[category],
                      'demand':r.randint(1,3),'priority':r.choice(['HIGH','NORMAL']),
                      'zone':r.choice(ZONES),'confidence':r.random(),
                      'status':r.choice(['OPEN','MATCHED']),
                      'needs_review':r.random()<0.1,'emergency_flag':r.random()<0.08,
                      'duplicate_of':None if r.random()<0.9 else 'C-OLD'})
    assignment,stats=optimize_assignments(cases,volunteers,stock,match_score)
    assert stats['optimal'] is True
    brute=brute_force(cases,volunteers,stock)
    assert abs(stats['objective']-brute) < 0.001, f'seed {seed}, solver {stats["objective"]}, oracle {brute}'
    assert len(assignment)==len(set(assignment))
    assert all(sum(c['demand'] for c in cases if c['id'] in assignment and c['resource']==resource)
               <=qty for resource,qty in stock.items())
    assert all(sum(item['volunteer']==v['id'] for item in assignment.values())<=v['available'] for v in volunteers)
    assert all(not next(c for c in cases if c['id']==cid).get('emergency_flag') for cid in assignment)
