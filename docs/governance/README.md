# Governance Documents

**Status:** Active governance index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md`
**Scope:** Local index for acceptance gates, agent rules, model/prompt governance, testing policy, reference policy, and documentation housekeeping.

---

## Purpose

This folder contains the rules that keep the repository contract-driven, phase-aligned, and reviewable.

Use this README to choose the right governance document before changing code, prompts, schemas, tests, docs, or model configuration.

---

## Core Governance Documents

These documents are part of the normal read path for substantial work.

| File | Role |
|------|------|
| `acceptance.md` | Defines gates, evidence requirements, completion status, and verification type. |
| `agent_guidelines.md` | Defines how AI coding agents may operate in the repository. |
| `model_governance.md` | Defines model, provider, prompt, benchmark, rollout, and rollback controls. |
| `docs_housekeeping.md` | Defines how documentation may be labeled, summarized, archived, or deleted. |

---

## Supporting Governance Policies

Read these when the task touches the related area.

| File | Use When |
|------|----------|
| `prompt_lifecycle.md` | Changing or promoting prompts, prompt versions, or prompt collections. |
| `testing_governance.md` | Changing test strategy, coverage expectations, benchmarks, or validation layers. |
| `REFERENCE_POLICY.md` | Managing reference material, source documents, or evidence-source expectations. |

---

## Quick Routing

| Task Type | Start With |
|-----------|------------|
| Marking work complete | `acceptance.md` |
| Implementing or reviewing agent-generated changes | `agent_guidelines.md` |
| Changing prompts, models, providers, or defaults | `model_governance.md` and `prompt_lifecycle.md` |
| Adding or changing tests and benchmarks | `testing_governance.md` |
| Moving, archiving, or deleting docs | `docs_housekeeping.md` |
| Handling source/reference material | `REFERENCE_POLICY.md` |

---

## Non-Negotiable Reminders

Governance cleanup or edits must not:

- weaken schemas,
- hide failed or partial acceptance status,
- switch model or prompt behavior without evidence,
- remove benchmark or rollback context,
- turn planning-only work into approved implementation scope,
- replace deterministic validation with undocumented human or LLM judgment.

---

## Maintenance

Update this README when:

- a governance document is added,
- a governance document changes responsibility,
- the required read path changes,
- a supporting policy becomes a core governance document.
