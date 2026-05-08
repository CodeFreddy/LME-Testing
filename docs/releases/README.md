# Release Records

**Status:** Active releases index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md`
**Scope:** Local index for release notes, baseline records, and release-governance summaries.

---

## Purpose

This folder preserves release-facing records and named baselines.

Release records should summarize what was accepted, verified, or baselined. They should not replace roadmap tasks, acceptance gates, or detailed evidence artifacts.

---

## Current Records

| File | Role |
|------|------|
| `RELEASES.md` | Release history and release-governance notes. |
| `BASELINE-183-RULES.md` | Full 183-rule baseline record and review summary. |

---

## Placement Rules

Add a document here when it is primarily:

- a release note,
- a named baseline,
- a release readiness summary,
- a release-governance record.

Do not place active task plans, raw run outputs, checkpoint prompts, source materials, or future architecture proposals here.

---

## Maintenance Rules

- Keep release records linked to acceptance evidence where relevant.
- Preserve baseline records unless a newer baseline explicitly supersedes them.
- Do not rewrite historical release claims to sound more complete than the evidence supports.
- Run `python scripts/check_docs_governance.py` after link or path changes.
