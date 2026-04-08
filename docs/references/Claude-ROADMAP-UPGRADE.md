# LME-Testing Enterprise AI Testing Upgrade Roadmap

**Version:** 1.0.0  
**Date:** 2026-04-08  
**Audience:** Developers, QA Leads, Automation Engineers  
**Purpose:** Guide stable, phased development when calling different LLM APIs to evolve this repo into enterprise-grade AI-driven testing infrastructure.

---

## Background: Two Perspectives, One System

This roadmap synthesises two inputs:

1. **Developer perspective (the repo):** A Maker-Checker LLM pipeline that reads `semantic_rules.json`, generates BDD test cases, reviews coverage, and supports human review/rewrite cycles. Built on Python standard library only, OpenAI-compatible API adapters, strict JSON schema validation.

2. **Tester perspective (`chat-prompt.md`):** A 15-prompt lifecycle that starts from raw business documents (PDF/Word), structures them into a knowledge base with paragraph IDs, generates Copilot skills, produces BDD `.feature` files, and integrates with a governance/audit layer — designed for four user types: BA, QA Lead, Automation Engineer, and Mixed.

**The goal of this roadmap** is to merge these two systems into a single, LLM-agnostic, enterprise-ready AI testing platform.

---

## Guiding Principles for LLM API Calls

All phases must follow these rules regardless of which LLM is used (Qwen, MiniMax, GLM, Claude, GPT-4, etc.):

1. **Prompt versioning:** Every system prompt and user prompt template must be stored in `config/prompts/` with a version slug (e.g. `maker_v2.md`). The run summary must record which version was used.
2. **Schema-first:** LLM outputs are never trusted directly. All responses go through schema validation before being persisted. `schemas.py` is the single source of truth.
3. **Provider abstraction:** New LLMs are added by extending `ProviderConfig` and `build_provider()` only. No pipeline code should reference a specific model name.
4. **Structured IDs as the spine:** Every artefact — atomic rule, semantic rule, test case, BDD feature, skill — must carry a structured ID. Cross-references use IDs, never file paths alone.
5. **Human-in-the-loop is non-negotiable:** Every phase must have a human review gate before artefacts are promoted to the next phase. Automation accelerates; it does not bypass review.
6. **Convergence over iteration count:** Loop termination is triggered by coverage plateau (block delta < 5% over two consecutive checker runs), not by a fixed number of rounds.

---

## Phase Overview

| Phase | Scope | Timeline | Target Coverage |
|-------|-------|----------|-----------------|
| **Short-term** | Stabilise and extend existing pipeline | Months 1–3 | ≥ 80% rule coverage on POC |
| **Medium-term** | Document ingestion → rule extraction → BDD, end-to-end | Months 4–9 | ≥ 90% on full rule set, step definitions linked |
| **Long-term** | Enterprise governance, multi-document, CI/CD, multi-team | Months 10–18 | 95%+ coverage, audit-ready, self-healing |

---

## Phase 1: Short-Term — Foundation Hardening (Months 1–3)

### Objective

Make the existing Maker-Checker pipeline reliable, reproducible, and ready to be called by any LLM without manual intervention.

### Milestone 1.1 — Convergence Loop with Auto-Termination

**What to build:**

Add a `ConvergenceController` in `workflow_session.py` that tracks block delta between checker runs and stops automatically.

```python
# lme_testing/convergence.py
class ConvergenceController:
    def __init__(self, max_rounds: int = 5, delta_threshold: float = 0.05):
        self.history: list[dict] = []

    def should_continue(self, current_summary: dict) -> bool:
        self.history.append(current_summary)
        if len(self.history) < 2:
            return True
        prev_blocks = self.history[-2].get("checker_block_count", 0)
        curr_blocks = current_summary.get("checker_block_count", 0)
        if prev_blocks == 0:
            return False
        delta = (prev_blocks - curr_blocks) / prev_blocks
        return delta >= self.delta_threshold and len(self.history) < self.max_rounds
```

