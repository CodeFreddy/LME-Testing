# LME Testing — TODO v3.1

**修订日期：** 2026-05-06
**说明：** 整合 master 分支合并分析、S2-T01 v1.5 结果、S2-B1/B2 集成状态、S2-C1/S2-C2/S2-C3/S2-C4/S2-C5 mock API bridge and deliverables policy work，S2-D1 browser-level review UI E2E，S2-F1 role-friendly HKv14 impact decision review package generator，S2-F2/S2-F3 MVP document readiness registry and input contract implementation，以及 S2-F4 CodeFreddy rule extraction review GUI integration and follow-up GUI fixes。

---

## 状态图例

| 标记 | 含义 |
|------|------|
| ✅ Code | 代码实现完成 |
| ✅ Stub | Stub/POC 验证（2条规则）|
| ✅ Real | 真实数据验证完成 |
| 🔄 In Progress | 进行中 |
| ⏳ Blocked | 等待外部条件 |
| ❌ Not Started | 未开始 |
| 🧊 Frozen | 暂缓 |
| 🍒 Cherry-pick | 来自 master 分支的改进 |

---

## Stage M — Master 分支合并 ✅ COMPLETE

**完成日期：** 2026-04-19

### SM-T01：Vendor 存档 ✅
- [x] 创建 `vendor/master-branch/` 目录 ✅
- [x] 解压 master zip 到 `vendor/master-branch/` ✅
- [x] 创建 `vendor/master-branch/README.md`（cherry-pick 状态列表）✅
- [x] 确认 vendor/ 被 git 追踪（不在 .gitignore 中）✅
- [x] **后续：** `vendor/` 目录已删除（2026-04-19）— master 通过单独 remote 访问

**状态：** ✅ COMPLETE

### SM-T02：UTC 时间戳 🍒（来自 master/storage.py）
- [x] `storage.py`：`timestamp_slug()` 使用 `datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")`
- [x] 保留 `atomic_write_json()`（Main 独有）
- [x] `docs/architecture/run_directory_structure.md`：补充新时间戳格式说明
- [x] CI unit test 通过（test_storage.py）

**状态：** ✅ COMPLETE — Main 已实现此功能

### SM-T03：Workflow 中断处理 🍒（来自 master/workflow_session.py）
- [x] `workflow_session.py`：`run_workflow()` 返回类型改为 `| None`
- [x] maker/checker 步骤加入 `try/except KeyboardInterrupt` + `provider.shutdown()`
- [x] 加入 `[workflow] Step N/4:` 进度输出
- [x] `pipelines.py`：`run_maker_pipeline` 和 `run_checker_pipeline` 加入 `provider_out: list | None = None`
- [x] `cli.py`：处理 `run_workflow()` 返回 `None` 的情况

**状态：** ✅ COMPLETE — Main 已实现此功能（比 master 更完整）

### SM-T04：重试配置 🍒（来自 master/config.py）（可选）
- [x] `config.py` 的 `RoleDefaults`：已含 `max_retries: int = 3`
- [x] `config.py` 的 `RoleDefaults`：已含 `retry_backoff_seconds: float = 2.0`
- [x] `providers.py` 使用这两个字段实现 retry loop

**状态：** 🧊 Frozen（标记为可选；功能已在 main 中实现）

### SM-T05：合并文档归档
- [x] `docs/archives/20260419_master_merge_strategy.md` 存在（已从 `docs/` 移至 archives）✅
- [x] `vendor/master-branch/README.md` 更新完成状态 ✅（vendor/ 已删除）

**状态：** ✅ COMPLETE

---

## Master 中识别的缺失模块（纳入 Stage 2）

| 模块 | Master 状态 | Main 状态 | 计划 |
|------|------------|---------|------|
| `src/lme_testing/audit_trail.py` | 引用但不存在（broken import）| ✅ 已实现并集成入 `review_session.py` | S2-B1 ✅ |
| `src/lme_testing/case_compare.py` | 引用但不存在（broken import）| ✅ 已实现并集成入 `review_session.py` | S2-B2 ✅ |

