# Maker / Checker Usage

This document describes the current commands, parameters, outputs, and review semantics for the project.

## 1. Key Files

- Entry CLI: `main.py`
- CLI registration: `lme_testing/cli.py`
- Config loading: `lme_testing/config.py`
- Provider adapter: `lme_testing/providers.py`
- Logging setup: `lme_testing/logging_utils.py`
- Maker / checker / rewrite pipelines: `lme_testing/pipelines.py`
- Prompt templates: `lme_testing/prompts.py`
- Schema validation: `lme_testing/schemas.py`
- Static human review page: `lme_testing/human_review.py`
- Review session service: `lme_testing/review_session.py`
- Workflow orchestrator: `lme_testing/workflow_session.py`
- HTML reporting: `lme_testing/reporting.py`
- Storage helpers: `lme_testing/storage.py`
- POC rules: `artifacts/poc_two_rules/semantic_rules.json`
- Full rules: `artifacts/lme_rules_v2_2/semantic_rules.json`
- Human review option config: `config/human_review_options.json`
- LLM config example: `config/llm_profiles.example.json`

## 2. Configuration

Default example config:

```text
config/llm_profiles.example.json
```

Human review issue type options are configured in:

```text
config/human_review_options.json
```

Each issue type must provide:

- `code`
- `label`
- `description`

The UI does not allow arbitrary free-text issue type input. It uses a collapsible multi-select checkbox table driven by this config.

## 3. Logging

All CLI commands initialize logging and print a `log_path` at startup.

Logs are written to:

- the current terminal
- a log file under the output directory, usually `logs/`

This applies to:

- `maker`
- `checker`
- `rewrite`
- `report`
- `human-review`
- `review-session`
- `workflow-session`

## 4. maker

### Example

```powershell
python main.py --config config/llm_profiles.example.json maker `
  --input artifacts/poc_two_rules/semantic_rules.json `
  --output-dir runs/poc_strict/maker_complete `
  --batch-size 1
```

### Parameters

- `--input`
- `--output-dir`
- `--limit`
- `--batch-size`
- `--resume-from`

### Output

- `maker_cases.jsonl`
- `maker_raw_responses.jsonl`
- `summary.json`

### Current maker constraints

- maker must return exactly one `result` per input `semantic_rule_id`
- maker must not return extra or missing rules
- each rule must generate exactly one scenario for each required case type
- evidence quotes must stay short and single-line

## 5. checker

### Example

```powershell
python main.py --config config/llm_profiles.example.json checker `
  --rules artifacts/poc_two_rules/semantic_rules.json `
  --cases runs/poc_strict/maker_complete/<run_id>/maker_cases.jsonl `
  --output-dir runs/poc_strict/checker_complete `
  --batch-size 2
```

### Parameters

- `--rules`
- `--cases`
- `--output-dir`
- `--limit`
- `--batch-size`
- `--resume-from`

### Output

- `checker_reviews.jsonl`
- `checker_raw_responses.jsonl`
- `coverage_report.json`
- `summary.json`

### Current checker constraints

- checker must return exactly one review per input `case_id`
- checker must not return extra or missing case ids
- `semantic_rule_id` must match the input case mapping
- checker returns structured blocking and coverage fields

## 6. human-review

`human-review` generates a static HTML page.

### Example

```powershell
python main.py human-review `
  --maker-cases runs/poc_strict/maker_complete/<run_id>/maker_cases.jsonl `
  --checker-reviews runs/poc_strict/checker_complete/<run_id>/checker_reviews.jsonl `
  --output-html reports/tmp_human_review/human_review.html
```

### Human review fields

- `Decision`
  - `pending | approve | rewrite | reject`
  - final execution action
- `Block Recommendation Review`
  - `not_applicable | pending_review | confirmed | dismissed`
  - audit-only, does not override `Decision`
- `Issue Types`
  - config-driven multi-select checkbox table
- `Comment`
  - free text

### Execution rule

Only `Decision = rewrite` triggers rewrite.

## 7. rewrite

`rewrite` regenerates rules selected by human review.

### Example

```powershell
python main.py --config config/llm_profiles.example.json rewrite `
  --rules artifacts/poc_two_rules/semantic_rules.json `
  --cases runs/poc_strict/maker_complete/<run_id>/maker_cases.jsonl `
  --checker-reviews runs/poc_strict/checker_complete/<run_id>/checker_reviews.jsonl `
  --human-reviews artifacts/poc_two_rules/human_reviews.json `
  --output-dir runs/poc_rewrite `
  --batch-size 1
```

### Parameters

- `--rules`
- `--cases`
- `--checker-reviews`
- `--human-reviews`
- `--output-dir`
- `--limit`
- `--batch-size`

