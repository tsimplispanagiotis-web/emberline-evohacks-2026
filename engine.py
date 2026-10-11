"""EMBERLINE: interpretable on-device text ML + capacity-aware task assignment.

All data here is SYNTHETIC. Not a validated emergency-response model.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity
from .training_additions import TRAINING_ADDITIONS

CATEGORY_PHRASES = {
  'Medical': [
    'My grandmother needs insulin and medication urgently', 'First aid kit required for cuts and burns',
    'Χρειαζόμαστε φάρμακα και ινσουλίνη για τη γιαγιά', 'Χρειάζομαι φαρμακευτική περίθαλψη',
    'We ran out of asthma inhalers and medical supplies', 'A child requires prescribed medicine',
    'Need a first aid volunteer and antiseptic bandages', 'Παρακαλώ φέρτε γάζες και αντισηπτικό',
    'Someone is injured and we need bandages', 'Medicine delivery requested at the community center',
    'Need insulin for my father at the shelter', 'We need a nurse for a minor injury'
  ],
  'Water': [
    'Please deliver drinking water to the shelter', 'We are out of clean bottled water',
    'Χρειαζόμαστε πόσιμο νερό στο κέντρο φιλοξενίας', 'Δεν έχουμε νερό για να πιούμε',
    'Requesting 10 litres of water for children', 'Bring bottles of fresh water',
    'Residents need water as soon as possible', 'Water bottles needed at the gymnasium',
    'Hydration supplies required for evacuated families', 'Ζητάμε 12 λίτρα νερό'
  ],
  'Food': [
    'Need sandwiches and meals for evacuated families', 'Our group needs food packs',
    'Χρειαζόμαστε φαγητό για τα παιδιά', 'Λείπουν γεύματα και τρόφιμα από το σχολείο',
    'Please deliver 8 food portions', 'Food donations required at our center',
    'We have no meals for tonight', 'Bring snacks and ready-to-eat food',
    'Warm meals needed for evacuees', 'Ζητάμε 5 μερίδες φαγητού'
  ],
  'Transport': [
    'Need a driver to take our family to a safe location', 'Car and transport for two elderly residents',
    'Χρειαζόμαστε μεταφορά για ηλικιωμένους', 'Ζητάμε αυτοκίνητο για εκκένωση',
    'Can someone drive us to the community center', 'We require a wheelchair accessible ride',
    'Need a shuttle or van for three passengers', 'Pickup needed for a family without a car',
    'Transport assistance from the bus stop', 'Χρειαζόμαστε οδηγό και 2 θέσεις'
  ],
  'Shelter': [
    'Looking for two beds for tonight', 'Need a safe place to sleep and blankets',
    'Χρειαζόμαστε κατάλυμα και κρεβάτια', 'Ψάχνουμε ασφαλή στέγαση για την οικογένεια',
    'A temporary shelter is needed for evacuees', 'Is there accommodation available nearby',
    'We need room for 3 people overnight', 'Requesting blankets and somewhere to stay',
    'Can you find us space in a shelter', 'Ζητάμε χώρο φιλοξενίας για τρία άτομα'
  ],
  'Other': [
    'I can volunteer at the community center', 'Where are the information updates',
    'Έχω μια γενική ερώτηση για το κέντρο', 'Πού θα βρω πληροφορίες',
    'I found a lost backpack', 'Please share the contact number for the coordinator',
    'I would like to help with translations', 'What are the opening hours of the school',
    'How do I join as a helper', 'I have some donated boxes',
  ]
}
ZONES = ['Rhodes Town','Ialyssos','Kremasti','Faliraki','Archangelos','Lindos']
ZONE_ALIASES = {
 'Rhodes Town':['rhodes town','rhodes city','rhodes center','ροδος','ρόδος','ρόδο','ρόδου','πολη ροδου','πόλη της ρόδου','πολη της ροδου'],
 'Ialyssos':['ialyssos','ialysos','ιαλυσός','ιαλυσος','ιαλυσό','ιαλυσού'],
 'Kremasti':['kremasti','κρεμαστή','κρεμαστη'],
 'Faliraki':['faliraki','φαληράκι','φαληρακι','φαληράκι,'],
 'Archangelos':['archangelos','αρχάγγελος','αρχαγγελος','αρχάγγελο','αρχαγγελο','αρχαγγέλου'],
 'Lindos':['lindos','λίνδος','λινδος','λίνδο','λινδο'],
}
SYNONYMS = {'Medical':['medicine','insulin','medication','φάρμακα','φαρμακα','injured','αιμορραγ'],
'Water':['water','νερό','νερο'],'Food':['food','meals','φαγητό','φαγητο'],
'Transport':['ride','drive','pickup','transport','μεταφορά','μεταφορα'],
'Shelter':['shelter','beds','sleep','κατάλυμα','καταλυμα','στέγαση','στεγαση']}
RESOURCE_TYPES = {'Medical':'kits','Water':'litres','Food':'meals','Transport':'seats','Shelter':'beds','Other':'none'}
BASE_DEMAND = {'Medical':1,'Water':5,'Food':2,'Transport':1,'Shelter':1,'Other':0}
RISK_PHRASES = ['unconscious','cannot breathe','can not breathe',"can't breathe",'cant breathe',
 'not breathing','stopped breathing','severe bleeding','chest pain','heart attack','trapped in fire',
 'life threatening','cardiac arrest','καρδιακη ανακοπη','δεν αναπνεει','δεν αναπνεω','αιμορραγει',
 'χωρισ αισθησεισ','δεν εχει αισθησεισ','εχασε τισ αισθησεισ',
 'δεν εχει σφυγμο','λιποθυμησε','πνιγεται','choking','no pulse',
 'collapsed and not responding','δυσκολια στην αναπνοη']
URGENCY_PHRASES = ['urgent','urgently','asap','immediately','right now','tonight','elderly','baby','children','child','insulin',
 'επείγον','επειγον','τώρα','τωρα','άμεσα','αμεσα','παιδιά','παιδια','ηλικιωμέν']

def normalize(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s.casefold()) if not unicodedata.combining(ch)).replace("ς", "σ")

@lru_cache(maxsize=1)
def model() -> Pipeline:
    x,y=[],[]
    for label,examples in CATEGORY_PHRASES.items():
        examples=examples+TRAINING_ADDITIONS[label]
        x.extend(examples);y.extend([label]*len(examples))
    pipe=Pipeline([('tfidf',TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),sublinear_tf=True)),
                   ('classifier',LogisticRegression(max_iter=800, class_weight='balanced',random_state=42))])
    pipe.fit(x,y)
    return pipe

@lru_cache(maxsize=1)
def similarity_vectorizer():
    corpus = [s for c,v in CATEGORY_PHRASES.items() for s in (v+TRAINING_ADDITIONS[c])]
    return TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5)).fit(corpus)

def similarity(a: str,b: str) -> float:
    v=similarity_vectorizer().transform([a.lower(),b.lower()])
    return float(cosine_similarity(v[0],v[1])[0,0])

def extract_zone(text: str) -> str:
    low=normalize(text)
    for zone,aliases in ZONE_ALIASES.items():
        if any(normalize(a) in low for a in aliases):return zone
    return 'Unspecified'

def get_demand(text: str, category: str) -> int:
    demand=BASE_DEMAND[category]
    if not demand:return 0
    lower=text.lower()
    if category=='Water':
        m=re.search(r'\b(\d{1,2})\s*(?:l(?:itres?|iters?)?|λίτρα|λιτρα)\b',lower)
    elif category=='Transport':
        m=re.search(r'\b(\d{1,2})\s*(?:passengers?|people|persons|seats|θέσεις|θέση|ατομα|άτομα)\b',lower)
    elif category=='Shelter':
        m=re.search(r'\b(\d{1,2})\s*(?:beds?|people|persons|κρεβάτια|κρεβατια|άτομα|ατομα)\b',lower)
    elif category=='Food':
        m=re.search(r'\b(\d{1,2})\s*(?:meals?|portions?|μερίδες|μεριδες|γεύματα|γευματα)\b',lower)
    else:m=None
    return min(30,max(1,int(m.group(1)))) if m else demand

def classify(text: str) -> dict[str,Any]:
    p=model().predict_proba([text])[0]
    cls=model().named_steps['classifier'].classes_
    i=int(p.argmax()); cat=str(cls[i]); confidence=round(float(p[i]),3)
    low=normalize(text)
    # Classification itself is learned. This narrow safety-sensitive override handles out-of-distribution phrases.
    if confidence<0.34:
        matches=[c for c,phrases in SYNONYMS.items() if any(normalize(q) in low for q in phrases)]
        if len(matches)==1:cat=matches[0]
    emergency=any(normalize(term) in low for term in RISK_PHRASES)
    if emergency: cat='Medical'
    urgent=any(normalize(term) in low for term in URGENCY_PHRASES)
    priority='CRITICAL' if emergency else 'HIGH' if (urgent or cat=='Medical') else 'NORMAL'
    return {'category':cat,'confidence':confidence,'zone':extract_zone(text),'priority':priority,
            'demand':get_demand(text,cat),'resource':RESOURCE_TYPES[cat],
            'emergency_flag':emergency,
            'needs_review':confidence<0.23 or extract_zone(text)=='Unspecified' or emergency,
            'model':'Local multilingual character n-gram TF-IDF + logistic regression (synthetic training examples)',
            'confidence_caveat':'Uncalibrated, synthetic-training model probability; NOT a safety guarantee'}

def match_score(case:dict,volunteer:dict,stock:dict) -> tuple[float,str]:
    category=case['category']
    if case.get('duplicate_of') or case.get('status') not in ('OPEN','MATCHED'):return (-1000,'Not eligible')
    if case.get('emergency_flag'):return (-1000,'Critical safety flag requires emergency services review')
    if category=='Other':return (-1000,'General requests require human triage')
    if category not in volunteer['skills']:return (-1000,'Missing required skill')
    if volunteer['available']<=0:return (-1000,'No volunteer capacity')
    if stock.get(RESOURCE_TYPES[category],0)<case['demand']:return (-1000,'Insufficient stock')
    local=volunteer['zone']==case['zone']
    score=72+(18 if local else 0)+(8 if case['priority']=='HIGH' else 0)
    if case['zone']=='Unspecified':score-=20
    return (float(score),'Same-zone specialist' if local else 'Cross-zone qualified volunteer')

DEMO_MESSAGES = [
 'Urgent: my grandmother needs insulin near Ialyssos. We need medical supplies today.',
 'At Faliraki shelter, we need 12 litres of clean drinking water for families.',
 'Need 3 seats in a car from Kremasti to the community center, ASAP.',
 'Χρειαζόμαστε 5 μερίδες φαγητού για παιδιά στη Λίνδο.',
 'At the shelter in Faliraki, please bring 12 litres of drinking water for our families.',
 'Looking for 2 beds for elderly relatives in Rhodes Town tonight.',
 'An unconscious man cannot breathe in Archangelos. Send help immediately.',
 'Need bandages and a medical kit for a minor injury in Lindos.',
 'We need food packs for displaced families near Archangelos.',
 'Can someone help us with a ride from Ialyssos?',
 'Where can I find the latest community update?',
]
VOLUNTEERS = [
 {'id':'V-01','name':'Maya','skills':['Medical','Shelter'],'zone':'Ialyssos','available':2},
 {'id':'V-02','name':'Nikos','skills':['Transport'],'zone':'Kremasti','available':2},
 {'id':'V-03','name':'Elena','skills':['Water','Food'],'zone':'Faliraki','available':2},
 {'id':'V-04','name':'Leo','skills':['Shelter','Food'],'zone':'Rhodes Town','available':2},
 {'id':'V-05','name':'Sofia','skills':['Medical','Water'],'zone':'Lindos','available':2},
 {'id':'V-06','name':'Theo','skills':['Food','Transport','Shelter'],'zone':'Archangelos','available':2},
]
INITIAL_STOCK={'kits':3,'litres':30,'meals':12,'seats':5,'beds':3}
