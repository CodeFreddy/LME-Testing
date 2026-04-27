# LME Testing — Revised Acceptance Criteria

**版本：** 2.0  
**修订日期：** 2026-04-18  
**修订说明：** 在原有 gate 基础上新增 `Verification Type` 字段，区分三种完成状态。

---

## 验证类型定义

| 类型 | 含义 |
|------|------|
| `code_implementation` | 代码写出来了，逻辑上正确 |
| `stub_verified` | 用 StubProvider 或 POC（≤2条规则）验证通过 |
| `real_data_verified` | 用真实 LLM API 和真实规模数据验证通过 |

**原则：** 只有 `real_data_verified` 才代表功能在生产可信场景下得到验证。`stub_verified` 是必要的但不充分。

---

## 通用验收规则

1. **无证据不完成** — gate 未有明确 Evidence 不得标记完成
2. **契约变更需协调更新** — artifact 格式变更必须同时更新 schema + test + docs + acceptance
3. **模型/prompt 变更需 regression** — 新模型或 prompt 版本必须有 benchmark 证据
4. **不得跨 Phase** — 不得将后阶段工作标记为当前 Phase 完成
5. **结构化输出保持结构化** — 现有 JSON 输出模块不得改为自由文本
6. **新增：governance signal 必须标注数据来源** — `real_api` / `stub` / `no_data`

---

## Phase 1 — Baseline Control and Pipeline Hardening

**完成日期：** 2026-04-13（代码实现），2026-04-19（Gate 6 真实数据）

### Gate 1：Artifact Schema Gate

**Verification Type：** `real_data_verified`

Evidence：
- 7 套 schema 文件已提交
- CI schema-validation job 通过
- valid/invalid fixtures 均按预期通过/失败

**状态：** ✅ COMPLETE

---

### Gate 2：Upstream Validation Pipeline Gate

**Verification Type：** `real_data_verified`

Evidence：
- `validate_rules.py` 验证 atomic + semantic rules
- CI upstream-validation job 通过
- 183 条 LME 规则通过验证

**状态：** ✅ COMPLETE

---

### Gate 3：Baseline CI Gate

**Verification Type：** `stub_verified`（smoke test 基于 stub + poc_two_rules）

Evidence：
- 6 个 CI job 在 push/PR 时自动运行
- smoke_test.py 使用 StubProvider 无 API 费用运行

**状态：** ✅ COMPLETE（stub 验证）

**注：** 全量规则集的 smoke 路径未验证，但这超出 CI smoke 的设计范围。

---

### Gate 4：Model and Prompt Metadata Gate

**Verification Type：** `stub_verified`

Evidence：
- maker/checker artifact 包含 provider、model、prompt_version、run_timestamp、pipeline_version
- `check_model_governance.py` 验证通过

**状态：** ✅ COMPLETE

---

### Gate 5：Stable Source Anchor Gate

**Verification Type：** `real_data_verified`

Evidence：
- `paragraph_id` 字段添加到 AtomicRule schema
- `paragraph_ids` 添加到 semantic_rule source 小节
- 183 条 LME 规则已更新 `paragraph_id`
- 唯一性验证在 `validate_rules.py` 中实现

**状态：** ✅ COMPLETE

---

### Gate 6：Checker Stability Gate

**Verification Type：** `real_data_verified`

Evidence（v3 measurement，2026-04-19）：
- `scripts/checker_stability.py` 真实 API 双次运行（full rules v3）
- stability_report: `runs/checker-stability/20260418T231915+0800-v3/stability_report.json`
- `data_source: "real_api"` ✅
- Run A: 63 reviews; Run B: 10 reviews（53 cases missing due to API disconnect）
- `total_cases: 63`（comparable cases appearing in both runs）
- `stable_count: 4`，`unstable_count: 6`
- `instability_rate: 9.5%`（6/63，**> 5% threshold**）
- **触发条件满足：** instability > 5% → `docs/governance/model_governance.md` 已记录分析

**Poc_two_rules 特定测量：**
- `runs/stability_real/stability_report.json` 中 `review_count: 0`（maker cases 路径无效，无有效数据）
- `stability_real` 目录的双次运行因 maker cases 路径错误未能执行

