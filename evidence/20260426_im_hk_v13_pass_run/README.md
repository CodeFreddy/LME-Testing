# HKv13 Pass Run Backup

**Purpose:** Backup of the latest completed Initial Margin Calculation Guide HKv13 run.

**Source document:** `docs/materials/Initial Margin Calculation Guide HKv13.pdf`

**Run chain:**
- Maker: `runs/im_hk_v13/maker/20260425T221152Z/`
- Checker: `runs/im_hk_v13/checker/20260426T002536Z/`
- Deterministic BDD export: `runs/im_hk_v13/bdd_deterministic/20260426T015751Z/`
- Step registry: `runs/im_hk_v13/step-registry/20260426T015803Z/`
- Review session: `runs/im_hk_v13/review_sessions/20260426T020242Z/`

**Completion signals:**
- Review session status: `finalized`
- Checker `remaining_after_resume`: `0`
- Maker scenarios generated: `178`
- Checker reviews generated: `178`
- BDD feature files generated: `60`
- Step registry total steps: `996`

**Contents:**
- `maker/20260425T221152Z/` — maker cases, raw responses, excluded rules, quality report, summary
- `checker/20260426T002536Z/` — checker reviews, raw responses, coverage report, summary
- `bdd_deterministic/20260426T015751Z/` — normalized BDD, generated features, step definitions, summary
- `step-registry/20260426T015803Z/` — step visibility report
- `review_sessions/20260426T020242Z/` — finalized review session manifest, report artifacts, audit trail
- `reports/` — top-level final HTML/CSV and readable maker/checker reports
- `source_artifacts/` — governed HKv13 semantic rules, validation report, metadata, extracted markdown

**Notes:** This is an evidence backup only. It does not change schemas, prompts, models, provider defaults, or pipeline contracts.