---

## Stage 1 — 真实数据接入（Stage M 完成后）

### S1-T01：Schema Signal 数据源修复
- [x] `validate_schemas.py --output-json` 参数
- [x] CI schema-validation job 写入 `runs/schema_validation_latest.json`
- [x] `_compute_schema_signals()` 读取真实文件
- [x] `schema_signal_source: "real_validation"` 字段
- [x] 验证：invalid fixture → `schema_failure_rate > 0`

**状态：** ✅ COMPLETE
**证据：** `runs/schema_validation_latest.json` 存在（370 fixtures，0 failures）；`compute_governance_signals()` → `schema_signal_source: "real_validation"`；`test_schema_failure_rate_detects_invalid_fixtures` 测试通过

### S1-T02：全量运行数据路径对齐
- [x] 手动定位全量 183 条规则的实际运行输出目录
- [x] 创建/更新 `docs/architecture/run_directory_structure.md`（含新旧时间戳格式区分）
- [x] `compute_governance_signals()` 扫描路径修复
- [x] 新增 `--runs-dir` 参数
- [x] 验证：`runs_analyzed > 0`，`total_rules ≥ 180`

**状态：** ✅ COMPLETE
**证据：** `docs/architecture/run_directory_structure.md` 存在；`compute_governance_signals()` → `runs_analyzed=21`，`total_rules=180`；coverage=72.78%；`--runs-dir` 参数在 CI ci.yml 中使用

### S1-T03：Session Snapshot 原子写入确认
- [x] 确认 `review_session.py` 中所有 snapshot 写入使用 `atomic_write_json()`
  - `/api/reviews/save` 路径 ✅
  - `/api/bdd/save` 路径 ✅
  - `/api/scripts/save` 路径 ✅
- [x] `docs/architecture/architecture.md` 声明单用户设计约束

**状态：** ✅ COMPLETE
**证据：** `review_session.py` lines 151-232-354 全部使用 `atomic_write_json`；`docs/architecture/architecture.md` 第 10、20、254 行明确单用户设计

### S1-T03b：Checker 真实稳定性测量
- [x] poc_two_rules 双次真实 MiniMax API checker 运行 ⚠️（API 可靠性问题导致 0 valid data）
- [x] Full rules v3 真实 API checker stability 测量
- [x] `runs/checker-stability/20260418T231915+0800-v3/stability_report.json`（含 `data_source: "real_api"`）
- [x] `docs/governance/acceptance.md` Phase 1 Gate 6 更新为真实数字（instability_rate = 9.5%）
- [x] 若 instability > 5%：`docs/governance/model_governance.md` 分析记录

**实测值：** instability_rate = 9.5%（6/63 comparable cases，v3 measurement）
**状态：** ✅ COMPLETE — Gate 6 已更新；v3 stability data 超出 5% threshold 已记录；poc_two_rules 特定测量因 API 可靠性问题未能获得有效数据

### S1-T04：全量规则质量基准
- [x] 全量 183 条规则 maker 运行（分批 `--batch-size 8`）
- [x] 全量 checker 运行
- [x] `reports/baseline_full_<date>.html`
- [x] 人工随机抽查 ≥ 10 条规则
- [x] `docs/releases/BASELINE-183-RULES.md`
- [x] `coverage_signals.total_rules ≥ 180`

**当前 coverage（全量）：** 72.78%（131/180 fully covered）
**状态：** ✅ COMPLETE
**证据：** maker: `runs/maker_v1.1_full/20260419T090524+0800/`；checker: `runs/checker_v1.1_full/20260419T092854+0800/`；HTML: `reports/baseline_full_20260418.html`；doc: `docs/releases/BASELINE-183-RULES.md`（12条人工抽查）；total_rules=180

