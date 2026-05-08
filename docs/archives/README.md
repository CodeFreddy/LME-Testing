# Documentation Archives

**Status:** Active archive index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md` and `docs/governance/docs_housekeeping.md`
**Scope:** Index for completed, superseded, demo, investigation, and historical documentation records.

---

## Purpose

This folder preserves documentation that is no longer the active planning or control surface, but still has value for traceability, evidence review, rollback context, or historical understanding.

Archive records should not be treated as current implementation approval unless a current control document links to them as active evidence.

---

## Archive Rules

Before moving a document here, follow `docs/governance/docs_housekeeping.md`.

In short:

1. preserve current status in a control doc first,
2. update links to the archived path,
3. keep preservation reasons visible,
4. run documentation governance checks.

Do not archive source materials, acceptance evidence, decision records, or checkpoints just because they are old.

---

## Archived Records

| File | Status | Preservation Reason |
|------|--------|---------------------|
| `20260419_master_merge_strategy.md` | Historical merge strategy | Preserves the controlled master-branch merge rationale and cherry-pick decisions. |
| `20260422_ai_test_generation_demo.md` | Historical demo note | Preserves demo-oriented AI test generation context. |
| `20260422_script_generation_investigation.md` | Historical investigation | Preserves script-generation findings and constraints. |
| `s2t01_coverage_analysis.md` | Complete S2-T01 evidence summary | Current S2-T01 status is owned by implementation and acceptance docs; this preserves detailed root-cause analysis. |
| `stage2_planned_modules.md` | Complete S2-B1/B2 planning record | S2-B1/B2 are implemented; this preserves the original module-planning context from the master-branch analysis. |

---

## Use Guidance

Use archived docs to answer historical questions such as:

- why a decision was made,
- what evidence supported an old gate,
- what investigation found before implementation,
- what was intentionally not merged or promoted.

For current work, start from:

- `docs/planning/roadmap.md`
- `docs/planning/implementation_plan.md`
- `docs/governance/acceptance.md`
- `docs/index.md`
