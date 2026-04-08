# AI Testing Platform — Upgrade Roadmap

> **Document Purpose**: This roadmap is designed to be read by LLMs as execution context when implementing upgrade tasks via API calls. Each phase contains explicit directives, file contracts, and machine-verifiable acceptance criteria. Human reviewers use this document to gate phase transitions.

---

## How LLMs Should Use This Document

When an LLM is invoked to implement any part of this roadmap, it MUST:

1. Identify the current phase and the specific task being requested.
2. Read the **Input Contract** for that task before generating any output.
3. Produce all outputs that satisfy the **Output Contract**.
4. Self-evaluate against the **Acceptance Criteria** and include a checklist in its output.
5. If a dependency from a prior task is missing, halt and report the gap — do not fabricate inputs.
6. All generated file content MUST be in English only.

---

## Current State

### What Exists (Developer Perspective — LME-Testing Repo)

The current system processes LME (London Metal Exchange) business rule documents through a linear pipeline:

```
Source Documents
  → Rule Extraction Scripts
  → atomic_rules.json
  → semantic_rules.json
  → Maker LLM   (generates BDD-style test scenarios)
  → Checker LLM (reviews coverage per rule_type → required_case_types)
  → Human Review Session (local HTTP server)
  → Rewrite (if Decision = rewrite)
  → Checker (re-run)
  → HTML Report
```

**Known gaps**: no schema validation on rule extraction output, no CI, maker/checker models are not version-locked, review session is single-user only, no support for document types beyond the current extraction scripts, zero automated tests of the framework itself.

### What the Target Looks Like (Tester Perspective — 15-Prompt Chain)

The tester-side design introduces:
- Structured paragraph IDs (`{DOMAIN}-{SUBDOMAIN}-{SEQ}`, e.g., `DC-IMRPF-001`)
- A 7-layer directory architecture (docs, processed, config, copilot-skills, tests, scripts, governance)
- A 15-prompt sequential chain covering: document ingestion → rule structuring → skill generation → test case generation → BDD scenario generation → execution → reporting → audit
- Template learning from existing `.feature` files to match team BDD style
- Step definition registry for mapping generated scenarios to existing automation
- Governance layer with audit trails, confidence scoring, and change tracking

The two perspectives must be unified into a single coherent platform.

---

## Phase 1 — Foundation Hardening

**Duration**: 4–6 weeks  
**Goal**: Make the existing pipeline reliable enough for LLMs to call it without silent failures, and establish the structural baseline for all subsequent phases.

---

### Task 1.1 — Rule Schema Validation

**Priority**: Critical  
**Why**: All downstream quality (maker output, checker coverage) depends on input rule quality. Currently there is no validation layer.

**Input Contract**:
- `artifacts/poc_two_rules/semantic_rules.json` — existing sample
- `lme_testing/pipelines.py` — to understand current field usage

**Implementation Directives**:
- Define JSON Schema files for both `atomic_rule` and `semantic_rule` objects.
- Store schemas at `config/schemas/atomic_rule.schema.json` and `config/schemas/semantic_rule.schema.json`.
- Add a `validate_rules(path)` function in `lme_testing/validation.py` that runs schema validation and returns a structured report.
- The report must include: total rules, valid count, invalid count, and per-rule error details.
- Integrate validation as the first step of the `maker` pipeline — if validation fails, abort with a clear error message and write the report to the run's `logs/` directory.

**Output Contract**:
```
config/schemas/
  atomic_rule.schema.json
  semantic_rule.schema.json
lme_testing/
  validation.py
```

**Acceptance Criteria**:
- [ ] Running `validate_rules()` on a deliberately malformed `semantic_rules.json` produces a structured error report and does not proceed to maker.
- [ ] Running `validate_rules()` on the POC sample passes with zero errors.
- [ ] The schema enforces: required fields (`rule_id`, `rule_type`, `description`), `rule_type` is one of the enumerated values, `required_case_types` is a non-empty array.
- [ ] Validation result is written to `logs/validation-report.json` in the run directory.