### S1-T05：项目状态声明重写
- [x] README Project Status 用真实数字重写（含 Stage M 合并状态）
- [x] 消除所有无数据支撑的"100%"和"Complete"声明
- [x] `docs/governance/acceptance.md` 每个 gate 有 Verification Type

**状态：** ✅ COMPLETE
**证据：** acceptance.md v2.0 每个 gate 有 Verification Type；README.md Verification Status 表格已更新；无"All Phases Complete"表述

---

## Stage 0（历史存档）— 框架实现

所有 Phase 1-3 代码实现完成（2026-04-13/14）。状态同 v2.0 TODO，不重复列举。

**关键差异（相较 v2.0 增加的说明）：**

| 模块 | Main 状态 | Master 状态 | 说明 |
|------|---------|----------|------|
| `review_session.py` | ✅ Code（BDD tabs，1251行）| 部分实现（824行，broken imports）| Main 更完整 |
| `providers.py` | ✅ Code（StubProvider，442行）| 旧版（135行，编码损坏）| Main 更完整 |
| `pipelines.py` | ✅ Code（planner+BDD，910行）| 旧版（639行，无 planner/BDD）| Main 更完整 |
| `workflow_session.py` | ✅ Code（无中断处理）| 有中断处理（更好）| 通过 SM-T03 合并 |
| `storage.py` | ✅ Code（本地时间）| UTC 时间（更好）| 通过 SM-T02 合并 |
| `audit_trail.py` | 不存在 | ✅ 已实现并集成 | S2-B1 ✅ |
| `case_compare.py` | 不存在 | ✅ 已实现并集成 | S2-B2 ✅ |

---

## Stage 2 — 质量提升、审计补全、Mock 执行桥接

**当前状态（2026-04-27）：**
- ✅ S2-T01 已完成：v1.5 maker + checker 覆盖率 78.89%（142/180 fully covered），当前证据基础下的 prompt 校准实际天花板。
- ✅ S2-B1/B2 已完成：`audit_trail.py` 与 `case_compare.py` 已实现并集成。
- ✅ S2-C1 已完成：基于 `docs/materials/LME_Matching_Rules_Aug_2022.md` 的 mock API execution bridge 已交付，用于验证 BDD/script 可以真实调用 API under test。
- ✅ S2-C2 已完成：Initial Margin HKv13 mock API execution bridge 已交付，作为 Initial Margin preservation baseline。
- ✅ S2-C3 已完成：HKv14 governed intake、HKv13→HKv14 deterministic diff evidence、POC decision note、modular HKv14 mock wrapper 已交付。
- ✅ S2-C4 已完成：HKv14 promoted downstream treatment mapping 已完成，HKv14 flat-rate validation data 已对齐三项公式。
- ✅ S2-C5 已完成：mock API deliverables location policy 已记录，当前 Stage 2 bridge sources and zips 保持在 `deliverables/`。
- ✅ S2-D1 已完成：browser-level review UI E2E 覆盖 Review -> BDD -> Scripts 主路径、BDD 未保存 edits 保留、可见 match metrics 刷新。
- ✅ S2-F1 已完成：HKv13→HKv14 role-friendly impact decision review package generator；canonical JSON + derived Markdown + local review HTML。
- ✅ S2-F2 已完成：MVP document readiness registry generator；canonical JSON + derived summary under `evidence/mvp_document_readiness/20260429T075702Z/`。
- ✅ S2-F3 已完成：MVP input document contract and optional-input readiness validation。
- ✅ S2-F4 已完成：CodeFreddy rule extraction review workflow integrated on `main`; `rule-workflow-session` GUI smoke-reviewed with HKv14; config fallback and pypdf PDF extraction fixes committed.
- ⏳ Stage 3 仍阻塞于真实 LME VM/API 权限；mock API 不代表真实 LME execution readiness。

