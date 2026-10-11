from app.engine import classify, similarity, extract_zone, get_demand, match_score

def test_greek_classification():
    result=classify('Χρειαζόμαστε 5 μερίδες φαγητού για παιδιά στη Λίνδο.')
    assert result['category']=='Food'
    assert result['zone']=='Lindos'
    assert result['priority']=='HIGH'
    assert result['demand']==5

def test_numeric_water():
    result=classify('Please bring 12 litres of drinking water in Faliraki.')
    assert result['category']=='Water'
    assert result['demand']==12

def test_urgent_medical():
    out=classify('An unconscious man cannot breathe in Archangelos. Help now!')
    assert out['emergency_flag']
    assert out['priority']=='CRITICAL'
    assert out['needs_review']

def test_similarity():
    assert similarity('need drinking water at Faliraki','please bring drinking water at Faliraki')>similarity('need drinking water at Faliraki','need a bed in Lindos')

def test_stock_constraint():
    case={**classify('Need 20 litres of water in Faliraki'),'status':'OPEN','duplicate_of':None}
    volunteer={'skills':['Water'],'zone':'Faliraki','available':1}
    assert match_score(case,volunteer,{'litres':10})[0]<0
    assert match_score(case,volunteer,{'litres':25})[0]>0

def test_life_safety_block():
    case={**classify('unconscious man cannot breathe in Archangelos'),'status':'OPEN','duplicate_of':None}
    volunteer={'skills':['Medical'],'zone':'Archangelos','available':1}
    assert match_score(case,volunteer,{'kits':10})[0]<0

import pytest
from app.engine import RESOURCE_TYPES, INITIAL_STOCK, DEMO_MESSAGES

@pytest.mark.parametrize('message,label',[
    ('Our shelter is out of drinking water in Faliraki','Water'),
    ('Can a driver pick up two passengers in Kremasti','Transport'),
    ('Αναζητούμε κατάλυμα για απόψε στη Λίνδο','Shelter'),
    ('Χρειαζόμαστε φάρμακα και ινσουλίνη στην Ιαλυσό','Medical'),
    ('We need hot meals and bread for the evacuated families','Food'),
    ('I would like to register as a volunteer translator','Other'),
])
def test_demo_domain_classification(message,label):
    assert classify(message)['category']==label

@pytest.mark.parametrize('message,expected',[
    ('Need 18 litres of water in Faliraki',18),
    ('We need 3 passengers from Kremasti',3),
    ('Χρειαζόμαστε 5 μερίδες φαγητού στη Λίνδο',5),
    ('We need 2 beds for tonight',2),
])
def test_supply_amount_extraction(message,expected):
    assert classify(message)['demand']==expected

def test_case_sensitive_xss_is_content_not_markup():
    r=classify('Please deliver 4 litres of water in Faliraki <script>alert(1)</script>')
    assert r['category']=='Water'
    assert r['demand']==4

def test_volunteer_skill_prevents_assignment():
    case={**classify('Need urgent food packs in Lindos'),'status':'OPEN','duplicate_of':None}
    volunteer={'skills':['Medical'],'zone':'Lindos','available':8}
    assert match_score(case,volunteer,{'meals':100})[0]<0

def test_late_duplicate_does_not_reserve():
    case={**classify('Need 5 litres of water in Faliraki'),'status':'DUPLICATE','duplicate_of':'R-1001'}
    volunteer={'skills':['Water'],'zone':'Faliraki','available':1}
    assert match_score(case,volunteer,{'litres':100})[0]<0
