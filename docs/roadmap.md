# Enterprise AI Testing Upgrade Roadmap

## 1. Current Starting Point

The current system is a **document-driven test design prototype**. It already supports a usable design loop:

`source docs -> extract scripts -> atomic_rules.json -> semantic_rules.json -> maker -> checker -> review-session -> rewrite -> checker -> report`

Today, the framework can already:

* extract rules from source documents into `atomic_rule` and `semantic_rule` artifacts,
* generate BDD-style scenarios through `maker`,
* assess scenario quality and rule coverage through `checker`, with strict coverage defined by `rule_type -> required_case_types`,
* support human approval / rewrite / reject decisions in a local review session,
* regenerate artifacts and produce final HTML reports.

The current weaknesses are also clear:

* rule extraction governance is not presented as a first-class validation layer,
* model and prompt stability governance are not explicit in the public workflow,
* review is local and single-user oriented,
* the repo still looks early-stage, with 2 commits and no published releases.

## 2. Upgrade Principles

These principles apply across all phases.

### 2.1 Model outputs must be governed, not trusted

All LLM-driven steps must be treated as probabilistic. Every model-facing module must be constrained by:

* explicit schemas
* versioned prompts
* artifact metadata
* regression baselines
* rollbackable model configuration

### 2.2 Upstream rule quality controls downstream value

No downstream improvement can compensate for invalid `atomic_rule` or `semantic_rule` inputs. Upstream validation is mandatory before expanding downstream scope.

### 2.3 Separate deterministic responsibilities from LLM-assisted responsibilities

LLMs may assist with:

* rule normalization
* ambiguity detection
* test planning drafts
* BDD generation suggestions

Deterministic modules must own:

* schema validation
* enum validation
* coverage accounting
* traceability checks
* duplicate detection thresholds
* execution result assertions where possible

### 2.4 Every phase must define both scope and non-scope

Each phase must explicitly state what is included and what is deferred, to avoid uncontrolled expansion.

### 2.5 AI agents must work against contracts, not free-form instructions

Any AI coding agent contributing to the repo must operate against:

* versioned docs
* fixed acceptance criteria
* schema contracts
* test gates
* no direct undocumented structural changes

## 3. Cross-Model Governance Requirements

These rules must exist before or alongside any feature growth.

### 3.1 Provider abstraction

Keep the current OpenAI-compatible provider layer, but formalize it into a model strategy contract:

* provider name
* model name
* model version if available
* prompt version
* temperature / key decoding settings
* timeout / retry settings

All artifacts produced by maker, checker, rewrite, and future planner modules must record this metadata.

### 3.2 Prompt versioning

Every prompt used in production workflows must have:

* a stable prompt ID
* semantic version
* owner
* change log
* linked benchmark set

### 3.3 Regression baseline

The repo already recommends `artifacts/poc_two_rules/semantic_rules.json` as a fast validation entry point. That should become the first official baseline suite.

Required baseline categories:

* extraction sanity
* maker structural validity
* checker consistency
* report generation
* end-to-end smoke

### 3.4 Model compatibility policy

Any new model API may only be adopted if it passes:

* schema conformance
* benchmark threshold
* checker stability threshold
* artifact diff review

### 3.5 Rollback policy

A new model or prompt version must be reversible without changing business logic or artifact schemas.

---

# 4. Short-Term Plan (0–3 months)

## 4.1 Stage Goal

Stabilize the current design pipeline so that different model APIs can be used without silently degrading artifact quality.

## 4.2 In Scope

* extraction validation
* schema formalization
* rule type governance
* baseline CI
* prompt / artifact versioning
* checker stability visibility
* repo documentation for AI agent execution

## 4.3 Out of Scope

* multi-user hosted review platform
* execution engine
* step definition integration
* advanced planning intelligence
* full enterprise workflow orchestration

## 4.4 Key Deliverables

### A. Formal schema layer

Add versioned JSON Schemas for:

* `atomic_rule`
* `semantic_rule`
* maker output
* checker output
* human review output

### B. Rule validation pipeline

Insert a formal validation stage:

