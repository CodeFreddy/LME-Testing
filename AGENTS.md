# Agent Entry Rules

Read this file first before making non-trivial changes in this repo.

This repository is governed by contracts, phase boundaries, and acceptance gates.
Agents may implement the roadmap, but must not silently redefine it through code or document changes.

## Read Order

For substantial work, read these files in order:

1. `docs/planning/roadmap.md`
2. `docs/planning/implementation_plan.md`
3. `docs/governance/acceptance.md`
4. `docs/architecture/architecture.md`
5. `docs/governance/model_governance.md`
6. `docs/governance/agent_guidelines.md`

## Non-Negotiable Rules

- Work against explicit contracts, not inferred intent.
- Do not bypass schemas or weaken artifact contracts silently.
- Do not switch default models or prompts without benchmark evidence and rollback notes.
- Do not expand scope across phases unless a human explicitly approves it.
- Do not introduce a new LLM-driven stage unless it has a defined contract, validation, traceability, and reviewable outputs.
- Do not treat rendered syntax output as canonical where a normalized governed artifact should own the contract.
- Prefer deterministic validation whenever it is available.
- Keep failures visible; do not hide broken contracts to keep flows passing.

## Baseline Checks

Before or immediately after substantial repo changes, run:

```text
python scripts/check_docs_governance.py
python scripts/check_artifact_governance.py
```

These checks are the minimum governance baseline:

- `check_docs_governance.py` enforces relative local links in `*.md`
- `check_artifact_governance.py` enforces minimum baseline artifact structure and controlled `rule_type` values

## Commit Handoff Rule

Every commit should refresh `docs/operations/session_handoff.md`.

Preferred path:

- enable repo hooks once with `powershell -ExecutionPolicy Bypass -File scripts/setup_git_hooks.ps1`
- let the post-commit hook regenerate the handoff automatically

If hooks are unavailable, update the handoff manually before committing:

```text
powershell -ExecutionPolicy Bypass -File scripts/update_session_handoff.ps1
```

## Checkpoint Preservation Rule

Whenever an agent generates a checkpoint and resume prompt, it must append or refresh the record in `docs/operations/checkpoints.md`.

The record must include:

- current task goal,
- confirmed key facts,
- files modified or inspected,
- remaining work,
- next single action,
- constraints that must not be violated,
- a directly reusable resume prompt.

Keep the latest checkpoint easy to find at the top of `docs/operations/checkpoints.md`, and preserve older checkpoints below it unless a human explicitly asks to prune them.

## Current Phase Bias

The current roadmap is biased toward:

1. upstream rule governance,
2. reproducible CI baseline,
3. source-anchor traceability,
4. model and prompt provenance,
5. checker stability visibility on a small baseline set.

Do not prioritize heavier future-platform work over these controls unless explicitly directed.

## Current Active Work

As of 2026-04-26, the active handoff is the HKv14 POC document workflow and modular mock API bridge.

Current facts to preserve:

- HKv14 governed intake was generated under `artifacts/im_hk_v14/` from `docs/materials/Initial Margin Calculation Guide HKv14.pdf`.
- The PDF extractor now uses `pypdf` as the primary extractor for PDF inputs and writes the full extracted Markdown source into the artifact output folder.
- The HKv13-to-HKv14 deterministic diff was generated under `evidence/im_hk_v14_diff/` and summarized in `docs/planning/im_hk_v14_diff_report.md`.
- The POC downstream decision note is `docs/planning/im_hk_v14_downstream_decision.md`; for POC, all deterministic diff candidates were accepted.
- The HKv14 mock API POC bridge uses a shared package in `deliverables/im_hk_mock_api_common/` plus a thin HKv14 wrapper in `deliverables/im_hk_v14_mock_api/`.
- The HKv13 mock API deliverable remains the preservation baseline and must not be overwritten by HKv14 work.
- A future role-friendly decision UI requirement is recorded as planning scope only; do not implement it unless a human explicitly asks.

Next recommended action for a fresh chat:

- Read the latest checkpoint in `docs/operations/checkpoints.md`, run `git status --short`, then either prepare the current package for review/commit or proceed only on the next human-approved task.

Constraints for this active work:

- Keep HKv14 as POC/mock/stub bridge work unless explicitly promoted.
- Do not claim production readiness for HKv14 downstream automation.
- Do not change schemas, prompts, default models, or roadmap phase boundaries without explicit approval and evidence.
- Keep deterministic validation visible; do not hide duplicate/advisory warnings to make flows look cleaner.

## Required Change Summary

For any substantial change, provide:

- change summary,
- roadmap phase or task mapping,
- acceptance items addressed,
- files changed,
- tests run or added,
- schema or prompt impact,
- known limitations,
- rollback considerations,
- self-evaluation using PASS / PARTIAL / FAIL where relevant.

## Stop and Escalate When

Stop and surface the issue if:

- a required prerequisite, schema, benchmark, or gate record is missing,
- the request implicitly crosses phase boundaries,
- a contract change affects downstream artifacts,
- a prompt or model change lacks benchmark evidence,
- a new stage is being added without a contract.

## Detailed Rules

Detailed agent operating rules live in:

- `docs/governance/agent_guidelines.md`
- `docs/governance/model_governance.md`
- `docs/governance/acceptance.md`
