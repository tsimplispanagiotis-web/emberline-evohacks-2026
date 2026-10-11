"""Small exact 0-1 integer program for the EMBERLINE synthetic dispatch sandbox.

The solver proposes assignments; it never contacts responders or reserves stock.
We maximize a transparent utility score subject to three hard constraints:
* at most one volunteer per case,
* volunteer slot capacity,
* global supply inventory by resource type.
"""
from __future__ import annotations
from collections import defaultdict
from time import perf_counter
from typing import Any
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


def candidate_utility(case: dict, volunteer: dict) -> float:
    # No location-derived travel times: zones are synthetic and deliberately coarse.
    base = 125 if case['priority'] == 'HIGH' else 100
    return float(base + (18 if volunteer['zone'] == case['zone'] else 0) + round(4 * case.get('confidence', 0), 1))


def optimize_assignments(cases: list[dict], volunteers: list[dict], stock: dict[str, int], scorer):
    """Return (chosen_by_case, diagnostics), with a reproducible optimality check.

    `scorer` is kept injectable so constraints can be unit-tested independently.
    """
    t0 = perf_counter()
    valid = [c for c in cases if c['status'] in ('OPEN', 'MATCHED') and
             not c.get('emergency_flag') and not c.get('duplicate_of') and
             not c.get('needs_review') and c['category'] != 'Other']
    choices = []
    failures = defaultdict(list)
    for c in valid:
        for v in volunteers:
            score, reason = scorer(c, v, stock)
            if score < 0:
                failures[c['id']].append(f'{v["name"]}: {reason}')
                continue
            choices.append((c, v, candidate_utility(c, v), reason))
    if not choices:
        return {}, {'method': '0-1 mixed-integer linear programming (HiGHS)',
                    'optimal': True, 'objective': 0.0, 'eligible_cases': len(valid),
                    'candidate_pairs': 0, 'selected': 0, 'solve_ms': round((perf_counter()-t0)*1000, 2),
                    'unmatched_reasons': dict(failures)}

    n = len(choices)
    ids = list(dict.fromkeys(c['id'] for c,_,_,_ in choices))
    vids = list(dict.fromkeys(v['id'] for _,v,_,_ in choices))
    resources = sorted(set(c['resource'] for c,_,_,_ in choices))
    rows = [('case', x) for x in ids] + [('volunteer', x) for x in vids] + [('stock', x) for x in resources]
    index = {row:i for i,row in enumerate(rows)}
    A = lil_matrix((len(rows), n), dtype=float)
    for j, (c, v, utility, _) in enumerate(choices):
        A[index[('case', c['id'])],j] = 1
        A[index[('volunteer', v['id'])],j] = 1
        A[index[('stock',c['resource'])],j] = c['demand']
    upper = np.array([1 if name == 'case' else
                      next(v['available'] for v in volunteers if v['id'] == rid) if name == 'volunteer' else
                      stock.get(rid, 0) for name, rid in rows], dtype=float)
    # Explicit feasibility. An optimal solution is guaranteed since x=0 is allowed.
    out = milp(c=-np.array([item[2] for item in choices]),
               integrality=np.ones(n), bounds=Bounds(np.zeros(n), np.ones(n)),
               constraints=LinearConstraint(A.tocsr(), np.zeros(len(rows)), upper),
               options={'time_limit': 5, 'mip_rel_gap': 0.0})
    if out.x is None:
        raise RuntimeError(f'Optimization did not find a feasible solution (status {out.status})')
    selected = [choices[i] for i, x in enumerate(out.x) if x > 0.5]
    assignment = {c['id']: {'volunteer': v['id'], 'match_score': round(utility, 2),
                            'reason': reason, 'why': [
                               f'Eligible skill: {c["category"]}',
                               f'Zone preference: {"same zone" if c["zone"] == v["zone"] else "cross-zone — not a travel-time estimate"}',
                               f'Available volunteer slots before plan: {v["available"]}',
                               f'Inventory requirement: {c["demand"]} {c["resource"]}',
                               f'Priority: {c["priority"]}',
                               'Chosen in a globally resource-feasible 0–1 integer program.'
                             ]} for c, v, utility, reason in selected}
    return assignment, {'method': '0-1 mixed-integer linear programming (HiGHS)',
                        'optimal': out.status == 0,
                        'objective': round(sum(x[2] for x in selected), 2),
                        'eligible_cases': len(valid), 'candidate_pairs': len(choices),
                        'selected': len(selected), 'solve_ms': round((perf_counter()-t0)*1000, 2),
                        'unmatched_reasons': dict(failures)}