**状态：** ✅ COMPLETE（基于 full rules v3 数据；poc_two_rules 特定测量因 API 可靠性问题未能获得有效数据）

---

### Gate 7：Documentation Gate

**Verification Type：** `real_data_verified`

Evidence：
- roadmap.md, implementation_plan.md, acceptance.md, architecture.md, model_governance.md, agent_guidelines.md 均已提交
- 本次修订为 v2.0，更新为诚实的状态描述

**状态：** ✅ COMPLETE（已更新至 v2.0）

---

### Phase 1 Exit Criteria

| 条件 | 状态 |
|------|------|
| 核心规则 artifact 在 CI 中 schema 验证 | ✅ |
| 无效 rule_type 硬失败 | ✅ |
| 结构化验证报告可产出并阻止下游执行 | ✅ |
| 可复现的 minimal smoke 存在于 CI | ✅（stub）|
| smoke 路径无真实 LLM API 调用 | ✅ |
| maker/checker artifact 记录模型和 prompt metadata | ✅ |
| checker instability 可在 baseline set 上显示 | ✅（9.5% instability，Gate 6 已更新）|
| stable source anchor 存在于 governed upstream artifact | ✅ |
| 治理文档在 repo 中存在 | ✅ |

**Phase 1 完成度：** ✅ 代码层面完成 / ⚠️ Checker Stability 待真实数据验证

---

## Stage 1 — 真实数据接入（当前阶段）

### Gate S1.1：Schema Signal 数据来源修复

**Verification Type：** `real_data_verified`

**验收标准：**
- `validate_schemas.py --output-json` 产出合法 JSON
- CI 写入 `runs/schema_validation_latest.json`
- `governance_signals.json` 中 `schema_signal_source: "real_validation"`
- 故意引入 invalid fixture 时 `schema_failure_rate > 0`

**Evidence（2026-04-19）：**
- `runs/schema_validation_latest.json` 存在，370 fixtures validated，0 failures
- `compute_governance_signals()` → `schema_signal_source: "real_validation"`
- `test_schema_failure_rate_detects_invalid_fixtures` 测试通过：写入 1 invalid/10 total → `failure_rate = 0.1 > 0`
- `validate_schemas.py --output-json runs/schema_validation_latest.json` 可正常执行

**状态：** ✅ COMPLETE

---

### Gate S1.2：Governance 路径对齐

**Verification Type：** `real_data_verified`

**验收标准：**
- `docs/architecture/run_directory_structure.md` 存在
- `governance_signals.json` 中 `runs_analyzed > 0`
- `coverage_signals.total_rules ≥ 180`

**Evidence（2026-04-19）：**
- `docs/architecture/run_directory_structure.md` 存在并描述完整 run 类型结构
- `compute_governance_signals()` → `runs_analyzed = 21 > 0`
- `coverage_signals.total_rules = 180 ≥ 180`
- `coverage_signals.latest_coverage_percent = 72.78%`
- 当前 `runs/` 包含 maker_v1.1_full、baseline_full 等全量运行

**状态：** ✅ COMPLETE

---

### Gate S1.3：Checker 真实稳定性

**Verification Type 目标：** `real_data_verified`

**验收标准：**
- `stability_report.json` 包含 `data_source: "real_api"`
- `docs/governance/acceptance.md` Gate 6 更新为真实数字
- 若 instability > 5%：`model_governance.md` 有分析记录

**当前 instability_rate：** 9.5%（6/63 comparable cases，v3 measurement）

**Evidence（2026-04-19）：**
- `runs/checker-stability/20260418T231915+0800-v3/stability_report.json`
- `data_source: "real_api"`
- `docs/governance/model_governance.md` 记录超过 5% 阈值的分析
- poc_two_rules 特定测量因 API 可靠性问题没有有效数据

**状态：** ✅ COMPLETE（full rules v3；样本受 API disconnect 限制）

---

### Gate S1.4：全量规则质量基准

**Verification Type 目标：** `real_data_verified`