### Output

- `rewritten_cases.jsonl`
- `merged_cases.jsonl`
- `rewrite_raw_responses.jsonl`
- `summary.json`

## 8. report

`report` renders HTML outputs.

### Example

```powershell
python main.py report `
  --maker-cases runs/.../maker_cases.jsonl `
  --checker-reviews runs/.../checker_reviews.jsonl `
  --maker-summary runs/.../summary.json `
  --checker-summary runs/.../summary.json `
  --coverage-report runs/.../coverage_report.json `
  --output-html runs/.../report/report.html
```

### Output

- `report.html`
- `maker_readable.html`
- `checker_readable.html`

All three report pages now include top navigation links so users can switch between them directly.

## 9. review-session

`review-session` is the main human review entrypoint.

### Example

```powershell
python main.py --config config/llm_profiles.example.json review-session `
  --rules artifacts/poc_two_rules/semantic_rules.json `
  --cases runs/poc_strict/maker_complete/<run_id>/maker_cases.jsonl `
  --checker-reviews runs/poc_strict/checker_complete/<run_id>/checker_reviews.jsonl `
  --maker-summary runs/poc_strict/maker_complete/<run_id>/summary.json `
  --checker-summary runs/poc_strict/checker_complete/<run_id>/summary.json `
  --coverage-report runs/poc_strict/checker_complete/<run_id>/coverage_report.json `
  --output-dir runs/review_sessions_verify `
  --rewrite-batch-size 1 `
  --checker-batch-size 2 `
  --host 127.0.0.1 `
  --port 8780
```

### Parameters

- `--rules`
- `--cases`
- `--checker-reviews`
- `--maker-summary`
- `--checker-summary`
- `--coverage-report`
- `--output-dir`
- `--rewrite-batch-size`
- `--checker-batch-size`
- `--host`
- `--port`

### Session behavior

- saves human review snapshots and `latest`
- runs `rewrite -> checker -> report` on submit
- advances to the next iteration automatically
- supports repeated review / rewrite cycles
- supports `Finalize`

### Finalize behavior

When `Finalize` is clicked:

- the session is marked finalized
- the browser redirects to the final `report.html`
- from there, users can switch to:
  - `maker_readable.html`
  - `checker_readable.html`

### Session outputs

Each session writes artifacts under:

```text
runs/review_sessions/<session_id>/
```

Typical structure:

```text
iterations/<n>/reviews/
iterations/<n>/rewrite/
iterations/<n>/checker/
iterations/<n>/report/
final/
session_manifest.json
```

## 10. workflow-session

`workflow-session` is the end-to-end orchestrator.

It can start from a chosen step, bootstrap maker/checker, then auto-start `review-session`.

### Example

```powershell
python main.py --config config/llm_profiles.example.json workflow-session `
  --source docs/materials/LME_Matching_Rules_Aug_2022.md `
  --artifacts-dir artifacts/poc_two_rules `
  --start-step maker `
  --output-dir runs/review_sessions_verify_full `
  --maker-batch-size 1 `
  --checker-batch-size 2 `
  --host 127.0.0.1 `
  --port 8783
```

### Parameters

- `--source`
- `--artifacts-dir`
- `--maker-cases`
- `--maker-summary`
- `--checker-reviews`
- `--checker-summary`
- `--coverage-report`
- `--start-step`
- `--output-dir`
- `--maker-batch-size`
- `--checker-batch-size`
- `--host`
- `--port`
- `--write-page-text`

### Recommended usage

For fast end-to-end validation, start from the POC artifacts and use:

- `--start-step maker`

This avoids redoing extraction and keeps turnaround short.

## 11. Strict Coverage Rules

Coverage is computed per `semantic_rule`.

A case type is accepted only when:

- `case_type_accepted = true`
- `coverage_relevance = direct`
- `is_blocking = false`

A rule becomes `fully_covered` only when all required case types have at least one accepted case.

## 12. Provider Retry Behavior

Provider calls now support retry for recoverable failures.

Default values:

- `max_retries = 3`
- `retry_backoff_seconds = 2.0`

Retry targets include:

- `RemoteDisconnected`
- timeouts
- common `429 / 5xx` responses

## 13. Current Cleanup Policy

To reduce noise, old historical runtime outputs were cleaned up.

Current useful runtime directories are expected to be:

- the latest `runs/poc_strict/...` baseline
- the latest active `runs/review_sessions_...` session

Avoid committing large historical runtime trees unless they are intentionally preserved as reference artifacts.

## 14. Maintenance Rules

If you change any of the following, update this document at the same time:

- CLI command parameters
- output file layout
- human review fields or option enums
- report navigation behavior
- retry / logging behavior
- rule coverage semantics