**Acceptance criteria:**
- [ ] Workflow stops automatically when block count reduction falls below 5% between rounds.
- [ ] Maximum rounds cap (default 5) is configurable in `config/llm_profiles.example.json`.
- [ ] `summary.json` records `termination_reason: "convergence" | "max_rounds" | "manual"`.
- [ ] Unit tests cover all three termination paths.

---

### Milestone 1.2 — Concurrent Batch Execution

**What to build:**

Replace sequential `for batch in _chunked(...)` loops in `pipelines.py` with `ThreadPoolExecutor`-based concurrent calls.

**Acceptance criteria:**
- [ ] `max_workers` is a configurable parameter exposed in CLI and `ProjectConfig`.
- [ ] Results are written to JSONL in order (sort by `semantic_rule_id` after collection).
- [ ] `resume_from` still works correctly under concurrent execution.
- [ ] Wall-clock time for 50-rule runs is reduced by at least 50% vs sequential.

---

### Milestone 1.3 — Prompt Version Management

**What to build:**

Move `MAKER_SYSTEM_PROMPT`, `CHECKER_SYSTEM_PROMPT`, `REWRITE_SYSTEM_PROMPT` from `prompts.py` into external files:

```
config/
  prompts/
    maker_system_v1.md
    checker_system_v1.md
    rewrite_system_v1.md
```

`prompts.py` becomes a loader that reads from disk and records the version slug.

**Acceptance criteria:**
- [ ] `summary.json` includes `prompt_versions: {maker: "v1", checker: "v1"}`.
- [ ] Switching prompt version requires only changing a config field, not code.
- [ ] Old prompt versions are never deleted — only new versions are added.
- [ ] README documents how to create and register a new prompt version.

---

### Milestone 1.4 — Few-Shot Skill Exemplar Registry

**What to build:**

After each human review session, approved cases (Decision=approve, is_blocking=False) are appended to `skills/approved_exemplars.jsonl`. The Maker prompt loader reads the N most recent exemplars and prepends them as few-shot examples.

**Acceptance criteria:**
- [ ] Exemplar file is append-only; no deletions.
- [ ] Maker prompt includes at most 5 exemplars (configurable).
- [ ] Exemplars are filtered by `rule_type` to match the current batch.
- [ ] `summary.json` records how many exemplars were used per run.
- [ ] Test shows that a second run after approvals produces fewer checker blocks.

---

### Milestone 1.5 — Coverage Trend Report

**What to build:**

A `report_trend()` function in `reporting.py` that reads all `coverage_report.json` files across runs and generates a trend table in the HTML report.

**Acceptance criteria:**
- [ ] Final `report.html` includes a "Coverage Trend" section showing per-run: `run_id`, `coverage_percent`, `checker_block_count`, `termination_reason`.
- [ ] Works correctly with as few as 1 run and as many as 20.

---

### Phase 1 Acceptance Gate

All five milestones must pass before Phase 2 begins:

| Check | Target |
|-------|--------|
| POC two-rule run completes end-to-end without manual intervention | Pass |
| Coverage on `poc_two_rules` reaches ≥ 80% `fully_covered` | Pass |
| All existing unit tests still pass | Pass |
| `prompt_versions` recorded in every run summary | Pass |
| Wall-clock time for 10-rule concurrent run vs sequential | ≥ 40% faster |

---

## Phase 2: Medium-Term — Document Ingestion to BDD (Months 4–9)

### Objective

Close the gap identified in `chat-prompt.md`: the pipeline currently starts from `semantic_rules.json`, which is hand-crafted. Phase 2 automates the journey from raw business documents (PDF, Word, Markdown) all the way to executable `.feature` files with linked step definitions.

This phase introduces **four new pipeline stages** before the existing Maker-Checker flow.

---

### Milestone 2.1 — Document Ingestion and Paragraph Extraction

**New module:** `lme_testing/ingestion.py`

Accepts PDF, DOCX, or Markdown. Outputs structured Markdown files with paragraph IDs following the convention from `chat-prompt.md`:

```
{domain}-{subdomain}-{sequence}
Examples: DC-IMRPF-001, MRCC-HVaR-001
```