**验收标准：**
- `coverage_report.json` 包含 ≥ 180 条规则
- `docs/releases/BASELINE-183-RULES.md` 存在（含人工抽查记录）
- coverage 数字如实记录（不掩盖低覆盖率）

**当前 coverage（全量）：** 72.78% baseline（131/180 fully covered）；S2-T01 v1.5 后 78.89%（142/180 fully covered）

**Evidence（2026-04-19 baseline）：**
- `docs/releases/BASELINE-183-RULES.md`
- `evidence/20260419_baseline_full/`
- coverage_report 包含 180 条可测试规则

**状态：** ✅ COMPLETE

---

### Gate S1.5：状态声明诚实性

**Verification Type：** `real_data_verified`

**验收标准：**
- README 无 "All Phases Complete" 表述
- 所有 "100%" 声明注明数据基础
- acceptance.md 每个 gate 有 Verification Type

**Evidence（2026-04-19）：**
- README.md Verification Status 表格已更新：S1.1 ✅ Complete, S1.2 ✅ Complete
- README.md 无 "All Phases Complete" 表述
- acceptance.md 每个 gate（含 Stage 1 S1.1/S1.2）有 Verification Type

**状态：** ✅ COMPLETE

---

## Phase 2 — Planned Test Design and Normalized BDD

**完成日期：** 2026-04-13（代码实现）  
**注意：** 所有 gate 基于 poc_two_rules（2条规则）验证，全量质量待 Stage 1 建立基准后评估。

### Gate 2.1：Multi-Document Ingestion

**Verification Type：** `stub_verified`

Evidence：
- `scripts/document_classes.py`：DocumentClass enum, 4 种 parsing strategy
- poc_two_rules 端到端通过

**已知限制：**
- 实现为 enum + keyword matching，不是结构感知的文档解析框架
- 复杂布局 PDF 提取质量未验证

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 复杂文档质量未知

---

### Gate 2.2：Planning Layer

**Verification Type：** `stub_verified`

Evidence：
- `schemas/planner_output.schema.json` 存在
- `run_planner_pipeline` 实现
- poc_two_rules planner 运行验证通过

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.3：Normalized BDD Contract

**Verification Type：** `stub_verified`

Evidence：
- `schemas/normalized_bdd.schema.json` 存在
- `run_bdd_pipeline` 实现
- BDD export 产出 .feature 文件
- poc_two_rules 验证通过

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.4：Traceability

**Verification Type：** `stub_verified`

Evidence：
- paragraph_ids 贯穿 planner → maker → BDD 流水线
- HTML report 可点击 rule ID 跳转

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.5：Step Visibility

**Verification Type：** `stub_verified`

Evidence：
- `src/lme_testing/step_registry.py` 实现 3-tier matching
- poc_two_rules step visibility 报告生成

**已知限制：**
- step library 基于模拟 LME API，step binding rate 35.4% 无实际意义
- 真实 binding rate 待 Stage 3 接入真实 API 后测量

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 真实 binding rate 未知

---

### Gate 2.6：Quality and Drift Reporting

**Verification Type：** `stub_verified`

Evidence：
- `scripts/generate_trend_report.py` 实现
- HTML report 有 coverage trend、dropdown 过滤器、rule ID 跳转

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.7：Model Governance Enforcement

**Verification Type：** `stub_verified`

Evidence：
- `scripts/check_model_governance.py` 实现
- `config/approved_providers.json` 存在

**状态：** ✅ COMPLETE（stub 验证）

---

## Stage 2 Extension — Governed HKv14 Role Review Slice

### Gate S2-F1：HKv14 Role-Friendly Impact Decision Review

**Verification Type 目标：** `stub_verified` for local UI/review surface and deterministic validation; no real execution readiness claim.

**状态：** ✅ COMPLETE（local deterministic package generator）

**Source plan：**
- `docs/planning/im_hk_v14_role_review_plan.md`