### S2-B1：audit_trail.py 实现（来自 master 概念）
- [x] `src/lme_testing/audit_trail.py`：`build_audit_trail(session_dir, output_path)` 实现
- [x] HTML output shows maker → checker → human decision chain per rule
- [x] Works with existing `review_session.py` without modification

**状态：** ✅ COMPLETE
**证据：** `src/lme_testing/audit_trail.py` 完整实现（267行），`build_audit_trail(session_dir, output_path) -> dict`；`review_session.py` 的 `finalize_session()` 已集成调用，输出到 `final/audit_trail.html`；生成失败不影响 session（graceful degradation）

### S2-B2：case_compare.py 实现（来自 master 概念）
- [x] `src/lme_testing/case_compare.py`：`build_case_compare(...)` 实现
- [x] HTML output highlights differences between two iterations
- [x] Works with existing `review_session.py` without modification

**状态：** ✅ COMPLETE
**证据：** `src/lme_testing/case_compare.py` 完整实现（216行），`build_case_compare(...)`；`review_session.py` 的 `_run_job()` 已集成调用，输出到 `iter<N>/rewrite/case_compare.html`；生成失败不影响 session（graceful degradation）

### S2-A 系列：质量提升（取决于 Stage 1 数据）

| 任务 | 状态 | 说明 |
|------|------|------|
| S2-T01: API 可靠性修复 | ✅ COMPLETE | requests session pooling + 异常类型检测 |
| S2-T01: 全量 180-rule maker+checker 运行 | ✅ COMPLETE | 322 cases, 0 failures, 72.22% coverage |
| S2-T01: 覆盖率分析 | ✅ COMPLETE | 见 `docs/planning/s2t01_coverage_analysis.md` |
| S2-T01: checker prompt v1.1 校准 | ✅ COMPLETE | 4 类 case type coverage_relevance 修复 |
| S2-T01: SR-MR-064-A-1 coverage_eligible=false | ✅ COMPLETE | 源文档页19截断，无法修复 |
| S2-T01: v1.5 重新运行验证覆盖率提升 | ✅ COMPLETE | 78.89%（142/180 fully covered），见 `docs/planning/s2t01_coverage_analysis.md` |
| Maker prompt 调优 | ✅ COMPLETE | v1.5 后剩余 gap 为证据约束或 LLM 非决定性 |
| Oracle 实测验证 | ⏳ PENDING | 触发条件未满足 |

**S2-T01 最终实测结果（2026-04-21）：**
- 180 rules → 322 scenarios → 322 reviews, 0 failures
- Coverage: 78.89%（142 fully, 5 partial, 1 uncovered）
- Net: +12 fully covered rules from baseline（130→142），+6.67 percentage points（72.22%→78.89%）
- 剩余 gap：SR-MR-060-B-1、SR-MR-004-01、SR-MR-071-A-1 为证据约束；SR-MR-015-B3-4、SR-MR-071-C-1 为 LLM 非决定性/边界波动。

**状态：** ✅ COMPLETE — prompt 校准达到当前证据基础下实际天花板；后续不继续靠 prompt 追求 80%。

### S2-C1：Mock API Execution Bridge
- [x] 基于 `docs/materials/LME_Matching_Rules_Aug_2022.md` 设计 mock API 服务
- [x] 提供可运行 HTTP API：`deliverables/lme_mock_api/mock_lme_api/server.py`
- [x] 将 BDD step scripts 更新为可通过 HTTP 调用 mock API：`deliverables/lme_mock_api/features/step_definitions/matching_rules_steps.py`
- [x] 提供样例 feature：`deliverables/lme_mock_api/features/matching_rules/core_matching_rules.feature`
- [x] 提供 lightweight BDD runner：`deliverables/lme_mock_api/run_bdd.py`
- [x] 提供压缩包：`deliverables/lme_mock_api.zip`
- [x] 文档化验证计划：`docs/planning/mock_api_validation_plan.md`

