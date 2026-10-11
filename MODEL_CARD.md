# EMBERLINE text classifier — Model Card

**Task.** Classify short Greek and English requests into six demonstration categories: Medical, Water, Food, Transport, Shelter, Other.

**Method.** TF-IDF character n-grams (2–5) followed by class-balanced logistic regression. Category probabilities are shown in the interface. A separate deterministic safety detector looks for narrowly defined life-threatening phrases and takes precedence over classification for emergency escalation; this is not guaranteed to recognize every emergency. Quantity/zone parsing is rule-based. A separate TF-IDF cosine similarity stage helps flag possible duplicate requests.

**Training data.** 206 deliberately synthetic, hand-authored, labeled requests. They do not contain real personal data, field reports, or a sampled representation of disaster communities. This model has not been trained or evaluated on actual disaster communications.

**Local reproducible evaluation (October 11, 2026).** A 5-fold stratified cross-validation was applied to the labeled synthetic training set (shuffle=True, random_state=2026). All vectorization and fitting were performed inside each training fold to avoid test-feature leakage. Aggregate accuracy: **78.6%** (162/206). Macro-average F1: approximately **0.785**.

| Category | Synthetic CV precision | Synthetic CV recall | Synthetic CV F1 |
| --- | ---: | ---: | ---: |
| Food | .800 | .706 | .750 |
| Medical | .833 | .833 | .833 |
| Other | .806 | .853 | .829 |
| Shelter | .694 | .735 | .714 |
| Transport | .719 | .676 | .697 |
| Water | .861 | .912 | .886 |

**Validation caveat.** The training corpus contains related phrasings and repeated domain terms; therefore, even cross-validation may overstate performance on unfamiliar, short, colloquial, dialectal, mixed-language, distressed or misspelled real messages. The figures above cannot establish model robustness in a crisis. No real-world recognition accuracy, life-safety recall, or operational throughput benefit is claimed.

**Known limitations.** Only two languages, narrow geographic lexicon, pattern-based extraction, no named-entity disambiguation, no fraud resistance, no identity validation, limited contextual understanding, and probabilistic confidence that has not been separately calibrated. Parsing may miss written-out quantities and multiple needs in one message. Duplicate similarity does not establish real identity. The integer-program optimizer is optimal only for a simplified utility model; geographic zone matching does not compute real routes. Model probabilities are not calibrated for safety-critical use.

**Risk controls.** When critical phrases are detected, volunteer dispatch is blocked and emergency-services escalation is recommended. No assignment is sent externally. Manual review tags highlight certain cases but are not a replacement for human verification. Confirmation happens before resources are deducted. The prototype must not be used to manage real emergencies or personal information.

**Reproduction.** `python evaluate_model.py` after `pip install -r requirements.txt`.
