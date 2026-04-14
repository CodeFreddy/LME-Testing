# Roadmap TODO — All Phases Complete

## Phase 1 Completion (2026/04/13)

- [x] Artifact Schema Gate
- [x] Upstream Validation Pipeline Gate
- [x] Baseline CI Gate
- [x] Model and Prompt Metadata Gate
- [x] Stable Source Anchor Gate
- [x] Checker Stability Gate
- [x] Documentation Gate

## Phase 2 Gates (COMPLETE 2026/04/13)

- [x] **Gate 1: Multi-Document Ingestion** — Support multiple document classes with source-aware extraction
- [x] **Gate 2: Planning Layer** — Planner stage between semantic_rules and BDD generation
- [x] **Gate 3: Normalized BDD Contract** — Schema-validated intermediate BDD representation
- [x] **Gate 4: Traceability Gate** — Full source-to-BDD traceability in artifacts and reports
- [x] **Gate 5: Step Visibility Gate** — Surface reusable steps and gaps without execution binding
- [x] **Gate 6: Quality and Drift Reporting** — Reports showing baseline drift, unstable judgments
- [x] **Gate 7: Model Governance Enforcement Gate** — Benchmark checks before model/prompt adoption

## Phase 3 Post-Completion Items

These items are **not yet started** — they are next-phase work:

- [ ] **Web Portal BDD Stage** — Add BDD tab to review portal: display AI-generated normalized BDD per approved scenario, allow human to edit Given/When/Then steps in-browser, save to session snapshot for audit trail
- [ ] **Web Portal Scripts Stage** — Add Scripts tab: display generated Ruby step definitions, show step registry gap analysis (matched/unmatched/reuse score), allow human edits, save to session snapshot
- [ ] **Stage Progression UI** — Add explicit stage buttons (Maker Review → BDD Edit → Scripts Review → Finalize) with gate logic in portal session state

## Phase 3 Gates (COMPLETE 2026/04/14)

- [x] **Gate 1: Step Definition Integration** — 3-tier matching, reuse scores, ownership
- [x] **Gate 2: Execution Readiness** — ExecutableScenario schema with environment/input/hooks/assertions
- [x] **Gate 3: Deterministic Oracle** — Oracle modules for structured rule categories
- [x] **Gate 4: Governance Signals** — Schema failure rate, instability, binding success
- [x] **Gate 5: Release Governance** — Release tags, compatibility matrix, benchmark gates
- [x] **Gate 6: Phase 3 Exit** — All above