`docs -> extraction scripts -> atomic_rules.json -> schema validation -> duplicate candidate detection -> rule_type enum validation -> semantic_rules.json`

### C. Minimal rule quality gates

Implement:

* required fields validation
* `rule_type` enum enforcement
* duplicate candidate detection
* invalid trace reference detection
* schema failure as hard-stop

### D. Prompt and artifact metadata

Every generated artifact must include:

* prompt version
* model ID
* provider
* run timestamp
* source artifact hash
* pipeline version

### E. Baseline CI

Add GitHub Actions to run:

* end-to-end smoke on `poc_two_rules`
* schema validation tests
* reporting smoke test
* core unit tests for pipeline and review session bootstrapping

### F. Checker stability signal

Run checker twice on the same small baseline and flag inconsistent conclusions.

### G. Repo docs for AI agents

Add:

* `docs/roadmap.md`
* `docs/acceptance.md`
* `docs/model_governance.md`
* `docs/agent_guidelines.md`

## 4.5 Acceptance Criteria

Short-term phase is accepted only if:

* all core artifacts are schema-validated in CI
* invalid `rule_type` values fail the pipeline
* baseline smoke run is reproducible in CI
* every maker/checker artifact records model and prompt metadata
* checker instability can be surfaced on the baseline set
* roadmap and governance docs are present in the repo

## 4.6 Success Metric

The system becomes **trustworthy enough for repeated internal development**, even if it is not yet enterprise-ready.

---

# 5. Mid-Term Plan (3–9 months)

## 5.1 Stage Goal

Upgrade from a stable design prototype into an AI-assisted **test planning and BDD generation platform** that can handle multiple document categories and produce reusable test design outputs.

## 5.2 In Scope

* document-type aware ingestion
* planning layer above maker/checker
* richer traceability
* improved review collaboration
* BDD normalization
* export interfaces for downstream execution teams

## 5.3 Out of Scope

* full runtime execution of all generated scenarios
* autonomous end-to-end execution against all systems
* full enterprise RBAC and production multi-tenant platform

## 5.4 Key Deliverables

### A. Multi-document ingestion framework

Support defined source classes, for example:

* rulebooks
* product specs
* API docs
* business workflow docs
* compliance / policy docs
* release notes / change documents

Each document class must have:

* parsing strategy
* extraction constraints
* expected rule patterns
* known failure modes

### B. Test planning layer

Introduce a planner stage between `semantic_rule` and BDD generation.

New flow:

`semantic_rules -> planning -> test objectives -> scenario families -> BDD generation`

The planner should produce:

* priority
* risk level
* coverage intent
* scenario family
* dependency notes
* recommended validation strategy

### C. Traceability model

Each final BDD scenario must trace back to:

* source document
* source clause / section
* atomic rule
* semantic rule
* planning decision
* checker verdict
* human review outcome

### D. BDD contract layer

Define a normalized BDD representation independent of final output syntax. This becomes the stable handoff artifact before step integration.

### E. Review collaboration v1

Add file-based or bundle-based review exchange:

* export review package
* import review package
* merge review decisions
* conflict surfacing

### F. Quality dashboards

Enhance reports with:

* rule_type coverage heatmap
* unstable checker decisions
* baseline drift versus previous runs
* document class breakdown
* traceability drill-down
* JSON/CSV export

## 5.5 Acceptance Criteria

Mid-term phase is accepted only if:

* at least 3 document classes are supported with explicit parsing rules
* planner outputs are versioned and schema-validated
* generated BDD artifacts are normalized and traceable
* review packages can be exported and merged
* report can show historical diffs and unstable judgments
* model change regression is enforced before adoption

## 5.6 Success Metric

The system becomes **usable for controlled team pilots** in document-driven test planning and BDD generation.

---

# 6. Long-Term Plan (9–18 months)

## 6.1 Stage Goal

Evolve the framework into an **enterprise AI testing platform** that connects document learning, planning, BDD generation, and execution integration with existing step definitions.

## 6.2 In Scope

* step definition mapping
* execution abstraction
* deterministic assertion layer
* hosted collaborative review service
* enterprise governance and observability
* controlled rollout across model providers

