# EMBERLINE 3.0 — From Chaos to Coordinated Action

**EvoHacks 2026 • AI for Automation • Built October 11, 2026**

> A multilingual, accountability-first relief workflow prototype that converts chaotic incoming requests into **auditable, globally optimized *proposals***, with hard resource constraints and mandatory human approval.

![Actual EMBERLINE 3.0 Scenario Lab](media/EMBERLINE_v3_ResilienceLab.png)

**This is a synthetic, educational project — NOT validated for emergency use. Do not enter real personal information or use for actual dispatch.** The application sends no calls, emails, messages or aid requests.

## One-minute tour

Imagine volunteers coordinating supplies after a disaster. Messages arrive in different languages and repeat each other. An urgent request for insulin, a request for water, and a request for beds can all compete for finite resources. EMBERLINE automates the *paperwork*, not the final decision:

1. **Ingest** 11 fictional English/Greek requests (or write any new request).
2. **Classify** with locally trained TF-IDF character n-grams and a six-class logistic regression model — not hard-coded answers.
3. **Extract** zone, demand and safety phrases; flag unknown data for manual verification.
4. **Deduplicate** with TF-IDF cosine similarity; show suggestions, not automatic merges.
5. **Optimize** with a **binary mixed-integer linear program** (HiGHS) that maximizes an explicitly documented utility score under exact resource and volunteer-capacity limits. This replaces the previous greedy approach.
6. **Explain** the rationale and whether the solver certified the result optimal for the simplified mathematical model.
7. **Approve** each proposal manually; only approval reserves inventory and slots. The remaining plan is automatically reoptimized.
8. **Stress-test** counterfactuals in the **Scenario Lab**: simulate a 75% meal shortage, a missing volunteer, water scarcity or new supplies; compare both optimized plans without changing the real synthetic state.
9. **Audit** and export decisions to JSON. Dispatch drafts are marked **NOT SENT**.

**Safety invariant:** Life-threatening phrases put cases on CRITICAL hold, prevent automatic volunteer assignment, and prominently recommend actual emergency services. Our phrase detector does *not* guarantee it finds every emergency; the prototype is not a medical or disaster response product.

## The innovation

Most AI hackathon projects end with a label or a chatbot response. EMBERLINE links **probabilistic NLP → deterministic safety → duplicate suggestions → integer programming → human-authorized state transitions → persistent audit → read-only counterfactual resilience planning**.

The operational challenge is not only *which volunteer should take which request*, but whether the **whole plan is feasible**. A greedy matcher may waste a flexible volunteer on a task a specialist could handle, leaving another task uncovered. EMBERLINE solves a 0–1 mixed-integer program instead. One included adversarial regression test demonstrates two assignments where a naive greedy choice would permit only one. **Additionally, 80 seeded random small instances are checked against an independent exhaustive-search oracle**, verifying the MILP objective and every capacity constraint.

### What the integer program actually guarantees

For all binary assignment decisions `x[case, volunteer]`:

- **At most one** volunteer proposed per case.
- **At most `available`** pending assignments per volunteer.
- **Total required units ≤ remaining stock** of each resource category.
- A potential assignment is created only when category/skill, inventory, review and safety constraints permit it.
- Approved cases are immutable, and proposals are recomputed after every approval, rejection, review or new intake.

Objective (synthetic): maximize `sum(utility(case,volunteer) × x)` where higher-priority needs have more utility and same-zone volunteers receive a preference bonus. **Optimality is relative to this limited objective**. It is not an optimal real-world emergency response plan or a real travel-time calculation.

## Run it

**Quick start:** on macOS/Linux run `bash start_mac_linux.sh`; on Windows double-click `start_windows.bat` (Python 3.10+ required). Both install local dependencies and start the server at `http://127.0.0.1:8000`.


**Python 3.10+** (recommended: Python 3.11–3.13):

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**, click **Process sample inbox**, then **Generate smart assignments**. Inspect a case to see **Why this match?**, edit an uncertain prediction, approve/reject a proposal, and view the audit ledger.

The sandbox stores state in a local SQLite file. Reset from the UI. To specify another database location: `EMBERLINE_DB=/path/to/demo.sqlite3`.

Alternatively, with Docker:

```bash
docker build -t emberline .
docker run --rm -p 8000:8000 emberline
```