**验证：**
- `python -m unittest tests.test_mock_api` 在 `deliverables/lme_mock_api` 中通过（2 tests OK）
- `python run_bdd.py` 在 mock API 启动后通过（33 passed, 0 failed）

**边界：** 这是 Stage 3 前置的 mock execution bridge，只证明 BDD/script 可以调用一个确定性 API under test；不代表真实 LME API 接入完成。

---

### S2-C2：Initial Margin HKv13 Mock API Execution Bridge
- [x] 基于 `docs/materials/Initial Margin Calculation Guide HKv13.pdf` 和 `artifacts/im_hk_v13/` 创建 Initial Margin mock API
- [x] 提供可运行源码：`deliverables/im_hk_v13_mock_api/`
- [x] 提供压缩包：`deliverables/im_hk_v13_mock_api.zip`
- [x] 文档化验证计划：`docs/planning/im_hk_v13_mock_api_validation_plan.md`
- [x] 覆盖 Section 3.2.4.2 Flat Rate Margin POC，expected margin `15,180,000`

**验证：**
- `.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v13_mock_api\tests -t deliverables\im_hk_v13_mock_api -v` 通过（4 tests OK；BDD summary 37 passed, 0 failed）

**边界：** HKv13 是 Initial Margin mock/stub preservation baseline，不代表真实 VaR Platform、HKSCC/HKEX execution readiness。

---

### S2-C3：Initial Margin HKv14 POC Document Workflow And Modular Mock API Bridge
- [x] 使用 `pypdf` 从 `docs/materials/Initial Margin Calculation Guide HKv14.pdf` 生成 governed intake：`artifacts/im_hk_v14/`
- [x] 生成 HKv13→HKv14 deterministic diff evidence：`evidence/im_hk_v14_diff/`
- [x] 生成 diff report：`docs/planning/im_hk_v14_diff_report.md`
- [x] 记录 POC downstream decision：`docs/planning/im_hk_v14_downstream_decision.md`
- [x] 抽取 shared implementation：`deliverables/im_hk_mock_api_common/`
- [x] 创建 HKv14 thin wrapper：`deliverables/im_hk_v14_mock_api/`
- [x] 提供压缩包：`deliverables/im_hk_v14_mock_api.zip`

**验证：**
- HKv14 extraction: 38 pages, 10 clauses, 164 atomic rules, 164 semantic rules
- HKv13→HKv14 diff: 10 changed candidates, 0 added, 0 removed, 1 ID drift candidate, 0 source-anchor warnings
- HKv14 wrapper tests and BDD runner passed

**边界：** S2-C3 是 POC/mock/stub bridge work；不声明 HKv14 production downstream automation readiness。

---

### S2-C4：Initial Margin HKv14 Promoted Downstream Slice
- [x] 记录 human-approved promotion scope：`docs/planning/im_hk_v14_promotion_scope.md`
- [x] 将 10 changed candidates 和 1 ID drift candidate 映射到 downstream treatment categories：`docs/planning/im_hk_v14_downstream_treatment_mapping.md`
- [x] 将 HKv14 flat-rate validation data 对齐为三项公式：`(60,000,000 x 12% + 750,000 x 30% + 300,000 x 55%) x 2 = 15,180,000`
- [x] 刷新 HKv14 wrapper tests、BDD label 和 zip package

**验证：**
- `.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v14_mock_api\tests -t deliverables\im_hk_v14_mock_api -v` 通过（3 tests OK；BDD summary 37 passed, 0 failed）
- `.venv\Scripts\python.exe deliverables\im_hk_v14_mock_api\poc_flat_rate_margin.py` 通过
- HKv13 side-by-side validation passed

**边界：** promoted downstream slice 是 mock/stub baseline candidate；不替代 Stage 3 real execution environment。

---

