"""Independent, reproducible synthetic optimization benchmark.

This is a proof-of-constraint case, NOT emergency outcome evaluation.
"""
from app.optimizer import optimize_assignments
from app.engine import match_score

CASES = [
    dict(id='WATER-1',category='Water',resource='litres',demand=1,zone='Faliraki',
         priority='NORMAL',confidence=.9,status='OPEN',needs_review=False,
         emergency_flag=False,duplicate_of=None),
    dict(id='FOOD-1',category='Food',resource='meals',demand=1,zone='Faliraki',
         priority='NORMAL',confidence=.9,status='OPEN',needs_review=False,
         emergency_flag=False,duplicate_of=None),
]
VOLUNTEERS = [
    dict(id='FLEX', name='Flexible worker',skills=['Water','Food'],zone='Faliraki',available=1),
    dict(id='WATER',name='Water specialist',skills=['Water'],zone='Faliraki',available=1),
]
STOCK={'litres':1,'meals':1}


def naive_greedy(cases, volunteers, stock):
    chosen=[]
    slots={v['id']:v['available'] for v in volunteers}
    left=dict(stock)
    for case in cases:
        for v in volunteers:
            vv={**v,'available':slots[v['id']]}
            score,_=match_score(case,vv,left)
            if score>=0:
                chosen.append((case['id'],v['id']))
                slots[v['id']]-=1
                left[case['resource']]-=case['demand']
                break
    return chosen


if __name__=='__main__':
    g=naive_greedy(CASES,VOLUNTEERS,STOCK)
    optimal,metrics=optimize_assignments(CASES,VOLUNTEERS,STOCK,match_score)
    print('Adversarial synthetic allocation — same inputs:')
    print('  Naive first-fit greedy:',g,'=>',len(g),'served')
    print('  Exact 0–1 MILP:',[(c,a['volunteer']) for c,a in optimal.items()],'=>',len(optimal),'served')
    print('  Solver optimal:',metrics['optimal'],'; utility:',metrics['objective'])
    print('No field performance, real-world rescues, or production latency claimed.')
