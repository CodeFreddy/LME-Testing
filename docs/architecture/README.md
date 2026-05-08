# Architecture Documents

**Status:** Active architecture index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md`
**Scope:** Local index for the main architecture contract and supporting architecture design records.

---

## Purpose

This folder contains the system boundary and design records for the repository.

Use this README to distinguish the current architecture contract from supporting design notes and future-facing proposals.

---

## Current Architecture Contract

| File | Role |
|------|------|
| `architecture.md` | Main system boundary, pipeline map, module map, known limitations, and architecture review checklist. |

For substantial implementation work, treat `architecture.md` as the canonical architecture source unless a more specific current control document explicitly overrides it.

---

## Supporting Architecture References

| File | Role |
|------|------|
| `run_directory_structure.md` | Documents run output layout and timestamp expectations. |
| `rule_model_and_parsing_design.md` | Captures rule model and parsing design detail. |
| `Executable_Engineering_Knowledge_Contract.md` | Broader architecture proposal and MVP concept source for later governed slices. |

---

## Use Guidance

Read `architecture.md` when:

- changing module boundaries,
- changing pipeline behavior,
- adding or removing artifact flow steps,
- changing traceability expectations,
- changing review-session or rule-workflow-session responsibilities,
- assessing whether a change crosses current phase boundaries.

Read supporting references only when the task touches their specific area.

Do not treat future-facing architecture proposals as implementation approval. Promotion into baseline work requires an explicit roadmap task, acceptance path, validation, and rollback considerations.

---

## Maintenance

Update this README when:

- a new architecture document is added,
- a supporting design note becomes current contract,
- an architecture proposal is superseded or archived,
- the main architecture read path changes.
