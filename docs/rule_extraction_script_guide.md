# Rule Extraction Script Guide

## Purpose

This document explains how the current extraction scripts turn source documents into governed rule artifacts.

It is written for developers and AI coding agents who need to:

- run the extraction pipeline,
- understand the current output artifacts,
- inspect where deterministic extraction ends and first-pass semantic normalization begins,
- and avoid treating this stage as a shortcut to later-phase BDD or execution work.

This document should be read together with:

- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/architecture.md`
- `docs/rule_model_and_parsing_design.md`
- `docs/acceptance.md`

---

## Current Scope

The current extraction pipeline has two scripts:

1. `scripts/extract_matching_rules.py`
   - extracts pages, clauses, and `atomic_rule` records from a source PDF or Markdown file
2. `scripts/generate_semantic_rules.py`
   - converts `atomic_rules.json` into first-pass `semantic_rules.json`

This pipeline is an upstream artifact-governance step.
It is not the same thing as:

- planning,
- normalized BDD generation,
- Gherkin export,
- step integration,
- or execution-ready scenario generation.

Those belong to later roadmap phases.

---

## High-Level Flow

The current intended flow is:

`source document -> pages -> clauses -> atomic_rules.json -> semantic_rules.json`

This flow exists to create governed intermediate artifacts that can later support:

- traceability,
- validation,
- review,
- maker/checker inputs,
- and later normalized BDD work.

The practical rule is simple:

- extraction scripts should produce stable, reviewable artifacts
- they should not try to collapse the whole downstream design pipeline into one step

---

## Source Inputs

### Supported formats

`extract_matching_rules.py` supports:

- `.pdf`
- `.md`
- `.markdown`

If `--input-format` is omitted, the script auto-detects from the file suffix.

### Recommended source

For repeatable extraction, prefer the maintained Markdown source when available:

- `docs/materials/LME_Matching_Rules_Aug_2022.md`

Markdown is easier to diff, inspect, and stabilize than raw PDF extraction.

### PDF vs Markdown

PDF support exists because the original source may only be available in PDF.
However, PDF extraction is inherently less stable because it depends on:

- page-stream parsing,
- text normalization,
- header removal,
- and cleanup of source noise.

Use Markdown as the working baseline when possible.

---

## Script 1: `extract_matching_rules.py`

### Purpose

This script extracts deterministic upstream artifacts from the source document:

- `metadata.json`
- `pages.json`
- `clauses.json`
- `atomic_rules.json`

If requested, it also writes one normalized text file per page.

### Main arguments

#### `--input`

Required path to the source PDF or Markdown file.

Example:

```powershell
python scripts/extract_matching_rules.py `
  --input "docs/materials/LME_Matching_Rules_Aug_2022.md"
```

#### `--input-format`

Optional explicit input format:

- `auto`
- `pdf`
- `md`

Default:

```text
auto
```

#### `--output-dir`

Output artifact directory.

Default:

```text
artifacts/matching_rules
```

Example:

```powershell
python scripts/extract_matching_rules.py `
  --input "docs/materials/LME_Matching_Rules_Aug_2022.md" `
  --output-dir "artifacts/lme_rules_v2_2"
```

#### `--doc-id`

Stable document identifier stored in metadata.

Default:

```text
lme_matching_rules_v2_2
```

#### `--doc-title`

Document title stored in metadata.

Default:

```text
LME Matching Rules
```

#### `--doc-version`

Document version stored in metadata.

Default:

```text
2.2
```

#### `--write-page-text`

When enabled, writes one normalized text file per extracted page under `pages/`.

---

## Script 2: `generate_semantic_rules.py`

### Purpose

This script converts `atomic_rules.json` into first-pass `semantic_rules.json`.

The output is intentionally a first-pass governed semantic artifact.
It should be treated as:

- structured normalization,
- traceability-preserving interpretation,
- and a stable upstream input to later review or maker/checker flows.

It should not be treated as a direct substitute for later planning, normalized BDD, or execution contracts.

### Main arguments

#### `--input`

Path to `atomic_rules.json`.

Default:

```text
artifacts/lme_rules_v2_2/atomic_rules.json
```

#### `--output`

Path to `semantic_rules.json`.

Default:

```text
artifacts/lme_rules_v2_2/semantic_rules.json
```

#### `--metadata`

Optional path to `metadata.json`.

If omitted, the script looks for `metadata.json` in the output directory.

#### `--doc-id` / `--doc-title` / `--doc-version`

Fallback document metadata used when the metadata file is absent or incomplete.

---

## Recommended Commands

### Markdown baseline run

```powershell
python scripts/extract_matching_rules.py `
  --input "docs/materials/LME_Matching_Rules_Aug_2022.md" `
  --output-dir "artifacts/lme_rules_v2_2" `
  --doc-id "lme_matching_rules_v2_2" `
  --doc-title "LME Matching Rules" `
  --doc-version "2.2" `
  --write-page-text

python scripts/generate_semantic_rules.py `
  --input "artifacts/lme_rules_v2_2/atomic_rules.json" `
  --output "artifacts/lme_rules_v2_2/semantic_rules.json"
```

### PDF run

```powershell
python scripts/extract_matching_rules.py `
  --input "docs/materials/LME Matching Rules August 2022.pdf" `
  --output-dir "artifacts/lme_rules_pdf"

python scripts/generate_semantic_rules.py `
  --input "artifacts/lme_rules_pdf/atomic_rules.json" `
  --output "artifacts/lme_rules_pdf/semantic_rules.json"
```

