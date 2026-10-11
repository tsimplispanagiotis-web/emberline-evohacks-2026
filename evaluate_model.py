"""Reproducible local 5-fold cross-validation on synthetic training phrases.

Synthetic internal validation IS NOT an estimate of real-world safety or field performance.
"""
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from app.engine import CATEGORY_PHRASES, TRAINING_ADDITIONS

x,y=[],[]
for label,original in CATEGORY_PHRASES.items():
    examples=original+TRAINING_ADDITIONS[label]
    x.extend(examples)
    y.extend([label]*len(examples))

classifier=Pipeline([
    ('tfidf', TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),sublinear_tf=True)),
    ('classifier',LogisticRegression(max_iter=800,class_weight='balanced',random_state=42))
])
cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=2026)
predicted=cross_val_predict(classifier,x,y,cv=cv)
print(f'Synthetic labeled examples: {len(x)}')
print(f'Stratified 5-fold CV accuracy: {accuracy_score(y,predicted)*100:.1f}%')
print(classification_report(y,predicted,digits=3))
print('CAVEAT: synthetic in-domain CV, not held-out real disaster messages.')