LLM call role: **Segmenter** — splits long documents into logical paragraphs and assigns IDs.

**Acceptance criteria:**
- [ ] Input: any PDF/DOCX/MD file under 200 pages.
- [ ] Output: one or more `docs/source-files/{module}.md` files with paragraph IDs.
- [ ] `docs/source-files/INDEX.md` is generated listing all modules and ID ranges.
- [ ] Duplicate IDs across modules are detected and flagged as errors.
- [ ] `PROMPT1-OUTPUT.md` (from `chat-prompt.md` design) is generated with execution metrics.
- [ ] LLM prompt stored at `config/prompts/segmenter_v1.md`.

---

### Milestone 2.2 — Atomic Rule Extraction

**New stage:** Extends `scripts/extract_matching_rules.py` to accept the structured Markdown from Milestone 2.1.

LLM call role: **Extractor** — reads each paragraph and decides if it contains an atomic rule; if so, generates an `atomic_rule` record.

**Acceptance criteria:**
- [ ] Output is `artifacts/{run_id}/atomic_rules.json` matching the existing schema.
- [ ] Each atomic rule carries `paragraph_id` pointing back to the source Markdown.
- [ ] Extractor abstains on reference-only paragraphs (marks `rule_type: "reference_only"`).
- [ ] Human review gate: a simple CLI command (`lme review-atomic`) lets a human approve, reject, or edit each atomic rule before proceeding.
- [ ] Confidence score for each extraction is stored; rules below 0.6 are flagged for mandatory human review.

---

### Milestone 2.3 — Semantic Rule Synthesis

**New stage:** Extends `scripts/generate_semantic_rules.py`.

LLM call role: **Synthesiser** — groups related atomic rules into semantic rules, assigns `rule_type` and `required_case_types`.

**Acceptance criteria:**
- [ ] Output is `artifacts/{run_id}/semantic_rules.json` compatible with the existing Maker pipeline.
- [ ] Each semantic rule lists `source.atomic_rule_ids` and `source.paragraph_ids`.
- [ ] `rule_type` assignment is validated against the allowed set in `RULE_TYPE_CASE_REQUIREMENTS`.
- [ ] Human review gate before semantic rules are handed to Maker.

---

### Milestone 2.4 — BDD Feature File Generation

**Enhancement to existing pipeline:**

After the Maker produces scenarios and Checker approves them, a new `run_bdd_export_pipeline()` function converts approved scenarios to Gherkin `.feature` files.

```
tests/bdd/features/{module}_{rule_type}.feature
```

**Acceptance criteria:**
- [ ] Every approved scenario becomes exactly one Gherkin `Scenario` or `Scenario Outline`.
- [ ] `Feature:` header includes `semantic_rule_id` and `rule_type`.
- [ ] `@tags` include `case_type`, `priority`, and `semantic_rule_id`.
- [ ] Each scenario includes a `# rule_source: {paragraph_id}` comment for traceability.
- [ ] Output is valid Gherkin parseable by `behave` without modification.
- [ ] `behave.ini` is auto-generated pointing to the features directory.

---

### Milestone 2.5 — Step Definition Scaffolding

**New module:** `lme_testing/step_scaffolding.py`

LLM call role: **Scaffolder** — reads `.feature` files and generates Python step definition stubs in `tests/bdd/steps/`.

**Acceptance criteria:**
- [ ] Every `Given/When/Then` step in every `.feature` file has a corresponding stub in `steps/`.
- [ ] Stubs include `# TODO: implement` markers and parameter type hints.
- [ ] Re-running on an updated `.feature` file adds new stubs without overwriting existing implementations.
- [ ] A `tests/bdd/steps/step_registry.json` maps each step text to its implementing function (populated by humans as they implement steps).
- [ ] Coverage report shows which steps are implemented vs stubbed.

---

### Milestone 2.6 — User-Type Aware Output

Implement the four user types from `chat-prompt.md` as output profiles:

