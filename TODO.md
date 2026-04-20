# LME Testing — TODO v3.0

**修订日期：** 2026-04-19  
**说明：** 整合 master 分支合并分析，新增 Stage M 任务。

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
- [x] `docs/run_directory_structure.md`：补充新时间戳格式说明
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
- [x] `docs/archives/MERGE_STRATEGY.md` 存在（已从 `docs/` 移至 archives）✅
- [x] `vendor/master-branch/README.md` 更新完成状态 ✅（vendor/ 已删除）

**状态：** ✅ COMPLETE

---

## Master 中识别的缺失模块（纳入 Stage 2）

| 模块 | Master 状态 | Main 状态 | 计划 |
|------|------------|---------|------|
| `lme_testing/audit_trail.py` | 引用但不存在（broken import）| 不存在 | S2-B1 |
| `lme_testing/case_compare.py` | 引用但不存在（broken import）| 不存在 | S2-B2 |

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
- [x] 创建/更新 `docs/run_directory_structure.md`（含新旧时间戳格式区分）
- [x] `compute_governance_signals()` 扫描路径修复
- [x] 新增 `--runs-dir` 参数
- [x] 验证：`runs_analyzed > 0`，`total_rules ≥ 180`

**状态：** ✅ COMPLETE  
**证据：** `docs/run_directory_structure.md` 存在；`compute_governance_signals()` → `runs_analyzed=21`，`total_rules=180`；coverage=72.78%；`--runs-dir` 参数在 CI ci.yml 中使用

### S1-T03：Session Snapshot 原子写入确认
- [x] 确认 `review_session.py` 中所有 snapshot 写入使用 `atomic_write_json()`
  - `/api/reviews/save` 路径 ✅
  - `/api/bdd/save` 路径 ✅
  - `/api/scripts/save` 路径 ✅
- [x] `docs/architecture.md` 声明单用户设计约束

**状态：** ✅ COMPLETE  
**证据：** `review_session.py` lines 151-232-354 全部使用 `atomic_write_json`；`docs/architecture.md` 第 10、20、254 行明确单用户设计

### S1-T03b：Checker 真实稳定性测量
- [x] poc_two_rules 双次真实 MiniMax API checker 运行 ⚠️（API 可靠性问题导致 0 valid data）
- [x] Full rules v3 真实 API checker stability 测量
- [x] `runs/checker-stability/20260418T231915+0800-v3/stability_report.json`（含 `data_source: "real_api"`）
- [x] `docs/acceptance.md` Phase 1 Gate 6 更新为真实数字（instability_rate = 9.5%）
- [x] 若 instability > 5%：`docs/model_governance.md` 分析记录

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
- [x] `docs/acceptance.md` 每个 gate 有 Verification Type

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
| `audit_trail.py` | 不存在 | 引用但不存在（broken）| S2-B1 实现 |
| `case_compare.py` | 不存在 | 引用但不存在（broken）| S2-B2 实现 |

---

## Stage 2（冻结，待 Stage 1 数据）

### S2-B1：audit_trail.py 实现（来自 master 概念）
- [x] `lme_testing/audit_trail.py`：`build_audit_trail(session_dir, output_path)` 实现
- [x] HTML output shows maker → checker → human decision chain per rule
- [x] Works with existing `review_session.py` without modification

**状态：** ✅ COMPLETE  
**证据：** `lme_testing/audit_trail.py` 完整实现（267行），`build_audit_trail(session_dir, output_path) -> dict` 可用；在 `test_fresh` session 上验证：生成 16KB HTML，包含完整 decision chain；main 的 `review_session.py` 不引用此模块（可选功能）

### S2-B2：case_compare.py 实现（来自 master 概念）
- [x] `lme_testing/case_compare.py`：`build_case_compare(...)` 实现
- [x] HTML output highlights differences between two iterations
- [x] Works with existing `review_session.py` without modification

**状态：** ✅ COMPLETE  
**证据：** `lme_testing/case_compare.py` 完整实现（216行）；`build_case_compare(prev, next, rewritten, iter_prev, iter_next, output)` 在 `test_fresh` session 上验证：生成 4.4KB HTML；main 的 `review_session.py` 不引用此模块（可选功能）

### S2-A 系列：质量提升（取决于 Stage 1 数据）

| 任务 | 状态 | 说明 |
|------|------|------|
| S2-T01: API 可靠性修复 | ✅ COMPLETE | requests session pooling + 异常类型检测 |
| S2-T01: 全量 180-rule maker+checker 运行 | ✅ COMPLETE | 322 cases, 0 failures, 72.22% coverage |
| S2-T01: 覆盖率分析 | ✅ COMPLETE | 见 `docs/s2t01_coverage_analysis.md` |
| S2-T01: checker prompt v1.1 校准 | ✅ COMPLETE | 4 类 case type coverage_relevance 修复 |
| S2-T01: SR-MR-064-A-1 coverage_eligible=false | ✅ COMPLETE | 源文档页19截断，无法修复 |
| S2-T01: 重新运行验证覆盖率提升 | ⏳ PENDING | 预计 coverage 72.22% → ~82% |
| Maker prompt 调优 | ⏳ PENDING | 可选，coverage 提升后评估 |
| Oracle 实测验证 | ⏳ PENDING | 触发条件未满足 |

**S2-T01 实测结果（2026-04-20）：**
- 180 rules → 322 scenarios → 322 reviews, 0 failures
- Coverage: 72.22% (130 fully, 17 partial, 1 uncovered)
- Partial root causes: 12 rules by checker strictness, 4 rules by maker skipping case types, 1 rule by source truncation
- 根因修复后预计: ~82% coverage

**状态：** ✅ Phase 1 complete — API reliability fixed, full run complete, root causes identified and fixed

---

## Stage 3（阻塞于外部）

- ⏳ LME VM 访问权限（ETA：未知）
- ⏳ 真实 LME API 替换模拟实现
- ⏳ Step library 重建（真实 API 模式）
- ⏳ Step binding rate 重新测量

---

## Darcy 个人任务（更新）

- [x] ✅ Code　Ruby Cucumber prototype 创建
- [x] ✅ Code　BDD tab：显示 normalized BDD，支持 Given/When/Then 编辑
- [x] ✅ Code　Scripts tab：步骤可见性显示
- [x] ✅ SM-T03　workflow_session.py 中断处理（cherry-pick from master）
- [x] ✅ S1-T02　定位全量运行数据目录
- [x] ✅ S1-T04　全量基准运行（72.78%，已文档化）
- [x] ✅ S2-B1　audit_trail.py 实现
- [ ] ⏳ 真实 LME API 接入（Stage 3，待 VM 权限）
- [ ] S2-A　Maker prompt v1.2 全量重跑（benchmark validated，需 API 预算）