**验收标准：**
- Existing HKv13 baseline artifacts and deliverables remain untouched. ✅
- HKv14 remains scoped as POC/mock/stub downstream baseline candidate work. ✅
- Every reviewed candidate links back to deterministic HKv13→HKv14 diff evidence or documented downstream treatment mapping. ✅
- Structured decision record JSON is canonical and validates deterministically. ✅
- Markdown decision summary is derived from the structured decision record. ✅
- Reviewer role, reviewer name, decision, rationale, comments, and timestamp are captured. ✅
- Allowed role and decision values are enforced. ✅
- Focused tests cover load, save, validation failure, and Markdown export. ✅
- Docs governance and artifact governance checks pass. ✅

**Evidence（2026-04-27）：**
- `src/lme_testing/im_hk_v14_role_review.py`
- `tests/test_im_hk_v14_role_review.py`
- CLI command: `python main.py im-hk-v14-role-review`
- Generated review package contains canonical `decision_record.json`, derived `decision_summary.md`, and local `review.html`.
- `.venv\Scripts\python.exe -m unittest tests.test_im_hk_v14_role_review -v`: passed, 5 tests OK.

**Non-acceptance boundaries：**
- No new LLM-driven stage is accepted under this gate.
- No prompt, schema, or default model change is accepted under this gate.
- No automatic test case update, automatic code generation, generic document platform, or Stage 3 real execution claim is accepted under this gate.

---

## Phase 3 — Execution Readiness

**完成日期：** 2026-04-14（代码实现）  
**注意：** 以下 gate 的"完成"均为代码层面，执行层面核心价值（真实 LME API 接入）待 Stage 3。

### Gate 3.1：Step Definition Integration

**Verification Type：** `stub_verified`（⚠️ step library 基于模拟 API）

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 真实执行能力待 Stage 3

---

### Gate 3.2：Execution Readiness

**Verification Type：** `code_implementation`（无真实消费者验证）

Evidence：
- `schemas/executable_scenario.schema.json` 存在
- 14 个 schema 测试通过

**已知限制：** 没有任何系统真实消费 ExecutableScenario 产出并执行测试

**状态：** ✅ COMPLETE（code only）/ ⚠️ 无真实执行验证

---

### Gate 3.3：Deterministic Oracle

**Verification Type：** `stub_verified`（⚠️ 未在真实 LME 规则场景验证）

Evidence：
- 8 个 oracle 模块，38 个单元测试通过

**已知限制：** oracle 单元测试使用人工构造的测试数据，未在真实 LME checker 场景中验证

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 真实场景验证待 Stage 2

---

### Gate 3.4：Governance Signals

**Verification Type：** `code_implementation`（2/4 信号数据为空或 stub）

Evidence：
- signals 框架实现，4 类信号数据结构
- CI governance-signals job 运行

**当前信号可信度：**

| 信号 | 数据来源 | 可信度 |
|------|---------|--------|
| schema_failure_rate | 无（推断）| ⚠️ 假数据 |
| checker_instability | StubProvider | ⚠️ 不代表真实 LLM |
| coverage_percent | 全量运行（路径未对齐）| 🔄 待对齐 |
| step_binding_rate | 模拟 step lib | ⚠️ 无实际意义 |

**状态：** ✅ COMPLETE（code only）/ ⚠️ 信号数据待 Stage 1 修复

---

### Gate 3.5：Release Governance

**Verification Type：** `stub_verified`

Evidence：
- `config/approved_providers.json`, `config/compatibility_matrix.json`, `config/benchmark_thresholds.json`
- `docs/releases/RELEASES.md`
- `scripts/check_release_governance.py` 通过

**已知限制：** benchmark evidence 基于 stub/poc_two_rules，全量质量基准待 Stage 1

**状态：** ✅ COMPLETE（stub 验证）

---

## Stage 2 — Quality Improvement, Mock Execution Bridge, and UI Assurance

### Gate S2.1：Maker/Checker Coverage Calibration

**Verification Type：** `real_data_verified`

**验收标准：**
- 全量 180-rule maker/checker 运行完成
- coverage 数字如实记录
- prompt 变更有版本记录和 benchmark evidence
- 剩余 gap 有 root-cause 分类

