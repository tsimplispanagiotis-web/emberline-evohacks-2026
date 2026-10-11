# EMBERLINE 3.0 — Judge Quick Start

**AI for Automation → Safety-aware multilingual triage + exact integer optimization + human review.**

**Watch:** `media/EMBERLINE_v3_EvoHacks_Demo.mp4` (2–3 minutes, real screen recording, original instrumental music + captions; no spoken narration).

**Run:** `pip install -r requirements.txt && python -m uvicorn app.main:app` → open `http://127.0.0.1:8000` → click **Process sample inbox** → **Generate smart assignments**.

**Stress-test:** Run Scenario Lab below the solver diagnostics → Food shortage 75%: 8→7 coverage; Volunteer absence: 8 retained, 3 reassigned. These are read-only calculations and leave the active sandbox unchanged.

**Interact:** inspect a proposed request → read **Why this match?** → approve (inventory changes) → check Resource Network and audit ledger. Inspect a CRITICAL case (never autonomously assigned) and a DUPLICATE case (human override available). Enter your own synthetic Greek or English request and correct uncertain fields.

**Reproducible evidence:** `python -m pytest -q` → 143 tests; `python benchmark.py` → greedy first-fit can handle only one request in an adversarial example while HiGHS MILP finds two; `python evaluate_model.py` → 78.6% stratified CV on 206 *synthetic* examples.

**What is new technically?** An independent counterfactual optimization engine and 80 seeded test problems checked against a brute-force oracle, in addition to an exact 0–1 mathematical optimization model for proposed volunteer matches with shared resource constraints, explainability and automatic reoptimization after every approval. AI language classification is real local ML, but the system is emphatically not validated for life safety or field use.

**Ethical boundary:** No real users, data, dispatch, calls, emergency responders, rescue outcomes or external notifications. This is a fictional sandbox; probabilities are uncalibrated and duplicate detection is advisory only.
