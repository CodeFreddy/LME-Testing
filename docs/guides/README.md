# Guides

**Status:** Active guides index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md`
**Scope:** Local index for operator and developer guides.

---

## Purpose

This folder contains practical guides for using and operating repository workflows.

Guides should explain how to perform an existing workflow. They should not approve new roadmap scope, redefine artifact contracts, or replace acceptance criteria.

---

## Current Guides

| File | Role |
|------|------|
| `maker_checker_usage.md` | Explains maker/checker CLI usage and workflow expectations. |
| `rule_extraction_script_guide.md` | Explains rule extraction script usage and operational notes. |

---

## Placement Rules

Add a document here when it is primarily:

- a user guide,
- an operator runbook,
- a developer workflow guide,
- a troubleshooting note for an existing approved workflow.

Do not place roadmap plans, governance policies, source materials, acceptance evidence, or session checkpoints here.

---

## Maintenance Rules

- Keep guides aligned with implemented behavior.
- Link to canonical contracts instead of duplicating long governance sections.
- If a workflow is deprecated, update the guide with a replacement path or archive it after the replacement is documented.
- Run `python scripts/check_docs_governance.py` after link or path changes.