### S2-C5：Mock API Deliverables Location Policy
- [x] 选择当前 Stage 2 policy：mock API bridge source folders and packaged zips stay under `deliverables/`
- [x] 记录 policy：`docs/planning/mock_api_deliverables_policy.md`
- [x] 明确 no directory move authorized
- [x] 明确 revisit trigger: before adding a new mock API bridge or turning the bridges into maintained tools

**状态：** ✅ COMPLETE

---

### S2-D1：Browser-Level Review UI E2E
- [x] 启动真实 local review-session HTTP server
- [x] 使用 deterministic fixture artifacts，不调用 live LLM provider
- [x] 用 Chrome DevTools Protocol 驱动 installed Chrome/Edge
- [x] 覆盖 Review -> BDD -> Scripts tab navigation
- [x] 验证 BDD textarea 未保存内容在 tab navigation 后不丢失
- [x] 验证 Save BDD Edits 后 Scripts match metrics 刷新
- [x] 验证 Save Scripts Edits 后 visible exact/unmatched metrics 更新
- [x] 无 browser 时自动 skip

**状态：** ✅ COMPLETE
**证据：** `tests/test_review_session_browser.py`；`docs/planning/ui_test_plan.md`；`.venv\Scripts\python.exe -m unittest tests.test_review_session_browser -v` 通过（1 browser test）；`.venv\Scripts\python.exe -m unittest discover -v tests` 通过（181 tests）

**边界：** 当前 browser E2E 覆盖 BDD/Scripts 主路径，不覆盖 submit/finalize browser flow。

---

### S2-F1：HKv14 Role-Friendly Impact Decision Review
- [x] 将 `Executable_Engineering_Knowledge_Contract.md` 的 MVP human-control slice 提升为小范围 governed plan
- [x] 记录 plan：`docs/planning/im_hk_v14_role_review_plan.md`
- [x] 实现 local single-user review surface: generated `review.html`
- [x] 输出 canonical `decision_record.json`
- [x] 输出 derived `decision_summary.md`
- [x] 加 focused validation/tests: load, save, validation failure, Markdown export
- [x] 运行 docs/artifact governance checks

**状态：** ✅ COMPLETE

**边界：** 不新增 LLM stage，不改变 schemas/prompts/default models，不实现 generic document platform，不声明 Stage 3 readiness；HKv13 mock API deliverable remains preservation baseline。

---

### S2-F2：MVP Document Readiness Registry
- [x] 将 `Executable_Engineering_Knowledge_Contract.md` 的 MVP document registration/readiness slice 提升为小范围 governed plan
- [x] 记录 plan：`docs/planning/mvp_document_readiness_plan.md`
- [x] 实现 deterministic document readiness registry generator
- [x] 输出 `document_readiness.json`
- [x] 输出 derived `document_readiness_summary.md`
- [x] 加 focused validation/tests: valid registry, missing source, placeholder handling, validation failure
- [x] 运行 docs/artifact governance checks

**状态：** ✅ COMPLETE — deterministic registry generator, CLI command, tests, and evidence package implemented. Overall readiness remains `blocked` because Test Plan and Regression Pack Index are explicit placeholders.

**边界：** 不新增 LLM stage，不实现 generic document upload/platform，不做 requirement-to-test/regression mapping，不声明 Stage 3 readiness。

---

### S2-F3：MVP Input Document Contract
- [x] 定义 Test Plan minimum input contract
- [x] 定义 Regression Pack Index minimum input contract
- [x] 明确 readiness/blocking rules
- [x] 明确 future implementation boundaries
- [x] 运行 docs governance check
- [x] `mvp-document-readiness` 支持 optional `--test-plan`
- [x] `mvp-document-readiness` 支持 optional `--regression-pack-index`
- [x] placeholder fallback preserved when real files are omitted
- [x] focused tests cover valid real inputs, missing source failure, incomplete content blocking, placeholder fallback

**状态：** ✅ COMPLETE — deterministic optional-input readiness validation implemented. Default readiness remains `blocked` until real Test Plan and Regression Pack Index files are provided.