---

### Task 1.2 — Prompt and Model Version Locking

**Priority**: Critical  
**Why**: The maker and checker LLM calls are currently model-agnostic with no version tracking. Changing models or prompt wording changes output quality silently.

**Input Contract**:
- `lme_testing/providers.py` — current provider adapter
- `lme_testing/pipelines.py` — where maker/checker prompts are constructed

**Implementation Directives**:
- Create `config/model-config.json` specifying: `maker_model`, `checker_model`, `maker_prompt_version`, `checker_prompt_version`.
- Extract all maker and checker prompt templates into `config/prompts/maker_v{N}.txt` and `config/prompts/checker_v{N}.txt`.
- Modify `pipelines.py` to load prompts from config rather than constructing them inline.
- Record `model_name`, `prompt_version`, and `run_timestamp` in every artifact's metadata block.
- Add `--model-config` CLI flag to `main.py` allowing a custom config path.

**Output Contract**:
```
config/
  model-config.json
  prompts/
    maker_v1.txt
    checker_v1.txt
```

**Acceptance Criteria**:
- [ ] Every maker output artifact includes a `metadata.model` and `metadata.prompt_version` field.
- [ ] Swapping `maker_model` in `model-config.json` and re-running produces a new artifact with updated metadata — without any code changes.
- [ ] Running with an unknown model name raises a clear error before any LLM call is made.

---

### Task 1.3 — Framework CI

**Priority**: High  
**Why**: This is a testing tool with no tests of itself. Any code change is unverified.

**Input Contract**:
- `tests/` — existing directory (currently sparse)
- `artifacts/poc_two_rules/semantic_rules.json` — POC fixture

**Implementation Directives**:
- Create `.github/workflows/ci.yml` with two jobs: `unit-tests` and `e2e-smoke`.
- `unit-tests`: run pytest on `tests/unit/` covering `validation.py`, `reporting.py`, and `human_review.py`.
- `e2e-smoke`: run the full maker → checker pipeline on the POC sample using a stub LLM provider (returns deterministic mock responses, no real API calls), and assert that the output report file exists and contains the expected rule IDs.
- Create `lme_testing/providers_stub.py` implementing the same interface as `providers.py` but returning fixture responses from `tests/fixtures/`.
- CI must pass before any PR can be merged.

**Output Contract**:
```
.github/workflows/ci.yml
tests/
  unit/
    test_validation.py
    test_reporting.py
    test_human_review.py
  fixtures/
    maker_response_fixture.json
    checker_response_fixture.json
lme_testing/
  providers_stub.py
```

**Acceptance Criteria**:
- [ ] `pytest tests/unit/` passes with zero failures.
- [ ] The e2e smoke test completes end-to-end using the stub provider without making any real LLM API calls.
- [ ] The CI workflow runs on every push to `master` and on every PR.
- [ ] A deliberate bug introduced into `validation.py` causes the unit test job to fail.

---

### Task 1.4 — Structured Paragraph ID Integration

**Priority**: High  
**Why**: The tester-side design uses structured paragraph IDs (`{DOMAIN}-{SUBDOMAIN}-{SEQ}`) as the linking key between source document rules and generated test cases. The current system has no equivalent, making traceability impossible.

**Input Contract**:
- `lme_testing/pipelines.py`
- `config/schemas/semantic_rule.schema.json` (from Task 1.1)
- `scripts/` — existing extraction scripts

**Implementation Directives**:
- Add a `paragraph_id` field to the `semantic_rule` schema. Format: `{DOMAIN}-{SUBDOMAIN}-{SEQ}` where DOMAIN is 2–4 uppercase chars, SUBDOMAIN is the specific rule topic, SEQ is zero-padded 3 digits.
- Update extraction scripts to assign paragraph IDs during rule extraction.
- Add a uniqueness check in `validation.py`: if any two rules share a `paragraph_id`, validation fails.
- Propagate `paragraph_id` into all downstream artifacts: maker output test cases, checker coverage records, and HTML reports.
- The HTML report's coverage table must be sortable by `paragraph_id`.