**Evidence（2026-04-21）：**
- `docs/planning/s2t01_coverage_analysis.md`
- v1.5 maker/checker runs：`runs/maker/20260421T074319Z/`、`runs/checker/20260421T083003Z/`
- Coverage：78.89%（142/180 fully covered）
- 结论：剩余 gap 为 evidence-constrained 或 LLM non-determinism

**状态：** ✅ COMPLETE

---

### Gate S2.2：Audit Trail and Case Compare

**Verification Type：** `code_implementation`

**验收标准：**
- `audit_trail.py` 生成 maker → checker → human decision chain HTML
- `case_compare.py` 生成相邻 iteration case 对比 HTML
- 两者集成到 `review_session.py`
- 生成失败不隐藏，但不阻塞主 session 流程

**Evidence（2026-04-21）：**
- `src/lme_testing/audit_trail.py`
- `src/lme_testing/case_compare.py`
- `review_session.py` finalize/rewrite 集成

**状态：** ✅ COMPLETE

---

### Gate S2.3：Mock API Execution Bridge

**Verification Type：** `stub_verified`

**验收标准：**
- mock API 基于 `docs/materials/LME_Matching_Rules_Aug_2022.md` 的代表性规则
- BDD step definitions 通过 HTTP 调用 mock API
- feature suite 可本地运行并通过
- README、源码、zip 交付物存在
- 文档明确 mock bridge 不等于真实 LME API 接入

**Evidence（2026-04-23）：**
- `deliverables/lme_mock_api/`
- `deliverables/lme_mock_api.zip`
- `docs/planning/mock_api_validation_plan.md`
- `python run_bdd.py`：33 passed, 0 failed
- `python -m unittest tests.test_mock_api`：2 tests OK

**状态：** ✅ COMPLETE（mock/stub execution bridge；真实 Stage 3 仍阻塞）

---

### Gate S2.4：Review UI Browser E2E

**Verification Type：** `stub_verified`

**验收标准：**
- Browser test 启动真实 local review-session HTTP server
- Browser test 使用 deterministic fixture artifacts，不调用 live LLM provider
- Review -> BDD -> Scripts 主路径可在真实浏览器中执行
- BDD textarea 未保存内容在 tab navigation 后不丢失
- Save BDD Edits 后 Scripts tab 可见 match metrics 刷新
- Save Scripts Edits 后可见 exact/unmatched 指标更新
- 无浏览器环境下测试应 skip，而不是伪造通过

**Evidence（2026-04-23）：**
- `tests/test_review_session_browser.py`
- `docs/planning/ui_test_plan.md`
- `.venv\Scripts\python.exe -m unittest tests.test_review_session_browser -v`：1 browser test OK
- `.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`：181 tests OK
- Browser runner：installed Chrome/Edge via Chrome DevTools Protocol

**状态：** ✅ COMPLETE（browser-level primary BDD/Scripts path；submit/finalize browser flow 未覆盖）

---

### Gate S2.5：Initial Margin HKv13 Mock API Execution Bridge

**Verification Type：** `stub_verified`

**验收标准：**
- mock API 基于 `docs/materials/Initial Margin Calculation Guide HKv13.pdf` 与 `artifacts/im_hk_v13/` 的代表性计算/数据规则
- BDD step definitions 通过 HTTP 调用 mock API
- feature suite 可本地运行并通过
- README、源码、zip 交付物存在
- 文档明确 mock bridge 不等于真实 Initial Margin execution readiness

**Evidence（2026-04-26）：**
- `deliverables/im_hk_v13_mock_api/`
- `deliverables/im_hk_v13_mock_api.zip`
- `docs/planning/im_hk_v13_mock_api_validation_plan.md`
- `python -m compileall deliverables/im_hk_v13_mock_api`：passed
- `python -m unittest discover -s deliverables\im_hk_v13_mock_api\tests -t deliverables\im_hk_v13_mock_api -v`：4 tests OK；BDD summary 37 passed, 0 failed
- Section 3.2.4.2 Flat Rate Margin POC：expected flat rate margin `15,180,000`

**状态：** ✅ COMPLETE（mock/stub execution bridge；真实 Stage 3 仍阻塞）

---

### Gate S2.6：Initial Margin HKv14 POC Document Workflow And Modular Mock API Bridge