**边界：** 不创建真实 Test Plan 或 Regression Pack Index，不新增 LLM stage，不实现 generic document upload/platform，不做 requirement-to-test/regression impact mapping，不声明 Stage 3 readiness。

---

### S2-F4：Rule Extraction Review Workflow GUI
- [x] 受控纳入 `CodeFreddy/LME-Testing` `feature/rule-extraction-review` at `b1287a2` 的 deterministic document intake + rule artifact review GUI slice。
- [x] 保留 newer local HKv14/MVP readiness work；未直接覆盖 `main`。
- [x] 暴露 CLI：`python main.py rule-workflow-session --port 8765`。
- [x] 支持 source upload/import、deterministic extraction、atomic/semantic rule review、review history snapshots、reviewed artifact saving。
- [x] 支持 optional case generation entry point and scenario review handoff under stub/LLM-configured execution.
- [x] Follow-up fix: missing `config/llm_profiles.json` now falls back to `config/llm_profiles.stub.json` for `rule-workflow-session`.
- [x] Follow-up fix: rule workflow PDF extraction uses `pypdf` first and falls back to `pdftotext`.
- [x] HKv14 GUI smoke path completed: PDF extract -> Rule Extraction Review -> Generate Cases -> `checker_readable.html` first look accepted by human.
- [x] Pushed to `origin/main`; `CodeFreddy/LME-Testing` `feature/rule-extraction-review` was updated to the same `main` commit.

**验证：**
- `python -m unittest tests.test_rule_extraction_review -v` 通过（11 tests OK）。
- `python scripts/check_docs_governance.py` 通过。
- `python scripts/check_artifact_governance.py` 通过。
- HKv14 PDF direct extraction via rule workflow extractor found 5 target sections.

**边界：** 不接受 CodeFreddy broader prompt/schema/review-decision/concurrency contract changes；不移除 `reject` 或 `block_recommendation_review`；不声明 Stage 3 或 HKv14 production execution readiness。

---

## Stage 3（阻塞于外部）

- ⏳ LME VM 访问权限（ETA：未知）
- ⏳ 真实 LME API 替换模拟实现
- ⏳ Step library 重建（真实 API 模式）
- ⏳ Step binding rate 重新测量

---

## Darcy 个人任务（更新）

- [x] ✅ Code　Ruby Cucumber prototype 创建（已归档，由 Python step_registry 替代）
- [x] ✅ Code　BDD tab：显示 normalized BDD，支持 Given/When/Then 编辑
- [x] ✅ Code　Scripts tab：步骤可见性显示
- [x] ✅ SM-T03　workflow_session.py 中断处理（cherry-pick from master）
- [x] ✅ S1-T02　定位全量运行数据目录
- [x] ✅ S1-T04　全量基准运行（72.78%，已文档化）
- [x] ✅ S2-B1　audit_trail.py 实现
- [x] ✅ S2-C1　mock API execution bridge 创建并打包
- [x] ✅ S2-C2　Initial Margin HKv13 mock API bridge
- [x] ✅ S2-C3　Initial Margin HKv14 POC modular mock bridge
- [x] ✅ S2-C4　HKv14 promoted downstream treatment mapping
- [x] ✅ S2-C5　mock API deliverables location policy
- [x] ✅ S2-D1　browser-level review UI E2E
- [x] ✅ S2-F1　HKv14 role-friendly impact decision review package generator
- [x] ✅ S2-F2　MVP document readiness registry
- [x] ✅ S2-F3　MVP input document contract and optional-input readiness validation
- [x] ✅ S2-F4　CodeFreddy rule extraction review GUI integration and HKv14 smoke review
- [ ] ⏳ 真实 LME API 接入（Stage 3，待 VM 权限）
- [ ] 🧊 S2-E　LLM 非决定性稳定化（SR-MR-015-B3-4、SR-MR-071-C-1；已明确暂跳过，未来需 benchmark 成本/收益批准）