**Output Contract**:
- Updated `config/schemas/semantic_rule.schema.json` with `paragraph_id` field
- Updated extraction scripts
- Updated `lme_testing/validation.py` with uniqueness check
- Updated `lme_testing/reporting.py` with `paragraph_id` column

**Acceptance Criteria**:
- [ ] POC sample rules all have unique, correctly formatted `paragraph_id` values.
- [ ] Attempting to load rules with duplicate `paragraph_id` values triggers a validation error.
- [ ] The final HTML report's coverage table includes a `paragraph_id` column.
- [ ] A test case artifact contains the `paragraph_id` of the rule it was generated from.

---

### Phase 1 Gate

Before proceeding to Phase 2, a human reviewer must confirm:

- [ ] All four Phase 1 tasks have passed their acceptance criteria.
- [ ] The CI workflow is green on `master`.
- [ ] The POC sample runs end-to-end cleanly: validate → maker → checker → review → report.
- [ ] `config/model-config.json` reflects the actual models being used.
- [ ] All output artifacts include `paragraph_id` and metadata fields.

**Gate sign-off file**: Create `governance/phase1-gate.md` with reviewer name, date, and checklist.

---

## Phase 2 — Enterprise Expansion

**Duration**: 6–10 weeks  
**Goal**: Expand document ingestion to multiple types, integrate the 15-prompt chain structure, generate BDD that maps to existing step definitions, and enable multi-team review.

---

### Task 2.1 — Multi-Document Type Ingestion

**Priority**: Critical  
**Why**: The current system is built around a single document format. Enterprise use requires PDF, Word (`.docx`), and Excel (`.xlsx`) ingestion with consistent output.

**Input Contract**:
- `scripts/` — existing extraction scripts
- `config/schemas/atomic_rule.schema.json`

**Implementation Directives**:
- Create `lme_testing/ingestion/` package with one adapter per document type:
  - `pdf_adapter.py` — extracts text and tables from PDF using a library (e.g., `pdfplumber` or equivalent)
  - `docx_adapter.py` — extracts structured content from Word documents
  - `xlsx_adapter.py` — extracts tabular rule data from Excel with configurable column mappings
- Each adapter must implement the same interface: `extract(filepath) -> List[AtomicRule]`.
- Add a `config/ingestion-config.json` file allowing column name mappings for Excel and section heading patterns for Word/PDF.
- After extraction, automatically assign `paragraph_id` values using the document's domain prefix defined in `ingestion-config.json`.
- Write extracted rules to `artifacts/{run_id}/atomic_rules.json` and immediately run Task 1.1 validation.

**Output Contract**:
```
lme_testing/ingestion/
  __init__.py
  pdf_adapter.py
  docx_adapter.py
  xlsx_adapter.py
  base_adapter.py
config/
  ingestion-config.json
```

**Acceptance Criteria**:
- [ ] Each adapter can process a sample file of its type and produce valid `atomic_rules.json` output.
- [ ] The extracted output passes Task 1.1 schema validation without modification.
- [ ] `paragraph_id` values are assigned and unique within each run.
- [ ] An unsupported file extension raises a clear error with guidance.
- [ ] The ingestion layer is covered by unit tests with sample fixture files.

---

### Task 2.2 — BDD Style Learning from Existing Feature Files

**Priority**: High  
**Why**: Generated BDD scenarios must match the team's existing Gherkin style, vocabulary, and step patterns — not generic defaults. This is the bridge between AI generation and existing test automation.

