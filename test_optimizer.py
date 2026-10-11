"""Optimization and safety assertions on deliberately adversarial synthetic inputs."""
import copy
import pytest
from app.engine import match_score, classify
from app.optimizer import optimize_assignments


def fake_case(i, category, resource, demand=1, zone='Faliraki', priority='NORMAL'):
    return dict(id=i, category=category, resource=resource, demand=demand,
                zone=zone, priority=priority, confidence=.9, status='OPEN',
                emergency_flag=False, duplicate_of=None, needs_review=False)


def test_exact_program_escapes_greedy_trap():
    # The flexible volunteer MUST be saved for food while the water-only volunteer takes water.
    cases = [fake_case('C1','Water','litres'), fake_case('C2','Food','meals')]
    volunteers = [dict(id='flex',name='Flexible',skills=['Water','Food'],zone='Faliraki',available=1),
                  dict(id='water',name='Water only',skills=['Water'],zone='Faliraki',available=1)]
    allocation, report = optimize_assignments(cases, volunteers, {'litres':1,'meals':1}, match_score)
    assert report['optimal'] is True
    assert len(allocation) == 2
    assert allocation['C1']['volunteer'] == 'water'
    assert allocation['C2']['volunteer'] == 'flex'


def test_shared_supply_ceiling_across_volunteers():
    cases = [fake_case(f'C{i}','Water','litres',demand=7) for i in range(4)]
    volunteers=[dict(id=f'V{i}',name=f'V{i}',skills=['Water'],zone='Faliraki',available=2) for i in range(3)]
    allocation, report = optimize_assignments(cases, volunteers, {'litres':15}, match_score)
    assert len(allocation) == 2
    assert sum(next(c['demand'] for c in cases if c['id']==cid) for cid in allocation)<=15


def test_volunteer_slot_caps():
    cases=[fake_case(f'C{i}','Water','litres') for i in range(10)]
    volunteer=[dict(id='V',name='Solo',skills=['Water'],zone='Faliraki',available=2)]
    allocation,_=optimize_assignments(cases,volunteer,{'litres':50},match_score)
    assert len(allocation)==2


def test_excludes_emergency_uncertain_and_duplicates():
    cases=[fake_case('ok','Medical','kits'),fake_case('critical','Medical','kits'),
           fake_case('dup','Medical','kits'),fake_case('review','Medical','kits')]
    cases[1]['emergency_flag']=True
    cases[2]['duplicate_of']='ok'
    cases[3]['needs_review']=True
    v=[dict(id='V',name='Medic',skills=['Medical'],zone='Faliraki',available=10)]
    allocation,_=optimize_assignments(cases,v,{'kits':20},match_score)
    assert list(allocation)==['ok']


def test_no_resource_no_proposal():
    cases=[fake_case('one','Shelter','beds',4)]
    volunteers=[dict(id='V',name='Lead',skills=['Shelter'],zone='Faliraki',available=3)]
    allocation,_=optimize_assignments(cases,volunteers,{'beds':2},match_score)
    assert not allocation

@pytest.mark.parametrize('text',["He can't breathe at Lindos", "HE CANNOT BREATHE", "δεν αναπνέει στη Ρόδο", "ΚΑΡΔΙΑΚΉ ΑΝΑΚΟΠΉ ΣΤΗ ΛΊΝΔΟ"])
def test_normalized_safety_phrases(text):
    assert classify(text)['emergency_flag'], text
