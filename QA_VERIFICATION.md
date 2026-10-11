# EMBERLINE 3.0 — Reproducible Verification

**Build date:** October 11, 2026. All sample messages and people are fictional; not fit for any real emergency.

## Tests

`python -m pytest -q` → **143 passed** (last checked on October 11, 2026). Includes:

- 41 original unit/API/workflow checks from EMBERLINE 2.0.
- 10 new counterfactual checks for deterministic simulation, zero state mutation, and untouched approved reservations.
- 80 seeded *random optimization problems*, where a separate exhaustive-search oracle matches the MILP optimum and every stock/volunteer limit is satisfied.
- 12 additional Greek location morphology and critical-safety phrase cases.

`node --check app/static/app.js` → passed. Python `compileall` → passed.

## Mathematical & synthetic benchmarks

`python benchmark.py`: two covered cases with MILP vs one with naive first-fit greedy in a deliberately crafted adversarial example, proven *only for that instance*.

`python evaluate_model.py`: **206 synthetically written examples**, six labels, 5-fold stratified accuracy **78.6%**, with vectorizer and classifier fitted only to training folds. Not representative of real field data.

## Browser verification

Chromium interaction checks exercised the unchanged client HTML/CSS/JS, bridged to real local FastAPI JSON responses, without browser-origin networking:

- 11-message import, optimizer (8 pending proposals), Scenario Lab 75% meal stock loss → 7 proposals, volunteer absence → 3 different assignments.
- API state unchanged by running Scenario Lab; tests confirm no audit, stock or approval changes.
- 1512px desktop and 390px mobile views. No uncaught JavaScript exceptions in tested flows.
- The earlier v2 core browser smoke test covered human approvals, resources, rejection, emergency hold, duplicate override, audit and NOT SENT draft. The v3 recording adds Scenario Lab.

## Safety & scope

**Never use for real dispatch, rescues, medical decision support or real personal information.** The critical phrase detector has unknown recall, and model probabilities are uncalibrated; the app contains no verified responder roster or travel-time model. Exact MILP optimality only concerns a specified synthetic utility function and shared capacities, not outcomes in disaster operations. The SQLite store uses only process-local locking and has no authentication; this is a local demonstration sandbox, *not* deployable as a safe public multi-user operations system.