## 6.3 Out of Scope

* unrestricted autonomous test execution without approval gates
* fully free-form agentic code generation without schema and review controls

## 6.4 Key Deliverables

### A. Step definition integration layer

Create a mapping layer between normalized BDD steps and existing step definitions.

This should support:

* exact step match
* parameterized step match
* candidate step suggestion
* unmatched step reporting
* reuse score
* ownership per step library

### B. Execution readiness contract

Introduce an `ExecutableScenario` representation that extends BDD with:

* environment requirements
* input data requirements
* setup hooks
* expected deterministic assertions
* cleanup hooks
* linked step definitions

### C. Deterministic oracle framework

Move execution truth away from LLM judgment wherever possible.

Deterministic modules should own:

* field validation
* state validation
* calculation validation
* deadline/window checks
* event sequence verification
* pass/fail accounting

### D. Hosted review and governance service

Upgrade review-session from local HTTP service to deployable web service with:

* user accounts
* reviewer roles
* audit trail
* conflict resolution
* comment threads
* assignment workflow

### E. Enterprise observability

Track:

* ingestion failure rate
* extraction drift
* duplicate / conflict rule rate
* planner change rate
* maker validity rate
* checker instability rate
* BDD reuse rate
* step binding success rate
* execution pass/fail distribution

### F. Release governance

Formalize:

* release tags
* compatibility matrix
* benchmark gates
* migration notes
* approved provider list

## 6.5 Acceptance Criteria

Long-term phase is accepted only if:

* normalized BDD can be bound to existing step definitions with measurable reuse
* unmatched steps are surfaced automatically
* execution-ready scenarios can be exported consistently
* hosted review supports multi-user auditability
* deterministic assertions exist for at least the core structured rule categories
* provider rollout requires benchmark pass and rollback path
* enterprise-level metrics are available for audit and platform operation

## 6.6 Success Metric

The system becomes **enterprise-usable as an AI-assisted testing platform**, not just a design prototype.

---

# 7. What AI Agents Must Follow

Any AI coding agent working on this roadmap must obey these repo-level rules:

## 7.1 Do not bypass schemas

No artifact format change is allowed without:

* schema update
* migration note
* acceptance update
* test update

## 7.2 Do not couple business logic to a specific model

All provider-specific behavior must remain behind provider or strategy interfaces.

## 7.3 Do not introduce free-form outputs where structured outputs exist

If a module currently emits JSON, keep it structured.

## 7.4 Do not expand scope across phases

Short-term work must not add mid-term or long-term concerns unless explicitly approved.

## 7.5 Every feature must ship with an acceptance test

No roadmap item is complete without a testable acceptance condition.

---

# 8. Recommended Repo Document Structure

## README.md

Keep concise:

* what the project is
* current workflow
* current scope
* quick start
* link to roadmap and governance docs

## docs/roadmap.md

Contains the phased plan above.

## docs/architecture.md

Defines:

* pipeline stages
* artifact contracts
* module boundaries
* deterministic vs LLM-owned responsibilities

## docs/acceptance.md

Lists phase-based acceptance criteria and benchmark gates.

## docs/model_governance.md

Defines:

* provider abstraction
* model onboarding rules
* prompt versioning
* baseline regression
* rollback policy

## docs/agent_guidelines.md

Defines how AI coding agents are allowed to modify the repo.

## docs/step_integration_plan.md

Reserved for the long-term BDD-to-step-definition integration design.

---

# 9. One-Paragraph Summary for the Repo

This project should evolve in three controlled stages. Short-term, it must stabilize the current document-to-rule-to-BDD design pipeline with schemas, CI, and model governance. Mid-term, it should add document-aware planning, normalized BDD, traceability, and collaborative review so teams can pilot it safely. Long-term, it should integrate with existing step definitions, add execution-ready contracts and deterministic assertions, and grow into a governed enterprise AI testing platform. The roadmap assumes multiple LLM APIs may be used, so every stage requires schema contracts, versioned prompts, benchmark gates, and rollback-safe model governance.