**Input Contract**:
- A directory of existing `.feature` files provided by the team (configured in `config/bdd-learning-config.json`)
- `lme_testing/pipelines.py`

**Implementation Directives**:
- Create `lme_testing/style_learner.py` that analyzes a corpus of `.feature` files and extracts:
  - Most common step verb patterns (Given/When/Then phrase structures)
  - Naming conventions for Feature, Scenario, and Scenario Outline blocks
  - Parameter patterns (e.g., `"<value>"` vs `{value}` vs table-driven)
  - Tag conventions (`@smoke`, `@regression`, etc.)
- Store the learned profile in `tests/bdd/learned/template-profiles.json` (matching the tester-side directory structure).
- The maker prompt must be updated to include the learned style profile as context when generating BDD scenarios.
- Add a `--learn-from` CLI flag to trigger style learning from a given directory before running maker.

**Output Contract**:
```
lme_testing/
  style_learner.py
tests/bdd/learned/
  template-profiles.json
  style-guide.md
config/
  bdd-learning-config.json
```

**Acceptance Criteria**:
- [ ] Given 10+ existing `.feature` files, `style_learner.py` produces a non-empty `template-profiles.json`.
- [ ] Maker-generated BDD scenarios, when reviewed by a human tester, are judged to match the team's style in at least 80% of cases.
- [ ] The style guide is human-readable and includes examples extracted from the corpus.
- [ ] Changing the input corpus changes the generated profile — confirmed by running on two different `.feature` file sets.

---

### Task 2.3 — Step Definition Registry

**Priority**: High  
**Why**: Generated BDD scenarios are only useful if their steps can be executed. The system must know which step definitions already exist and generate steps that match them — or flag new steps that need implementation.

**Input Contract**:
- Existing step definition files (Ruby/Cucumber or other framework) provided at a configured path
- `tests/bdd/learned/template-profiles.json` (from Task 2.2)

**Implementation Directives**:
- Create `lme_testing/step_registry.py` that parses existing step definition files and builds an index:
  - Pattern: the Gherkin step pattern (regex or Cucumber expression)
  - File: source file path
  - Line: line number
  - Parameters: list of parameter names/types
