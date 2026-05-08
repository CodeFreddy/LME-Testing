# Mock API Deliverables Policy

**Status:** Current Stage 2 policy
**Decision date:** 2026-04-26
**Canonical owner:** `docs/planning/implementation_plan.md` sections S2-C1 through S2-C4
**Related roadmap task:** S2-C1, S2-C2, S2-C3, S2-C4
**Decision:** Keep current mock API samples under `deliverables/`; do not move to `samples/` or `tools/` now.

---

## Decision

For the current Stage 2 baseline, mock API bridge source folders and packaged zip handoffs remain under `deliverables/`.

This applies to:

- `deliverables/lme_mock_api/`
- `deliverables/lme_mock_api.zip`
- `deliverables/im_hk_v13_mock_api/`
- `deliverables/im_hk_v13_mock_api.zip`
- `deliverables/im_hk_mock_api_common/`
- `deliverables/im_hk_v14_mock_api/`
- `deliverables/im_hk_v14_mock_api.zip`

No directory move is authorized by this policy.

---

## Rationale

The current mock APIs are reviewable handoff packages and evidence-backed execution bridge samples. Keeping them under `deliverables/` avoids churn after the HKv13/HKv14 bridge work and preserves existing validation commands, zip packaging paths, and documentation references.

---

## Revisit Trigger

Revisit this policy before adding a new mock API bridge or turning the mock APIs into maintained internal tools.

At that point, choose explicitly between:

- keeping `deliverables/` as the long-lived location,
- moving runnable examples to `samples/`,
- moving maintained mock bridge tooling to `tools/mock_apis/`,
- or splitting source samples from packaged handoff zips.

Any future move must update tests, docs, validation plans, zip packaging commands, and handoff guidance in the same change.

---

## Boundaries

- This is a documentation and repository organization policy only.
- No schemas, prompts, default models, artifact contracts, or roadmap phase boundaries change.
- This does not make any mock API a real LME, VaR Platform, HKSCC, HKEX, or production Initial Margin execution environment.

---

## Self-Evaluation

| Item | Status | Notes |
| --- | --- | --- |
| Human decision captured | PASS | User selected option 4 on 2026-04-26. |
| No file move authorized | PASS | Current paths remain stable. |
| Revisit trigger defined | PASS | Revisit before a new mock bridge or tool promotion. |
| Contract impact explicit | PASS | No schema, prompt, model, or artifact contract impact. |