| Type | Description | Output Format |
|------|-------------|---------------|
| A — BA | Business-facing, no technical jargon | Simplified Markdown, plain-language scenarios |
| B — QA Lead | Coverage-focused, compliance-centric | Coverage report, rule traceability matrix |
| C — Automation Engineer | CI/CD-ready, runnable | `.feature` files, step stubs, `behave.ini` |
| D — Mixed | All of the above | Combined HTML report with tabs |

**Acceptance criteria:**
- [ ] `--output-profile [ba|qa-lead|automation|mixed]` CLI flag.
- [ ] Each profile generates its own report subset.
- [ ] Default profile is `mixed`.

---

### Phase 2 Acceptance Gate

| Check | Target |
|-------|--------|
| Full pipeline runs: raw PDF → `semantic_rules.json` → BDD `.feature` files | Pass |
| Coverage on `lme_rules_v2_2` full set reaches ≥ 90% `fully_covered` | Pass |
| Generated `.feature` files parse cleanly with `behave --dry-run` | Zero parse errors |
| Step definition stubs are generated for 100% of steps | Pass |
| Human review gates present at ingestion, atomic extraction, and semantic synthesis | Pass |
| All four user-type output profiles produce non-empty output | Pass |

---

## Phase 3: Long-Term — Enterprise Governance and CI/CD Integration (Months 10–18)

### Objective

Make the platform audit-ready, self-healing, and suitable for multi-team use in a regulated environment (financial services, exchange operations).

---

### Milestone 3.1 — Multi-Document Knowledge Base

Extend the ingestion pipeline to handle a corpus of documents, not just one at a time.

**Acceptance criteria:**
- [ ] `docs/source-files/INDEX.md` tracks all documents, their versions, and ingestion dates.
- [ ] Cross-document references (e.g. Rule A in document 1 depends on definition in document 2) are detected and modelled.
- [ ] When a document is updated, only affected atomic/semantic rules are re-extracted (incremental update, as designed in `chat-prompt.md` Prompts 8–9).
- [ ] Change impact report is generated: which test cases and `.feature` files are affected by the document change.

---

### Milestone 3.2 — Multi-Provider Checker Ensemble

Use two different LLMs as Checker in parallel and take the union of blocking findings.

**Acceptance criteria:**
- [ ] `config/llm_profiles.json` supports `checker_ensemble: [provider_a, provider_b]`.
- [ ] A finding is only marked `is_blocking=True` if at least one of the ensemble members blocks.
- [ ] A finding is marked `high_confidence_block` if both members agree.
- [ ] `coverage_report.json` records ensemble agreement rate as a quality metric.

---

### Milestone 3.3 — Full Governance Layer

Implement the governance structure from `chat-prompt.md` Sections III and IV:

```
governance/
  reviews/           # Per-prompt review artefacts
  checker/           # LLM checker analysis outputs
  change-tracking/   # Document, skill, test case, BDD change history
  performance-metrics/
  error-tracking/
  audit-trail.md
```

**Acceptance criteria:**
- [ ] Every run produces a timestamped entry in `governance/audit-trail.md`.
- [ ] Change history for every artefact (rule, test case, `.feature`) is maintained with git commit references.
- [ ] `governance/performance-metrics/dashboard.md` is auto-generated after each run with execution times, block counts, coverage percent, and error rates.
- [ ] Alert conditions defined (error rate > 5%, coverage regression > 2%) trigger entries in `governance/alerts/alert-log.md`.

---

### Milestone 3.4 — CI/CD Pipeline Integration

**Acceptance criteria:**
- [ ] A GitHub Actions (or GitLab CI) workflow file is provided in `.github/workflows/lme-testing.yml`.
- [ ] The workflow runs the full pipeline on push to `main` for any change under `artifacts/` or `docs/`.
- [ ] `behave --dry-run` runs on all generated `.feature` files as a CI gate.
- [ ] Coverage regression (current run coverage < previous run coverage - 2%) fails the pipeline.
- [ ] The HTML report is published as a CI artefact.
- [ ] Step definition implementation coverage is reported as a CI metric.

---

### Milestone 3.5 — Anthropic / Claude Provider Support

Add a native Anthropic provider adapter (the API response format differs from OpenAI-compatible):