- Store the registry at `tests/bdd/step-registry.json`.
- During BDD generation, the maker must be instructed (via prompt) to prefer steps that match existing registry entries.
- After generation, a post-processing step compares generated steps against the registry and produces a `diff-report.md` in `tests/bdd/diff-reports/` listing:
  - **Matched steps**: generated steps with a matching registry entry (and the entry's location)
  - **New steps**: generated steps with no registry match, flagged for implementation
- New steps are marked with a `@needs-implementation` tag in the `.feature` file.

**Output Contract**:
```
lme_testing/
  step_registry.py
tests/bdd/
  step-registry.json
  diff-reports/
    diff-report-{run_id}.md
```

**Acceptance Criteria**:
- [ ] The registry correctly indexes all step patterns from a provided step definition file.
- [ ] A generated `.feature` file with 10 scenarios produces a diff report distinguishing matched vs. new steps.
- [ ] Steps matching existing registry entries use the same parameter style as the original definition.
- [ ] New steps are correctly tagged with `@needs-implementation`.
- [ ] The diff report is human-readable and actionable.

---

### Task 2.4 — Checker Stability Layer

**Priority**: High  
**Why**: The checker is an LLM — its judgments are probabilistic. Running once per test case is not reliable enough for enterprise use.

**Input Contract**:
- `lme_testing/pipelines.py`
- `config/model-config.json`

**Implementation Directives**:
- Extend `model-config.json` with a `checker_stability` block:
  ```json
  {
    "checker_stability": {
      "runs": 3,
      "aggregation": "majority_vote",
      "variance_threshold": 0.3
    }
  }
  ```
- Modify the checker pipeline to run each case `N` times (configurable, default 3).
- Aggregate results using majority vote for binary decisions (`approve`/`reject`) or average for scored outputs.
- If variance across runs exceeds `variance_threshold`, mark the result as `unstable` and surface it for human review with priority.
- Record all individual run results in the artifact metadata so the variance is auditable.

**Output Contract**:
- Updated `lme_testing/pipelines.py`
- Updated `config/model-config.json` schema

**Acceptance Criteria**:
- [ ] Running the checker 3 times on the same input produces 3 results, all recorded in the artifact.
- [ ] A case where runs disagree (2 approve, 1 reject) is flagged as `unstable` in the coverage report.
- [ ] Setting `runs: 1` in config produces the original single-run behavior.
- [ ] Unstable cases appear as a distinct section in the HTML report.

---

### Task 2.5 — Multi-User Review Session

**Priority**: Medium  
**Why**: The current review session is a local single-user HTTP server. Team review requires shared state and the ability to merge decisions from multiple reviewers.

**Input Contract**:
- `lme_testing/review_session.py`
- `lme_testing/human_review.py`

**Implementation Directives**:
- Extend the review session to support a file-based shared state model: review decisions are stored in `artifacts/{run_id}/reviews/{reviewer_id}.json`.
- Add a `merge-reviews` CLI command that reads all reviewer JSON files for a run and produces a merged `final-review.json` using configurable conflict resolution (default: flag conflicts for manual resolution).
- When two reviewers disagree on a decision, the merged result is `conflict` — surfaced as a separate category in the report.
- The review session web page gains a `Reviewer ID` input field (defaults to machine hostname) so multiple reviewers can run sessions concurrently against the same run directory (shared via network drive or Git).
- Export: the review session can export a portable `review-export.json` and import from a received file, enabling async review workflows.

**Output Contract**:
- Updated `lme_testing/review_session.py`
- New `lme_testing/review_merger.py`
- Updated `main.py` with `merge-reviews` command

**Acceptance Criteria**:
- [ ] Two reviewers each produce a `{reviewer_id}.json` file; `merge-reviews` produces a merged file.
- [ ] Cases where both agree produce a single final decision.
- [ ] Cases where they disagree are marked `conflict` in the merged file and highlighted in the report.
- [ ] Export and import of review files works without data loss.

---

### Task 2.6 — Governance Layer

**Priority**: Medium  
**Why**: Enterprise use requires an audit trail: who reviewed what, when, using which model version and prompt version, and what changed between runs.

**Input Contract**:
- All preceding task outputs
- `config/model-config.json`

**Implementation Directives**:
- Create `governance/` directory structure:
  ```
  governance/
    audit-trail.md         — append-only log of all pipeline runs
    change-history.md      — log of rule changes between document versions
    change-tracking/
      document-changes/    — diffs between ingested document versions
      rule-changes/        — diffs in semantic_rules.json between runs
      testcase-changes/    — diffs in generated test cases
      bdd-changes/         — diffs in generated .feature files
    reviews/
      executions/          — per-run review records (one sub-dir per run_id)
  ```
- At the end of every pipeline run, append a structured entry to `audit-trail.md` containing: `run_id`, `timestamp`, `document_source`, `model_config_version`, `prompt_versions`, `rule_count`, `case_count`, `coverage_rate`, `reviewer_decisions`.
- When a document is re-ingested after an update, generate a diff in `governance/change-tracking/document-changes/` and propagate impacted `paragraph_id` values to `rule-changes/`.

**Output Contract**:
```
governance/
  audit-trail.md
  change-history.md
  change-tracking/ (directory structure)
  reviews/executions/ (directory structure)
```

**Acceptance Criteria**:
- [ ] Running the pipeline twice produces two entries in `audit-trail.md`.
- [ ] Re-ingesting a modified document produces a change diff in `governance/change-tracking/document-changes/`.
- [ ] The audit trail entry includes model and prompt version information.
- [ ] The governance directory structure matches the specification exactly.

---

### Phase 2 Gate

- [ ] All Phase 2 tasks have passed their acceptance criteria.
- [ ] At least one non-LME document type (PDF or Word) has been ingested successfully end-to-end.
- [ ] Generated `.feature` files pass `--dry-run` in the team's Cucumber/BDD framework without syntax errors.
- [ ] The diff report correctly identifies at least one matched step and one new step.
- [ ] The governance audit trail contains at least three pipeline run entries.
- [ ] Phase 1 CI remains green.

**Gate sign-off file**: Create `governance/phase2-gate.md`.

---

## Phase 3 — Enterprise AI Testing Platform

**Duration**: 3–6 months  
**Goal**: Full enterprise capability — multi-domain document ingestion, automatic step definition generation, CI/CD gate integration, cross-run regression analysis, and a self-improving prompt system.

---

### Task 3.1 — Domain-Agnostic Document Pipeline

**Priority**: Critical  
**Why**: The system is currently coupled to LME financial documents. Enterprise use spans compliance documents, API specifications, regulatory frameworks, insurance policies, and more.

**Implementation Directives**:
- Introduce a `domain` concept in `ingestion-config.json`. A domain definition includes:
  - Document type hints (PDF/Word/Excel)
  - Section patterns that indicate rule boundaries
  - `paragraph_id` prefix mapping (`DOMAIN` part of the ID)
  - Known entity vocabularies (e.g., financial terms, risk parameters)
- The maker prompt is assembled dynamically from: base template + domain vocabulary + learned BDD style profile + step registry context.
- Create a `domains/` directory at repo root. Each sub-directory is a domain definition package with its own `domain-config.json`, sample documents, and POC fixture.
- The pipeline can be invoked with `--domain {name}` to load the corresponding domain config.

**Acceptance Criteria**:
- [ ] Two structurally different document domains (e.g., LME financial rules and a regulatory compliance document) can be processed by the same pipeline using different `--domain` flags.
- [ ] Each domain's generated BDD scenarios are coherent within that domain's vocabulary.
- [ ] Switching domains does not require code changes — only config.

---

### Task 3.2 — Auto Step Definition Generation

**Priority**: High  
**Why**: Task 2.3 flags new steps. This task closes the loop by generating stub step definitions for them automatically.

**Implementation Directives**:
- After BDD generation, read `diff-reports/diff-report-{run_id}.md` for steps tagged `@needs-implementation`.
- For each new step, generate a stub step definition in the team's target framework (Ruby/Cucumber by default, configurable in `config/bdd-learning-config.json`).
- The stub includes: the step pattern, parameter extraction, a `pending` placeholder body, and a comment linking back to the `paragraph_id` of the originating rule.
- Write stubs to `tests/bdd/steps/generated/` with a filename matching the `.feature` file they were generated for.
- Append all new stubs to the step registry (`tests/bdd/step-registry.json`).

**Acceptance Criteria**:
- [ ] Every step tagged `@needs-implementation` in a `.feature` file has a corresponding stub in `tests/bdd/steps/generated/`.
- [ ] Stubs are syntactically valid for the target framework (verified by running the framework's `--dry-run`).
- [ ] Each stub contains a comment with the originating `paragraph_id`.
- [ ] Newly generated stubs are added to the step registry.

---

### Task 3.3 — CI/CD Quality Gate

**Priority**: High  
**Why**: The platform is only valuable at enterprise scale if it blocks bad rule changes from reaching production — like a quality gate in traditional CI.

**Implementation Directives**:
- Add a `gate` CLI command: `python main.py gate --baseline {run_id} --current {run_id} --threshold 0.85`.
- The gate command compares two runs: the baseline (usually the last approved run) and the current run.
- It computes: coverage delta, new uncovered rules, rules whose checker verdict changed, and new `@needs-implementation` steps.
- Exit code 0 if all pass; exit code 1 if any threshold is breached (configurable thresholds in `config/gate-config.json`).
- Create `.github/workflows/quality-gate.yml` that runs the gate command on PR and blocks merge on exit code 1.
- The gate report is posted as a PR comment (structured Markdown).

**Acceptance Criteria**:
- [ ] Running `gate` between two identical runs produces exit code 0.
- [ ] Running `gate` where the current run has 5% lower coverage than baseline produces exit code 1.
- [ ] The GitHub Actions workflow posts the gate report as a PR comment.
- [ ] Coverage threshold is configurable without code changes.

---

### Task 3.4 — Cross-Run Regression Analysis

**Priority**: Medium  
**Why**: Teams need to see whether coverage is improving or degrading over time, and whether maker/checker quality has changed after a prompt update.

**Implementation Directives**:
- Create `lme_testing/regression.py` that reads the audit trail and computes time-series metrics:
  - Coverage rate over time (per `rule_type`)
  - Checker stability rate over time (% of cases with `unstable` verdicts)
  - Rewrite rate over time (% of cases requiring human rewrite)
  - New step rate over time (% of generated steps that are new)
- Add a `report-regression` CLI command that generates an HTML regression report in `artifacts/regression/`.
- The regression report includes trend charts (generated as SVG) and a summary table.

**Acceptance Criteria**:
- [ ] Given 5+ historical runs in the audit trail, `report-regression` generates a valid HTML report.
- [ ] The report shows at least 4 trend metrics as charts.
- [ ] A run with a deliberately lower coverage rate appears as a downward trend in the chart.

---

### Task 3.5 — Self-Improving Prompt System

**Priority**: Medium (Long-term)  
**Why**: Over time, patterns of human review decisions (rewrite/reject) contain signal about where maker prompts are systematically weak. This task feeds that signal back into prompt improvement.

**Implementation Directives**:
- Create `lme_testing/prompt_optimizer.py` that aggregates human review decisions across runs and identifies:
  - `rule_type` values with consistently high rewrite rates
  - Common failure patterns in checker rejection reasons
  - Step categories with consistently high `@needs-implementation` rates
- For each identified weakness, generate a candidate prompt improvement (an addendum to the maker or checker prompt) and write it to `config/prompts/candidates/`.
- Candidate prompts are NOT automatically applied — a human must promote them to `config/prompts/maker_v{N+1}.txt` and update `model-config.json`.
- The system tracks which candidate prompt was applied in which run via the audit trail.

**Acceptance Criteria**:
- [ ] Given 10+ runs with review data, `prompt_optimizer.py` produces at least one candidate prompt addendum.
- [ ] Candidate prompts are written to `config/prompts/candidates/` and not applied automatically.
- [ ] The audit trail records prompt version changes.
- [ ] Applying a candidate prompt and re-running the POC sample produces measurably different (intended to be better) maker output.

---

### Phase 3 Gate

- [ ] All Phase 3 tasks have passed their acceptance criteria.
- [ ] At least two different business domains have been processed end-to-end.
- [ ] Generated `.feature` files and stubs have been reviewed and merged into the team's test automation repository.
- [ ] The CI quality gate has blocked at least one PR in testing.
- [ ] The regression report covers at least 10 historical runs.
- [ ] The system has been used by at least two independent reviewers using the multi-user review session.

**Gate sign-off file**: Create `governance/phase3-gate.md`.

---

## LLM Execution Guidelines

These rules apply whenever an LLM is invoked via API to implement any task in this roadmap.

### Before Writing Any Code or Files

1. Confirm which task is being implemented by identifying its task ID (e.g., `Task 1.1`).
2. Read the **Input Contract** section. If any listed input file does not exist, report this and stop.
3. Read all **Acceptance Criteria** for the task. These are your definition of done.
4. Check whether any prior phase gate has been signed off in `governance/`. If a Phase 2 task is requested but `governance/phase1-gate.md` does not exist, flag this.

### Output Requirements

Every LLM implementation session MUST produce:
- All files listed in the **Output Contract**.
- A self-evaluation checklist at the end of the session, checking off each acceptance criterion as `PASS`, `PARTIAL`, or `FAIL` with reasoning.
- If any criterion is `FAIL`, the session is not complete — continue working.

### Stability Across Different Models

Because this roadmap may be executed by different LLMs (GPT-4, Claude, Gemini, etc.), all prompts and config files must be self-contained. No task implementation should depend on implicit context from a prior conversation — all necessary context must be in files readable from the repository.

Specifically:
- All prompt templates are files in `config/prompts/`, not strings embedded in code.
- All configuration is in `config/*.json`, readable with standard JSON parsers.
- All inter-task contracts are defined by schema files in `config/schemas/`.

### When Uncertain

If an implementation decision is ambiguous (e.g., a schema field type is not specified), choose the most conservative option, document the assumption in the output file's header comment, and add a `TODO: confirm with human reviewer` note.

---

## Directory Structure (End State)

```
project-root/
├── artifacts/                        # Per-run outputs
│   └── {run_id}/
│       ├── atomic_rules.json
│       ├── semantic_rules.json
│       ├── maker_output.json
│       ├── checker_output.json
│       ├── final-review.json
│       ├── logs/
│       └── report.html
├── config/
│   ├── model-config.json
│   ├── gate-config.json
│   ├── ingestion-config.json
│   ├── bdd-learning-config.json
│   ├── prompts/
│   │   ├── maker_v1.txt
│   │   ├── checker_v1.txt
│   │   └── candidates/
│   └── schemas/
│       ├── atomic_rule.schema.json
│       └── semantic_rule.schema.json
├── docs/
│   └── source-files/                 # Ingested and structured source documents
├── domains/                          # Domain definition packages
│   └── {domain-name}/
│       ├── domain-config.json
│       └── poc/
├── governance/
│   ├── audit-trail.md
│   ├── change-history.md
│   ├── change-tracking/
│   ├── reviews/
│   ├── phase1-gate.md
│   ├── phase2-gate.md
│   └── phase3-gate.md
├── lme_testing/
│   ├── ingestion/
│   ├── cli.py
│   ├── pipelines.py
│   ├── providers.py
│   ├── providers_stub.py
│   ├── validation.py
│   ├── style_learner.py
│   ├── step_registry.py
│   ├── review_session.py
│   ├── review_merger.py
│   ├── workflow_session.py
│   ├── regression.py
│   ├── prompt_optimizer.py
│   ├── reporting.py
│   ├── human_review.py
│   └── logging_utils.py
├── tests/
│   ├── unit/
│   ├── fixtures/
│   └── bdd/
│       ├── features/
│       ├── steps/
│       │   └── generated/
│       ├── learned/
│       │   ├── template-profiles.json
│       │   └── style-guide.md
│       ├── diff-reports/
│       └── step-registry.json
├── scripts/                          # Extraction and utility scripts
├── .github/workflows/
│   ├── ci.yml
│   └── quality-gate.yml
├── main.py
├── requirements.txt
├── ROADMAP.md                        # This file
└── README.md
```

---

## Summary

| Phase | Duration | Key Deliverables | Primary Stakeholder |
|---|---|---|---|
| Phase 1: Foundation | 4–6 weeks | Schema validation, CI, prompt versioning, paragraph IDs | Developer |
| Phase 2: Expansion | 6–10 weeks | Multi-doc ingestion, BDD style learning, step registry, governance | Tester + Developer |
| Phase 3: Enterprise | 3–6 months | Domain-agnostic pipeline, auto stubs, CI gate, regression analysis | Platform Team |

The central principle across all phases: **every artifact must be traceable to a `paragraph_id`, every `paragraph_id` must be traceable to a source document, and every LLM decision must be traceable to a model version and prompt version.**