**Verification Type：** `stub_verified`

**验收标准：**
- HKv14 PDF input produces governed artifacts without weakening artifact contracts
- HKv13→HKv14 deterministic diff evidence is generated and reviewable
- POC downstream decision note records accepted deterministic diff candidates
- HKv14 mock bridge reuses shared common implementation and keeps HKv13 deliverable preserved
- BDD step definitions call the HKv14 mock API through HTTP
- README、源码、zip 交付物存在
- 文档明确 HKv14 POC bridge 不等于 production downstream automation readiness

**Evidence（2026-04-26）：**
- `artifacts/im_hk_v14/`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`
- `docs/planning/im_hk_v14_diff_report.md`
- `docs/planning/im_hk_v14_downstream_decision.md`
- `docs/planning/im_hk_v14_mock_api_validation_plan.md`
- `deliverables/im_hk_mock_api_common/`
- `deliverables/im_hk_v14_mock_api/`
- `deliverables/im_hk_v14_mock_api.zip`
- `.venv\Scripts\python.exe -m unittest tests.test_compare_initial_margin_versions -v`：passed
- `.venv\Scripts\python.exe -m unittest tests.test_extract_matching_rules -v`：passed
- `.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v14_mock_api\tests -t deliverables\im_hk_v14_mock_api -v`：3 tests OK；BDD summary 37 passed, 0 failed
- `.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`：193 tests OK, 1 skipped when Chrome DevTools unavailable
- `.venv\Scripts\python.exe scripts/check_docs_governance.py`：passed
- `.venv\Scripts\python.exe scripts/check_artifact_governance.py`：passed

**状态：** ✅ COMPLETE（HKv14 POC/mock/stub bridge；真实 Stage 3 和 production downstream automation 仍不声明完成）

---

### Gate S2.7：Initial Margin HKv14 Promoted Downstream Slice

**Verification Type：** `stub_verified`

**验收标准：**
- promotion scope exists and records explicit human approval
- 10 HKv13→HKv14 changed candidates and 1 ID drift candidate are mapped to downstream treatment categories
- required HKv14-specific BDD/data/test changes are identified before implementation
- HKv13 deliverable remains preserved
- HKv13 and HKv14 validation commands pass after any implementation change
- docs and artifact governance checks pass
- schema, prompt, and model impact remains none unless a separate governed task is opened

**Evidence（2026-04-26）：**
- `docs/planning/im_hk_v14_promotion_scope.md`
- `docs/planning/im_hk_v14_downstream_treatment_mapping.md`
- `docs/planning/im_hk_v14_mock_api_validation_plan.md`
- updated `deliverables/im_hk_v14_mock_api/data/flat_rate_margin_poc.json`
- updated `deliverables/im_hk_v14_mock_api/tests/test_mock_api.py`
- updated `deliverables/im_hk_v14_mock_api/features/initial_margin/flat_rate_margin_poc.feature`
- refreshed `deliverables/im_hk_v14_mock_api.zip`
- `.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v14_mock_api\tests -t deliverables\im_hk_v14_mock_api -v`：passed, 3 tests OK；BDD summary 37 passed, 0 failed
- `.venv\Scripts\python.exe deliverables\im_hk_v14_mock_api\poc_flat_rate_margin.py`：passed
- `.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v13_mock_api\tests -t deliverables\im_hk_v13_mock_api -v`：passed, 4 tests OK；BDD summary 37 passed, 0 failed
- `.venv\Scripts\python.exe scripts/check_docs_governance.py`：passed
- `.venv\Scripts\python.exe scripts/check_artifact_governance.py`：passed

**状态：** ✅ COMPLETE（promoted mock/stub downstream baseline candidate；真实 Stage 3 和 production downstream automation 仍不声明完成）

---

## 证据模板

每个完成的 roadmap 项应提供：

```
变更摘要：
修改文件：
验证类型：[code_implementation / stub_verified / real_data_verified]
数据来源：[stub / real_api / no_data]（适用于 governance signals）
已测试项：
产生的 artifacts：
已知限制：
回滚影响：
```

