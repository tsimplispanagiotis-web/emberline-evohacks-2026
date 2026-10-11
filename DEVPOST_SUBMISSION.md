# Devpost: EMBERLINE — From Chaos to Coordinated Action

**Tagline:** Beyond a disaster chatbot: multilingual AI triage, mathematically optimal resource plans, and read-only resilience simulations — with humans in control.

**Built with:** Python · FastAPI · scikit-learn · TF-IDF · logistic regression · SciPy/HiGHS · mixed-integer optimization · SQLite · vanilla JavaScript · CSS · pytest.

## Inspiration

When disaster hits, community volunteers can receive scattered messages in different languages: someone needs insulin, another group needs water, another needs transport. The hardest part is not just interpreting each message — it's coordinating a whole collection of requests without counting the same inventory twice. We wanted to automate time-consuming administrative work *without* handing life-changing decisions to an opaque AI.

## What it does

EMBERLINE turns unstructured Greek/English messages into classified, reviewable aid requests. It extracts likely supply amounts and locations, flags possible duplicate reports and life-threatening phrases, and computes an inventory- and capacity-feasible *proposal* for matching cases with six fictional volunteers. Humans inspect the explanation and explicitly approve every reservation. The dashboard records decisions, generates unsent communication drafts, and exports a traceable audit report. **It never dispatches anyone. All data are fictional.**

## How we built it

We trained a six-label multilingual text classifier using character n-gram TF-IDF and class-balanced logistic regression. Rule-based extraction looks for locations, quantities and urgent warning language; a separate cosine-similarity system flags potentially duplicate reports. We coupled the probabilistic NLP front-end with a **0–1 mixed-integer programming solver (HiGHS)**. Its binary decisions maximize a transparent utility function subject to hard per-volunteer slot and per-resource stock constraints. This lets the whole group of assignments be optimized jointly, rather than approving individually plausible but mutually incompatible suggestions.

The **Scenario Lab** independently solves counterfactual plans under a 75% meal shortage, volunteer absence, combined disruptions or additional supplies. It shows before/after coverage, reassigned cases and objective change, *without* changing actual simulated inventory or audit state.

All workflow actions are available through FastAPI and an interactive dark operations dashboard. SQLite stores the synthetic state and an audit trail. We added explicit safety blocks, manual correction/rejection/override controls, and automatic reoptimization after an approval so pending suggestions never silently overspend the remaining resources.

## What makes it original

**Probabilistic understanding, mathematical certainty about simplified capacity constraints, and human authority in one end-to-end loop.** Unlike an AI assistant that merely generates text, EMBERLINE can explain both *why* it proposes a particular assignment and *why* it refuses to automate a critical request. A synthetic adversarial test demonstrates the difference between a flexible volunteer prematurely consumed by greedy selection and the globally optimized solution that assigns both requests.

## Challenges we faced

The central design challenge was combining uncertain language predictions with non-negotiable numeric constraints. A model might infer that someone needs water, but the requested litres and the available supplies must not be hallucinated. We used learned ML for language understanding, explicit constraints for inventory and human review for uncertainty. We also tackled the problem of stale assignments: after one human approval, the remaining proposals are recomputed using the actual new stock and volunteer capacity.

## Accomplishments

The demonstration handles **11 fictional bilingual messages** with one probable duplicate and one critical safety alert. For the included test scenario, the solver currently finds **8 feasible proposals**, all subject to human approval. **143 automated tests pass**, including an adversarial case where integer programming delivers both feasible assignments instead of the one that an unfortunate greedy choice could allow. The suite also includes 80 seeded optimization problems verified against an independent exhaustive-search reference, and tests proving that the Scenario Lab does not mutate live sandbox state. We tested desktop and narrow-mobile Scenario Lab interactions in Chromium without uncaught JavaScript errors.

Our 80 randomized five-case MILP checks independently match brute-force enumeration and demonstrate mathematical correctness on that bounded test distribution. In the included scripted what-if, **8 covered requests become 7 under a 75% meal shortage**; removing one volunteer results in **3 reassigned cases** while preserving coverage. These are fictional benchmark outcomes, not field-impact statistics.

An independently reproducible stratified cross-validation on our **206 deliberately synthetic training phrases** yields **78.6% in-domain classification accuracy**. This number does not validate performance in real disaster conditions, and model probabilities are not calibrated for life-safety decisions. The prototype is **not for real emergencies**.

## What we learned

The meaningful boundary in applied AI isn't just what can be automated; it's what must remain understandable and under human control. We can combine a small local classifier, explicit mathematical optimization and a transparent approval system without relying on an expensive remote foundation model or hiding how decisions are made.

## What's next

The next steps would be independent multilingual validation, reliable emergency detection, uncertainty calibration, fairness-aware allocation, verified travel times, privacy protection and role-based access, and only then a carefully scoped pilot supervised by emergency-management specialists. There are **no claims of real-world users, partnerships, rescues or field deployment**.

## Required links (fill in before submission)

- **PUBLIC source repository:** [INSERT PUBLIC GITHUB/GITLAB URL]
- **Video demo 2–3 minutes:** [INSERT PUBLIC/UNLISTED VIDEO URL]
- **Run instructions:** in the public repository README (`python -m uvicorn app.main:app`).
- **Live URL (optional):** Only include an independently verified deployment of **this same FastAPI version**. The separately hosted Lovable web prototype is NOT the identical codebase.