## Tests — verified October 11, 2026

```bash
python -m pytest -q
# 143 passed
python evaluate_model.py
# 206 synthetic examples; 78.6% stratified 5-fold CV accuracy (not field accuracy)
```

Tests cover classification, Greek/English inflected locations and emergency phrases, resource feasibility, an adversarial flexible-volunteer case, **80 randomized solver-vs-brute-force oracle problems**, prevention of duplicate/emergency assignments, sequential approval resource invariants, scenario immutability, manual review, API validation and end-to-end workflows.

A Chromium DOM+interaction smoke test, with requests bridged to the actual FastAPI backend, exercised the Scenario Lab at desktop and 390px mobile widths; the prior v2 browser tests also covered ingestion, optimization, human review/approval, duplicates, safety holds, drafts, inventory and audit. No uncaught JavaScript errors were observed. New screenshots are `media/EMBERLINE_v3_*.png`.

## Reproducible model evaluation

The classifier is trained on **206 hand-authored synthetic examples**, covering six categories in English and Greek. `evaluate_model.py` runs stratified 5-fold cross-validation, training a fresh vectorizer/model within each fold to avoid feature leakage. The aggregate test-set accuracy is **78.6% on synthetic in-domain phrases**; performance on actual disaster communications, recall on high-risk requests and uncertainty calibration are unknown. See [`MODEL_CARD.md`](MODEL_CARD.md).

The UI shows *model-estimated probabilities*; they are **not** independently calibrated confidence guarantees. Emergency phrase rules are separate from the model and must not be considered a reliable life-safety system.

## Tech stack and architecture

```text
Browser: responsive HTML/CSS/vanilla JS
   |   -- intake, filters, inspect/explain, approve/reject/review, export
   v
FastAPI (Python) --> SQLite (fictional cases, supplies, volunteers, decisions)
   |
   +-- NLP: scikit-learn TF-IDF + logistic regression
   +-- Rule extraction: zone, numeric demand, critical safety triggers
   +-- Deduplication: TF-IDF cosine similarity
   +-- Optimization: SciPy HiGHS 0–1 MILP
   +-- Invariants + human-review state machine
   +-- Audit ledger and NOT SENT dispatch drafts
```

Not a foundation model or external API. No LLM key required. No live data source, person tracking, automated notifications or rescue service integration. It runs locally. The separate hosted Lovable preview is **not** an identical deployment of this FastAPI source repository and should not be represented as such.

## Project structure

| Path | Contents |
| --- | --- |
| `app/engine.py` | Trained NLP model, extraction, similarity, eligibility rules |
| `app/optimizer.py` | Binary integer program, hard constraints, rationale + optimality diagnostics |
| `app/scenario.py` | Read-only counterfactual simulations, before/after allocations and deltas |
| `app/main.py` | REST API, review/approval transitions, SQLite, safety + audit |
| `app/static/` | Full responsive dark command center, accessible interactive elements |
| `tests/` | 143 parametrized unit, randomized-oracle and integration tests |
| `evaluate_model.py` | Synthetic 5-fold model evaluation |
| `media/` | Real recorded video and screenshots |
| `DEVPOST_SUBMISSION.md` | Draft Devpost submission |
| `HOW_TO_SUBMIT_GR.md` | Greek submission checklist |

## Boundaries and next steps

Before any real-world pilot, EMBERLINE would need verified responders, emergency-operations expertise, sensitive data safeguards, role-based access, location accuracy, consent, language and safety validation, independent trials and robust incident-response procedures. This build makes **no** claims about real-world impact or emergency readiness.

### Reproducible counterfactual lab

Open the live *local* dashboard, run **Process sample inbox**, click **Generate smart assignments**, then scroll to **What if the plan breaks?**. Select **Food shortage (75% fewer meals)**. On the included fictional data, the optimum goes from **8 to 7 proposed matches**. Change to **Volunteer absence (Elena)**: coverage remains **8**, but **3 assignments change volunteers**. No stock, volunteer slots or history entries are modified by these analyses.

The code implementing this is in `app/scenario.py` and the scenario endpoints are `GET /api/scenarios`, `POST /api/scenario`. Exact outcomes are deterministic for this test fixture; these are not disaster-response forecasts or social-impact measurements.

MIT License · October 11, 2026.
