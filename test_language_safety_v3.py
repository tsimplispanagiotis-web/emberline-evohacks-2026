"""Explicitly documented small sets of safety phrases; not a field-recall claim."""
from app.engine import classify, extract_zone, ZONES
import pytest

@pytest.mark.parametrize('message,expected',[('Φαγητό στη Ρόδο','Rhodes Town'),('χρειαζόμαστε νερό στο Αρχάγγελο','Archangelos'),('help στην Ιαλυσό','Ialyssos'),('transport from Kremasti','Kremasti'),('beds στη Λίνδο','Lindos'),('water στο Φαληράκι','Faliraki')])
def test_morphology_zone_variants(message,expected):
    assert extract_zone(message)==expected

@pytest.mark.parametrize('text',["He is choking in Lindos",'Στον Αρχάγγελο λιποθύμησε ένας άνθρωπος',
 'Στη Ρόδο δεν έχει σφυγμό', 'The patient has no pulse in Kremasti',
 'A child collapsed and not responding in Faliraki', 'Έχασε τις αισθήσεις της στην Ιαλυσό'])
def test_known_severe_safety_phrases_override_ml(text):
    case=classify(text)
    assert case['emergency_flag'] is True
    assert case['needs_review'] is True
    assert case['priority']=='CRITICAL'
    assert case['category']=='Medical'
