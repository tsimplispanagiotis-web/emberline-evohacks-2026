"""Counterfactual analysis in a synthetic, *read-only* planning sandbox.

The baseline and shocked scenarios use identical eligible cases and optimizer
settings. No volunteer, stock, case, audit or database row is ever mutated.
"""
from __future__ import annotations
from copy import deepcopy
from .engine import match_score
from .optimizer import optimize_assignments

PRESETS = {
    'water_shortage': '50% less remaining drinking water',
    'food_shortage': '75% less remaining prepared meals',
    'volunteer_absence': 'Elena unavailable (0 remaining slots)',
    'combined_shock': '50% less water + Elena unavailable',
    'supply_boost': '20 additional litres of water and 12 meals',
}


def analyze_scenario(state: dict, preset: str) -> dict:
    if preset not in PRESETS:
        raise ValueError(f'Unknown scenario: {preset}')
    snapshot = deepcopy(state)
    cases = snapshot['cases']
    volunteers = snapshot['volunteers']
    stock = snapshot['stock']

    baseline, baseline_stats = optimize_assignments(cases, volunteers, stock, match_score)
    virtual_volunteers = deepcopy(volunteers)
    virtual_stock = deepcopy(stock)
    if preset in ('water_shortage', 'combined_shock'):
        virtual_stock['litres'] //= 2
    if preset == 'food_shortage':
        virtual_stock['meals'] //= 4
    if preset in ('volunteer_absence', 'combined_shock'):
        for v in virtual_volunteers:
            if v['id'] == 'V-03':
                v['available'] = 0
    if preset == 'supply_boost':
        virtual_stock['litres'] += 20
        virtual_stock['meals'] += 12
    alternative, alternative_stats = optimize_assignments(cases, virtual_volunteers, virtual_stock, match_score)
    before, after = set(baseline), set(alternative)
    changed_assignment = [cid for cid in sorted(before & after)
                          if baseline[cid]['volunteer'] != alternative[cid]['volunteer']]
    diff = {
        'lost_coverage': sorted(before - after),
        'gained_coverage': sorted(after - before),
        'reassigned': changed_assignment,
        'unchanged_coverage': len(before & after),
        'delta_coverage': len(after) - len(before),
        'delta_utility': round(alternative_stats['objective'] - baseline_stats['objective'], 2),
    }
    return {
        'scenario': preset,
        'description': PRESETS[preset],
        'baseline': {'selected': len(before), 'objective': baseline_stats['objective'],
                     'optimal': baseline_stats['optimal']},
        'counterfactual': {'selected': len(after), 'objective': alternative_stats['objective'],
                           'optimal': alternative_stats['optimal']},
        'impact': diff,
        'effective_resources': {'before': {'stock': stock, 'slots': {v['id']: v['available'] for v in volunteers}},
                                'after': {'stock': virtual_stock,
                                          'slots': {v['id']: v['available'] for v in virtual_volunteers}}},
        'assignments': {'baseline': {cid: item['volunteer'] for cid, item in baseline.items()},
                        'counterfactual': {cid: item['volunteer'] for cid, item in alternative.items()}},
        'mode': 'SYNTHETIC COUNTERFACTUAL — NOT AN EMERGENCY FORECAST',
    }