Use the PDF path only when the Markdown baseline is unavailable or needs cross-checking.

---

## Output Artifacts

### From `extract_matching_rules.py`

Expected artifacts:

- `metadata.json`
- `pages.json`
- `clauses.json`
- `atomic_rules.json`

Optional artifacts when `--write-page-text` is enabled:

- `pages/page_001.txt`
- `pages/page_002.txt`
- and so on

### From `generate_semantic_rules.py`

Expected artifact:

- `semantic_rules.json`

---

## What Each Stage Is Responsible For

### `extract_matching_rules.py`

This script is responsible for deterministic upstream extraction:

- source format detection,
- page extraction,
- clause splitting,
- `atomic_rule` splitting,
- initial `rule_type` and `testability` guesses,
- and metadata capture.

It should be stable, reproducible, and conservative.

It should not:

- invent downstream test scenarios,
- collapse ambiguity into overconfident semantics,
- or behave like a full semantic reasoning pipeline.

### `generate_semantic_rules.py`

This script is responsible for first-pass semantic normalization:

- stable `semantic_rule_id` generation,
- source traceability carry-forward,
- semantic classification,
- normalized statement fields,
- type-specific payload construction,
- evidence packaging,
- and basic test design hints.

It should preserve enough structure for downstream governance and review.

It should not:

- pretend to be the final semantic truth,
- bypass human review where uncertainty is high,
- or replace later-phase governed artifacts such as planner outputs or normalized BDD contracts.

---

## Current Behavioral Notes

### Extraction script behavior

`extract_matching_rules.py` currently includes logic for:

- PDF page-stream extraction using the standard library,
- Markdown page extraction from `## Page N` sections,
- cleanup of common source noise,
- clause splitting,
- subclause-aware `atomic_rule` splitting,
- and deterministic JSON artifact writing.

This means the script is already doing important upstream governance work.
Changes here should be treated as high-impact because they affect the denominator and traceability basis for later stages.

### Semantic generation behavior

`generate_semantic_rules.py` currently performs heuristic normalization for fields such as:

- actor
- action
- object
- tags
- priority
- conditions
- constraints
- outcome
- type-specific payload

It also carries forward source information and evidence into `semantic_rules.json`.

Because this stage uses heuristics, its outputs should be treated as governed first-pass artifacts, not as unquestionable canonical truth.

---

## Review Expectations

After running extraction, review should focus on:

- whether clauses were split at the right boundaries,
- whether `atomic_rule` records are conservative and traceable,
- whether `rule_type` guesses are plausible,
- whether `semantic_rule` source links still point back to the right atomic records,
- whether evidence remains short and attributable,
- and whether obviously over-inferred fields are being introduced.

This review is especially important before using the artifacts for maker/checker runs.

---

## Governance Notes

### 1. Upstream artifacts come first

Do not treat maker/checker quality as a reason to ignore extraction quality.
If `atomic_rules.json` or `semantic_rules.json` drift, the downstream pipeline inherits the problem.

### 2. Stable traceability matters

The extraction stage is where source anchoring begins.
If the repo later strengthens paragraph-level or clause-level anchors, this script layer is where that groundwork must remain stable.

### 3. Do not skip governed intermediate artifacts

This pipeline exists to produce reviewable artifacts.
Do not replace it with direct document-to-scenario generation in normal repo workflows.

### 4. Do not overstate semantic certainty

Fields inferred by heuristic logic should remain distinguishable from explicit source facts.
When in doubt, preserve evidence and traceability rather than forcing confidence.

---

## Common Risks

### PDF instability

PDF extraction may produce noisy text, page boundary issues, or clause segmentation drift.

### Markdown drift

If the maintained Markdown source changes formatting conventions, page extraction or clause splitting may need adjustment.

### Over-eager semantic normalization

If `generate_semantic_rules.py` becomes too aggressive, it may:

- blur source facts and inferred facts,
- reduce reviewability,
- or make downstream artifacts look more certain than they are.

### Broken downstream assumptions

If field names, enums, or traceability structure change here, downstream maker/checker and reporting code may also require updates.

---

## Recommended Working Order

1. Start from the maintained Markdown source when possible.
2. Run `extract_matching_rules.py`.
3. Inspect `metadata.json`, `clauses.json`, and `atomic_rules.json`.
4. Run `generate_semantic_rules.py`.
5. Inspect `semantic_rules.json` before using it as downstream input.
6. Only then proceed to maker/checker or later validation flows.

---

## AI Agent Rules

Any AI coding agent editing this stage should follow these rules.

### 1. Do not bypass deterministic extraction with prompt-only shortcuts

If extraction behavior changes, fix the extraction logic or schemas rather than moving hidden logic into prompts.

### 2. Do not treat first-pass semantic rules as later-phase contracts

`semantic_rules.json` is not a replacement for planner outputs, normalized BDD, or execution-ready artifacts.

### 3. Preserve traceability fields

Do not remove or weaken source metadata, atomic rule references, or evidence fields without updating the governing docs and downstream consumers.

### 4. Keep input/output assumptions explicit

If a script argument, artifact shape, or default output path changes, update this document and related implementation docs.

### 5. Prefer baseline stability over aggressive inference

When a tradeoff exists, choose the design that keeps upstream artifacts more reproducible and reviewable.

---

## Related Files

- [extract_matching_rules.py](../scripts/extract_matching_rules.py)
- [generate_semantic_rules.py](../scripts/generate_semantic_rules.py)
- [rule_model_and_parsing_design.md](./rule_model_and_parsing_design.md)
