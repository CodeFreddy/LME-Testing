# LME Testing

`LME-Testing` is a document-driven test design prototype for LME matching rules.

The project turns official LME documents into structured rules, uses a `maker` model to generate BDD-style test cases, uses a `checker` model to review them, then supports human review, rewrite, re-check, and final HTML reporting.

## What This Project Does

The current workflow is:

1. Extract rules from LME source documents.
2. Normalize them into `atomic_rule` and `semantic_rule` artifacts.
3. Use `maker` to generate structured test scenarios.
4. Use `checker` to assess case quality and rule coverage.
5. Let a human reviewer decide whether cases should be approved, rewritten, or rejected.
6. Rewrite selected rules through `maker` again.
7. Re-run `checker` and regenerate reports.

Coverage is strict. A rule is not considered fully covered just because one case matches it. The system maps each `rule_type` to `required_case_types`, and a rule becomes `fully_covered` only when all required case types are accepted by `checker`.

## Main Entrypoints

- `main.py`
  - CLI entrypoint.
- `lme_testing/cli.py`
  - Registers all commands.
- `lme_testing/pipelines.py`
  - Core maker / checker / rewrite pipelines.
- `lme_testing/review_session.py`
  - Local HTTP review session service.
- `lme_testing/workflow_session.py`
  - End-to-end orchestrator that can bootstrap maker/checker and auto-start review-session.
- `lme_testing/reporting.py`
  - HTML report generation.
- `lme_testing/human_review.py`
  - Static human review page generator.
- `lme_testing/providers.py`
  - OpenAI-compatible provider adapter with retry support.
- `lme_testing/logging_utils.py`
  - Shared terminal + file logging setup.

## Important Commands

### maker

Generate structured test scenarios from `semantic_rules.json`.

### checker

Review maker output and compute rule-level coverage.

### rewrite

Regenerate only the rules that human review marked as `rewrite`.

### review-session

Start a local review web page. The page can:

- save review drafts
- submit review decisions
- run `rewrite -> checker -> report`
- finalize the session
- jump to the final `report.html`

After finalize, the final report page includes top navigation links for:

- `Summary Report`
- `Maker Readable`
- `Checker Readable`

### workflow-session

Run the end-to-end flow from a chosen step and auto-start `review-session` after the first checker pass.

## Typical Flow

```text
source docs
  -> extract scripts
  -> atomic_rules.json
  -> semantic_rules.json
  -> maker
  -> checker
  -> review-session
  -> rewrite
  -> checker
  -> report
```

## Human Review Model

Human review currently uses these fields:

- `Decision`
  - `pending | approve | rewrite | reject`
  - This is the final execution action.
- `Block Recommendation Review`
  - `not_applicable | pending_review | confirmed | dismissed`
  - This is audit-only and does not override `Decision`.
- `Issue Types`
  - Config-driven multi-select options loaded from `config/human_review_options.json`.
  - The page uses a collapsible checkbox table instead of free text.
- `Comment`
  - Free-text reviewer notes.

Only `Decision = rewrite` triggers rewrite.

## Logging And Reliability

All CLI commands initialize logging and print a `log_path` at startup.

Logs are written to:

- the current terminal
- a file under the command output directory, usually `logs/`

Model calls now include retry support for recoverable failures such as:

- `RemoteDisconnected`
- timeouts
- common `429 / 5xx` responses

## Recommended Starting Point

Use the POC sample first:

- `artifacts/poc_two_rules/semantic_rules.json`

This keeps maker/checker/review-session validation fast and avoids long full-rule runs during development.

## Documents

- [docs/maker_checker_usage.md](docs/maker_checker_usage.md)
- [docs/rule_model_and_parsing_design.md](docs/rule_model_and_parsing_design.md)
- [docs/rule_extraction_script_guide.md](docs/rule_extraction_script_guide.md)
