# Agent Entry Rules

Read this file first before making non-trivial changes in this repo.

This repository is governed by contracts, phase boundaries, and acceptance gates.
Agents may implement the roadmap, but must not silently redefine it through code or document changes.

## Read Order

For substantial work, read these files in order:

1. `docs/roadmap.md`
2. `docs/implementation_plan.md`
3. `docs/acceptance.md`
4. `docs/architecture.md`
5. `docs/model_governance.md`
6. `docs/agent_guidelines.md`

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

Every commit should refresh `docs/session_handoff.md`.

Preferred path:

- enable repo hooks once with `powershell -ExecutionPolicy Bypass -File scripts/setup_git_hooks.ps1`
- let the post-commit hook regenerate the handoff automatically

If hooks are unavailable, update the handoff manually before committing:

```text
powershell -ExecutionPolicy Bypass -File scripts/update_session_handoff.ps1
```

## Checkpoint Preservation Rule

Whenever an agent generates a checkpoint and resume prompt, it must append or refresh the record in `docs/checkpoints.md`.

The record must include:

- current task goal,
- confirmed key facts,
- files modified or inspected,
- remaining work,
- next single action,
- constraints that must not be violated,
- a directly reusable resume prompt.

Keep the latest checkpoint easy to find at the top of `docs/checkpoints.md`, and preserve older checkpoints below it unless a human explicitly asks to prune them.

## Current Phase Bias

The current roadmap is biased toward:

1. upstream rule governance,
2. reproducible CI baseline,
3. source-anchor traceability,
4. model and prompt provenance,
5. checker stability visibility on a small baseline set.

Do not prioritize heavier future-platform work over these controls unless explicitly directed.

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

- `docs/agent_guidelines.md`
- `docs/model_governance.md`
- `docs/acceptance.md`
