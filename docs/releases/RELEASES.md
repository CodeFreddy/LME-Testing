# Release Governance

This directory contains release records for LME-Testing.

Release naming: `RELEASE-<major>.<minor>.<patch>-<date>.md`

Example: `RELEASE-1.0.0-20260414.md`

## Release Record Format

Each release record must include:
- Release version and date
- Phase gates completed
- Breaking changes (if any)
- Approved providers
- Benchmark evidence
- Rollback notes

## Current Release

| Release | Date | Phase | Status |
|---------|------|-------|--------|
| 1.0.0 | 2026-04-14 | Phase 3 Gate 1-4 | Current |

## Release History

### Release 1.0.0 (2026-04-14)

**Phase:** Phase 3 — Execution Readiness and Selective Enterprise Controls

**Gates Completed:**
- Gate 1: Step Definition Integration ✅
- Gate 2: Execution Readiness ✅
- Gate 3: Deterministic Oracle ✅
- Gate 4: Governance Signals ✅

**Approved Providers:**
- `stub` (Tier 1, all roles)
- `minimax/MiniMax-M2.7` (Tier 1, all roles)

**Benchmark Evidence:**
- Schema validation: 0% failure rate
- Checker instability: 0% (stub-only runs are deterministic)
- Coverage: 100% on poc baseline
- Step binding rate: 35.4% (step library not yet populated)

**Artifact Contracts:**
- `atomic_rule.schema.json`
- `semantic_rule.schema.json`
- `maker_output.schema.json`
- `checker_output.schema.json`
- `executable_scenario.schema.json` (Phase 3 Gate 2)
- `normalized_bdd.schema.json`
- `planner_output.schema.json`

**Breaking Changes:** None

**Rollback Notes:** Revert to Phase 2 artifacts by checking out prior commit. All Phase 3 artifacts are additive.
