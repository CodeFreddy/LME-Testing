# Documentation Housekeeping Policy

**Status:** Active governance policy
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md`
**Scope:** Documentation organization, archiving, and cleanup rules

---

## Purpose

This policy defines how to keep the `docs/` tree clean, accurate, and friendly without losing governance history, evidence, or decision context.

Documentation in this repository is part of the system contract. Cleanup must therefore preserve traceability instead of treating older files as disposable notes.

---

## Core Rule

Prefer curation before deletion.

The safe order is:

1. label,
2. summarize,
3. cross-link,
4. archive,
5. delete only when explicitly safe.

Do not silently delete or rewrite context that records a contract, decision, benchmark, acceptance gate, rollback note, or source-material relationship.

---

## Document Classes

### Current Control Docs

These documents define the current repo contract and should stay concise, current, and internally consistent:

- `docs/planning/roadmap.md`
- `docs/planning/implementation_plan.md`
- `docs/governance/acceptance.md`
- `docs/architecture/architecture.md`
- `docs/governance/model_governance.md`
- `docs/governance/agent_guidelines.md`
- `docs/index.md`

Cleanup action: update and consolidate, not archive.

### Active Planning Docs

These documents describe open or upcoming work.

Cleanup action: keep in `docs/planning/`, add clear status metadata, and link to the owning roadmap or implementation-plan section.

### Evidence Summaries

These documents summarize validation results, benchmark outcomes, deterministic diffs, or baseline records.

Cleanup action: preserve unless the evidence has been migrated to an equivalent canonical record and linked from the relevant acceptance gate.

### Guides

These documents explain how to operate or develop the system.

Cleanup action: keep current with behavior. Archive only if the workflow is no longer supported and a replacement guide exists.

### Operations Docs

These documents preserve session continuity, handoff, and recoverable checkpoints.

Cleanup action: refresh according to the repository rules. Do not prune historical checkpoint records unless a human explicitly asks.

### Source Materials And References

These include PDFs, source conversions, historical prompts, and external comparison notes.

Cleanup action: do not rewrite for style. Archive or delete only with explicit preservation reasoning because they may explain artifact lineage.

### Archives

These preserve completed, superseded, demo, investigation, or historical records.

Cleanup action: keep discoverable through `docs/index.md` or a local archive note when the archived material remains useful.

---

## Required Metadata For New Planning Docs

New planning documents should start with:

```text
**Status:** Active / Draft / Proposed / Partial / Complete / Superseded / Archived
**Date:** YYYY-MM-DD
**Canonical owner:** roadmap / implementation_plan / acceptance / architecture / evidence / index
**Related roadmap task:** task ID or "None"
**Scope:** one-line boundary
```

If a document is superseded, also include:

```text
**Superseded by:** path
**Preservation reason:** why the old document remains useful
```

---

## Safe Archiving Rule

A planning or investigation document may move to `docs/archives/` when all of the following are true:

- the active status or final outcome is summarized in a current control doc,
- acceptance evidence is recorded where relevant,
- downstream documents no longer depend on its location,
- `docs/index.md` or another nearby index points to the archived record when useful,
- `python scripts/check_docs_governance.py` passes after the move.

Archiving should not change the meaning of the roadmap, acceptance status, architecture boundaries, or model/prompt governance.

---

## Safe Deletion Rule

Deletion is allowed only when all of the following are true:

- the file is not source material, evidence, an acceptance record, or a decision record,
- it is not linked from current control docs,
- its useful content exists elsewhere with equal or better detail,
- no artifact lineage depends on it,
- the deletion is mentioned in the change summary,
- documentation governance checks pass.

When in doubt, archive instead of deleting.

---

## Line-Level Cleanup Rule

For stale lines inside an otherwise current document:

- replace outdated status with the current status,
- keep a short note if the old statement explains an important decision,
- link to the newer canonical source,
- avoid rewriting past decisions as if they were always true.

Do not remove known limitations, failed checks, partial status, or blocked prerequisites just to make a document look cleaner.

---

## Recommended Cleanup Workflow

For a housekeeping pass:

1. Run or inspect `git status --short`.
2. Review `docs/index.md` and the target folder.
3. Classify each candidate file as current control, active planning, evidence summary, guide, operations, reference, or archive.
4. Add missing status metadata to active planning docs.
5. Consolidate repeated current-state text into the correct current control doc.
6. Archive only after the canonical current status is preserved elsewhere.
7. Run `python scripts/check_docs_governance.py`.
8. If artifact-related references changed, also run `python scripts/check_artifact_governance.py`.
9. Record the cleanup scope, files changed, validation, and rollback considerations in the final change summary.

---

## Candidate Actions

Use these labels in cleanup notes or inventories:

| Action | Meaning |
|--------|---------|
| Keep | File is current and in the right place. |
| Label | Add or refresh status metadata. |
| Summarize | Move repeated detail into a shorter pointer to a canonical source. |
| Merge | Fold useful content into a current control doc or active plan. |
| Archive | Move completed or superseded material to `docs/archives/`. |
| Delete Candidate | Consider deletion only after the safe deletion rule is satisfied. |

---

## Non-Negotiable Boundaries

Housekeeping must not:

- weaken artifact contracts,
- hide partial or failed acceptance status,
- remove benchmark evidence,
- erase prompt/model rollback context,
- convert planning-only work into approved implementation scope,
- claim production readiness by simplifying wording,
- prune checkpoints unless explicitly requested by a human.

---

## Summary

Good documentation housekeeping should make the current path easier to see while keeping the historical trail recoverable. The result should be less noise, not less truth.