```python
class AnthropicProvider:
    # Uses /v1/messages, handles content blocks, supports extended thinking
```

**Acceptance criteria:**
- [ ] `provider_type: "anthropic"` works in `llm_profiles.json`.
- [ ] Supports `claude-sonnet-4-6` as Checker (higher quality blocking judgement).
- [ ] Supports Chinese LLMs (Qwen, MiniMax) as Maker (cost efficiency).
- [ ] Mixed-provider ensemble (e.g. Qwen Maker + Claude Checker) works end-to-end.

---

### Milestone 3.6 — Step Definition Integration Check

Once automation engineers implement step definitions (Milestone 2.5 stubs), run an integration check:

**Acceptance criteria:**
- [ ] `behave` (not just `--dry-run`) runs on a test environment and produces a pass/fail report.
- [ ] The coverage report distinguishes between:
  - `scenario_generated` — scenario exists as `.feature`
  - `step_stubbed` — step exists but not implemented
  - `step_implemented` — step is implemented and ran
  - `scenario_passed` — scenario ran and passed
  - `scenario_failed` — scenario ran and failed
- [ ] Failed scenarios are fed back into the Maker-Checker rewrite cycle automatically.

---

### Milestone 3.7 — Skill Export for GitHub Copilot

Implement the Copilot skill generation described in `chat-prompt.md` Prompts 3–5:

**Acceptance criteria:**
- [ ] Approved semantic rules and their test scenarios can be exported as GitHub Copilot skill files to `copilot-skills/skill-definitions/`.
- [ ] Each skill file contains the structured reference fields (`rule_source`, `test_reference`, `validation_reference`, `update_history`) defined in `chat-prompt.md`.
- [ ] Skills reference paragraph IDs from the knowledge base.
- [ ] BDD association slots are pre-populated once `.feature` files exist.

---

### Phase 3 Acceptance Gate

| Check | Target |
|-------|--------|
| Full pipeline runs on a corpus of 3+ LME documents without manual file editing | Pass |
| CI/CD pipeline runs green on a sample repo | Pass |
| `behave` (not dry-run) executes at least 20% of generated scenarios against a stub environment | Pass |
| Audit trail is complete for a 3-round Maker-Checker-Rewrite cycle | Pass |
| Coverage regression detection works: intentionally removing a rule causes CI to fail | Pass |
| Copilot skill files generated for at least one document module | Pass |

---

## Cross-Phase Technical Constraints

### LLM API Calling Conventions

All phases must follow these conventions when calling LLM APIs:

```json
{
  "model": "<configured in llm_profiles.json>",
  "temperature": 0.1,
  "max_tokens": 8000,
  "response_format": {"type": "json_object"},
  "messages": [
    {"role": "system", "content": "<loaded from config/prompts/{role}_{version}.md>"},
    {"role": "user",   "content": "<built by build_{role}_user_prompt()>"}
  ]
}
```

Never hardcode model names in pipeline code. Always read from `ProjectConfig`.

### Schema Validation is Mandatory at Every Stage

Every new LLM call introduced in Phases 2 and 3 must have a corresponding `validate_{stage}_payload()` function in `schemas.py` before the call goes into production.

### Retry and Backoff

All providers must use the existing retry pattern in `OpenAICompatibleProvider.generate()`. New providers inherit the same `max_retries` and `retry_backoff_seconds` settings.

### Output Determinism

For reproducibility, each run produces a `run_id` timestamp slug. Given the same inputs and the same prompt version, runs should produce structurally equivalent outputs (modulo LLM non-determinism). Temperature = 0.0 for Checker, 0.1 for Maker.

---

## File and Directory Conventions

Following the tester's design from `chat-prompt.md` and integrating with the existing repo structure:

