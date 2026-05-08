# Source Materials

**Status:** Active materials index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md` and `docs/governance/REFERENCE_POLICY.md`
**Scope:** Local index for source documents and source-derived materials used by governed artifacts.

---

## Purpose

This folder stores source materials that feed or explain governed extraction workflows.

Materials are not planning notes. They are lineage inputs. Do not rewrite, summarize, or delete them just to make the documentation folder look cleaner.

---

## Current Materials

| File | Role |
|------|------|
| `LME Matching Rules August 2022.pdf` | Source PDF for LME matching rules. |
| `LME_Matching_Rules_Aug_2022.md` | Markdown conversion/source text used by rule extraction and mock API validation. |
| `Initial Margin Calculation Guide HKv13.pdf` | Source PDF for Initial Margin HKv13 governed artifacts and mock bridge work. |
| `Initial Margin Calculation Guide HKv14.pdf` | Source PDF for Initial Margin HKv14 governed intake and diff work. |

---

## Preservation Rules

- Preserve original source files unless a human explicitly approves removal.
- Do not edit source materials to fix downstream extraction issues; fix the extractor or record a derived artifact instead.
- If a conversion is regenerated, preserve the source lineage and update affected artifact/evidence records.
- Do not move files without updating artifact generation paths, planning references, and governance checks.

---

## Placement Rules

Add files here when they are:

- original source documents,
- source-derived text used as extraction input,
- stable reference material directly tied to artifact lineage.

Do not place planning proposals, generated evidence outputs, run outputs, release notes, or checkpoint prompts here.

---

## Related Records

Source-derived governed artifacts live outside this folder, for example:

- `artifacts/`
- `evidence/`
- `deliverables/`

Planning and acceptance records should link back to these materials when the source document matters for traceability.
