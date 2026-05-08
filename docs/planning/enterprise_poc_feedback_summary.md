# Enterprise POC Feedback Summary

**Date:** 2026-05-08  
**Source:** End-user POC feedback from SVP, Product Owner, Test Lead, Automation Lead, and testers  
**POC scope:** HKv14 rule workflow GUI and end-to-end test generation flow  
**Status:** Feedback captured for planning. This note does not approve new roadmap scope, schema changes, prompt changes, default model changes, or production readiness claims.

---

## Executive Themes

The POC was understood as a useful direction, but the audience expects the next version to move from a local demonstrator toward an enterprise-ready testing platform. The main feedback themes were:

- enterprise deployment architecture,
- controlled access to HKEX and source-code execution environments,
- stronger test-scope definition and requirement context,
- clearer human review workflows for BRD, rules, cases, and generated scripts,
- measurable maker/checker quality controls,
- role-specific interfaces and outputs,
- reusable knowledge for onboarding and team practice.

---

## Stakeholder Questions And Comments

### Enterprise Deployment

- Consider Spring AI or a micro-service architecture for enterprise-level deployment.
- Clarify how the system would run inside an enterprise environment rather than as a local POC.
- Confirm whether GitHub Copilot is ready or expected as part of the development workflow.
- Confirm whether generated scripts and test cases can run with the actual source code.

### Environment And System Access

- Confirm system access to the HKEX environment.
- Identify what credentials, network access, VPN, API endpoints, or test environment approvals are required.
- Clarify whether the POC should execute against:
  - local mock API,
  - HKEX test environment,
  - source-code-level service execution,
  - or a controlled enterprise integration environment.

### Test Inputs And Existing Assets

- Determine whether existing test cases are required from the testing team.
- Clarify how existing regression packs, manual test cases, and automation scripts should be imported or referenced.
- Add support for OTP test cases if OTP is part of the business or technical test scope.
- Decide whether generated cases should be compared against existing team-owned cases before approval.

### BRD And Rule Review Process

- Add a BRD split and review process before or alongside rule extraction.
- Allow reviewers to comment in human language, not only by editing structured rules.
- Support comments on individual rules.
- Support comments on a group of cases.
- Preserve business-readable comments as review evidence and audit material.

### Maker/Checker Quality And Measurement

The group raised a key governance concern: maker and checker can both be wrong. If the maker produces an incorrect case and the checker marks it as `Yes` or `Pass`, the workflow needs a way to detect and measure that risk.

Requested controls:

- benchmark sets for known-good and known-bad cases,
- confidence level or quality score,
- sampling checklist for human review,
- explicit review process for `Yes` / `Pass` cases,
- metrics for false positives and false negatives,
- evidence that checker approval is not treated as final truth without human or deterministic validation.

Planning implication:

- Checker output should remain advisory unless supported by deterministic validation, benchmark evidence, or human approval.
- The system should not hide passed cases from review; it should provide sampling and risk-based review paths.

### Test Scope And Requirement Understanding

The group asked how the system defines what to test for a new requirement.

Requested capabilities:

- define rules and test scope before generation,
- explain why a requirement should produce specific test cases,
- identify what is new, changed, unchanged, or out of scope,
- use RAG or a skill/knowledge layer for background context,
- include domain knowledge such as account type, business process, test story, known defects, known team experience, and prior test practice,
- share background context with the maker/checker flow so generated cases are not based only on the current extracted rule text.

Planning implication:

- A future planning layer should capture business context and test-scope decisions before generating cases.
- Context should be governed and traceable, not a hidden prompt-only input.

### Prompt And Team Customization

- Prompts may need customization by business area and team.
- Prompt changes need audit, version control, and rollback.
- Prompt behavior should be role-aware and domain-aware.
- Different teams may need different terminology, case style, priority rules, and review checklist templates.

Governance note:

- Any future prompt customization must preserve benchmark evidence, prompt versioning, model governance, and rollback notes.

### Role-Based Planning And Interfaces

The POC should evolve toward role-specific input and output:

- SVP / Product Owner: scope, priority, risk, readiness, and decision summary.
- Test Lead: test strategy, coverage, review checklist, and approval status.
- Automation Lead: executable coverage, source-code/API binding, script quality, and maintainability.
- Tester: readable cases, comments, expected results, gaps, and reuse guidance.
- Business Analyst: BRD split, rule interpretation, impact notes, and human-language comments.

Requested capability:

- role-based priority planning for test case generation.
- separate interfaces for different role inputs and outputs.

### Knowledge Reuse And New Joiner Training

The POC was seen as useful for onboarding if the system records and reuses business and testing practice.

Requested capability:

- capture business context,
- capture test practice,
- record reviewer comments and decisions,
- reuse prior explanations, known cases, known defects, and team conventions,
- support new joiner training through searchable examples and reviewed knowledge.

Planning implication:

- The system may need a governed knowledge base, but this should be scoped carefully to avoid introducing an ungoverned RAG or LLM stage.

### Rule Extraction Prompt Boundary

Current observation:

- There is no LLM prompt for rule extraction now.
- Rule extraction is currently deterministic/governed in the local POC path.

Open question:

- If an end-to-end enterprise case requires LLM-assisted rule extraction, a new governed stage would be needed.

Governance note:

- A new LLM-driven rule extraction stage must not be added silently. It would require a defined contract, validation, traceability, benchmark evidence, reviewable outputs, and rollback notes.

---

## Product Gaps Raised By The POC

| Area | Gap | Suggested Next Planning Question |
|------|-----|----------------------------------|
| Deployment | Local POC is not enterprise architecture | What target deployment pattern is approved: Spring AI, micro-services, or another enterprise platform? |
| Environment | HKEX access is not yet established | Which HKEX test environment, credentials, and access controls are available? |
| Execution | Source-code execution path is unclear | Should generated scripts run against source code, API, mock API, or HKEX test environment first? |
| Existing assets | Team test cases are not integrated | What existing manual/regression/automation assets should seed or benchmark generation? |
| BRD review | BRD splitting and comments are not first-class | What is the minimum BRD review contract before rule extraction? |
| Case review | Group comments and passed-case sampling are missing | What sampling policy is acceptable for maker/checker `Pass` cases? |
| Quality | Maker/checker can agree on wrong results | What benchmark and confidence model should be used before trusting LLM approval? |
| Context | New requirements need domain background | What governed RAG/skill/context sources are approved? |
| Roles | Single UI does not map to role-specific workflows | Which role-specific views are MVP, and what must each role approve? |
| Training | Reviewed knowledge is not packaged for onboarding | What knowledge should be reusable for new joiner training? |

---

## Candidate Backlog Items

These are candidate planning items only. They are not approved implementation scope.

1. Enterprise deployment architecture note
   - Compare Spring AI, micro-service deployment, local desktop, and internal platform options.
   - Include security, audit, access control, runtime, and model-provider assumptions.

2. HKEX environment access checklist
   - Record required systems, credentials, network paths, API endpoints, test data, and approval owners.

3. Existing test asset intake
   - Define import contracts for manual test cases, regression packs, automation scripts, and OTP-specific test cases.

4. BRD split and business review workflow
   - Add a governed review step for BRD sections, extracted business rules, and human-language comments.

5. Maker/checker benchmark and sampling framework
   - Add benchmark cases, confidence scoring, false-positive review, and sampling checklists.

6. Requirement-to-test-scope planning layer
   - Define how new requirements become test scope, priorities, and case-generation instructions.

7. Governed RAG or skill context layer
   - Capture approved domain context, account types, business processes, known defects, and team practice.

8. Prompt customization governance
   - Define versioning, ownership, benchmark evidence, rollback, and team-specific prompt profiles.

9. Role-based review surfaces
   - Provide separate outputs for Product Owner, Test Lead, Automation Lead, tester, and BA.

10. Knowledge reuse and training package
    - Turn reviewed cases, comments, decisions, and explanations into reusable onboarding material.

---

## Recommended Next Step

Create a bounded planning slice for the next review instead of implementing all feedback at once.

Recommended slice:

`Enterprise POC feedback -> target deployment assumptions -> HKEX/source-code access checklist -> role-based MVP workflow -> maker/checker quality controls`

This slice should produce:

- enterprise deployment assumptions,
- access checklist,
- role-specific workflow map,
- benchmark/sampling proposal,
- prompt and RAG governance boundaries,
- clear non-goals.

This slice is now tracked as S2-F8 in `docs/planning/next_phase_plan.md` and `docs/planning/implementation_plan.md`.

Recommended sequencing:

1. Complete S2-F6A rewrite prompt governance cleanup.
2. Implement S2-F7A read-only Scripts implementation metadata.
3. Prepare S2-F8 enterprise POC response package for stakeholder discussion.

S2-F8 may proceed in parallel only if it remains documentation-only.

---

## Non-Goals Until Explicitly Approved

- Do not claim production readiness.
- Do not add a new LLM rule-extraction stage without a governed contract.
- Do not change default models or prompts without benchmark evidence.
- Do not treat maker/checker `Pass` as final truth without benchmark, deterministic validation, or human review policy.
- Do not implement RAG, enterprise micro-services, HKEX integration, Copilot workflow changes, or source-code execution without separate approval.