```
LME-Testing/
├── artifacts/
│   └── {corpus_name}/
│       ├── atomic_rules.json
│       ├── semantic_rules.json
│       └── pages/
├── config/
│   ├── llm_profiles.json          # LLM provider and role bindings
│   ├── human_review_options.json  # Issue type config
│   └── prompts/                   # ← NEW: versioned prompt files
│       ├── maker_system_v1.md
│       ├── checker_system_v1.md
│       ├── rewrite_system_v1.md
│       ├── segmenter_v1.md        # Phase 2
│       ├── extractor_v1.md        # Phase 2
│       └── synthesiser_v1.md      # Phase 2
├── docs/
│   └── source-files/              # ← NEW Phase 2: structured knowledge base
│       ├── INDEX.md
│       └── {module}.md
├── lme_testing/
│   ├── cli.py
│   ├── config.py
│   ├── convergence.py             # ← NEW Phase 1
│   ├── ingestion.py               # ← NEW Phase 2
│   ├── step_scaffolding.py        # ← NEW Phase 2
│   ├── pipelines.py
│   ├── providers.py
│   ├── reporting.py
│   ├── review_session.py
│   ├── schemas.py
│   └── workflow_session.py
├── tests/
│   └── bdd/
│       ├── features/              # ← NEW Phase 2: Gherkin files
│       ├── steps/                 # ← NEW Phase 2: step definitions
│       └── step_registry.json     # ← NEW Phase 2
├── copilot-skills/                # ← NEW Phase 3
│   └── skill-definitions/
├── governance/                    # ← NEW Phase 3
│   ├── audit-trail.md
│   ├── change-tracking/
│   └── performance-metrics/
├── runs/                          # Runtime outputs (gitignored)
├── skills/                        # Few-shot exemplar registry
│   └── approved_exemplars.jsonl   # ← NEW Phase 1
└── .github/
    └── workflows/
        └── lme-testing.yml        # ← NEW Phase 3
```

---

## Prompt Dependency Chain

The full execution order across all phases:

```
Raw Document (PDF/DOCX/MD)
  ↓ [Segmenter LLM — Phase 2]
docs/source-files/{module}.md  (paragraph IDs)
  ↓ [Extractor LLM — Phase 2] + [Human Review Gate]
atomic_rules.json
  ↓ [Synthesiser LLM — Phase 2] + [Human Review Gate]
semantic_rules.json
  ↓ [Maker LLM — Phase 1 hardened]
maker_cases.jsonl
  ↓ [Checker LLM — Phase 1 hardened, Phase 3 ensemble]
checker_reviews.jsonl
  ↓ [Human Review — review-session]
human_reviews.json
  ↓ [Rewrite LLM if needed — convergence loop]
  ↓ [BDD Exporter — Phase 2]
tests/bdd/features/*.feature
  ↓ [Step Scaffolder LLM — Phase 2]
tests/bdd/steps/*.py  (stubs → human implements)
  ↓ [behave — Phase 3]
test execution results
  ↓ [Failed scenarios feed back into rewrite cycle — Phase 3]
  ↓ [Copilot Skill Exporter — Phase 3]
copilot-skills/skill-definitions/*.md
  ↓
report.html + governance/audit-trail.md
```

---

## Version Control and Branching Strategy

```
main               — stable, all acceptance gates passed
develop            — integration branch
feature/phase-1-*  — Phase 1 milestones
feature/phase-2-*  — Phase 2 milestones
feature/phase-3-*  — Phase 3 milestones
```

**Tagging convention:**
- `v1.0.0` — Phase 1 acceptance gate passed
- `v2.0.0` — Phase 2 acceptance gate passed
- `v3.0.0` — Phase 3 acceptance gate passed

Every `PROMPT{N}-OUTPUT.md` or equivalent run summary must be committed to git so the audit trail is version-controlled.

---

## Recommended Starting Point

1. Start with `artifacts/poc_two_rules/` for all Phase 1 milestones — it runs in seconds.
2. Move to `artifacts/lme_rules_v2_2/` once all Phase 1 acceptance criteria are met.
3. Use a single LME document (e.g. the August 2022 Matching Rules PDF already in `docs/materials/`) as the Phase 2 ingestion target.
4. Do not attempt Phase 3 milestones until Phase 2 BDD feature files are passing `behave --dry-run` cleanly.

---

*This roadmap should be reviewed and updated at the end of each phase. Changes require a pull request, updated version number, and a `CHANGELOG.md` entry.*
