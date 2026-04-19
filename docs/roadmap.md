# LME Testing — Roadmap v3.0

**修订日期：** 2026-04-19  
**变更说明：** 在 v2.0 基础上，整合 master 分支合并分析结果，更新团队协作背景。

---

## 项目真实状态（合并后）

| 维度 | 状态 |
|------|------|
| 代码框架（Main） | ✅ 完整：maker/checker/BDD/oracle/governance |
| Master 分支合并 | 🔄 待执行（vendor/ 存档 + 4 项 cherry-pick） |
| Master 特有功能（audit_trail/case_compare） | 📋 已识别，纳入 Stage 2 |
| Governance signals 数据 | ⚠️ 2/4 信号数据为空或 stub（待 Stage 1 修复）|
| 全量 183 条规则质量基准 | 🔄 数据存在但 governance 无法读取 |
| Checker 真实稳定性 | ⚠️ 71% (14 cases, v1) → 60% (10 cases, v4)，远高于 10% 阈值；API 随机断开导致无法完成全量 322-case 测量 | S2-T02 待定（S2-T01 blocked）|
| 真实 LME API 接入 | ⏳ ETA 未知（需内部 VM 权限）|

---

## 核心原则（延续 v2.0）

1. **Artifacts are first-class contracts**
2. **Upstream quality first**
3. **Deterministic before LLM**
4. **Human review is a control layer**
5. **Durable context is repo-readable**
6. **Real data before governance claims**
7. **Honest capability boundary**
8. **新增：Merge by understanding, not by overwriting** — 多人协作时，分支合并基于逐文件分析，不盲目覆盖

---

## Stage 0 — 框架完成（存档）

**日期：** 2026-04-13/14  
**说明：** AI 代理 48 小时实现全框架，代码层面完整，验证深度为 2 条规则 POC。  
**存档，不再重新进入此阶段。**

---

## Stage M — Master 分支合并（新增，当前优先）

**时间预估：** 1-3 天  
**前置条件：** 无  
**目标：** 将同事 master 分支的有效改进合并进 main，同时保留 main 的完整 BDD 和 governance 体系

### Gate M.1 — 存档 Master 代码

- 创建 `vendor/master-branch/` 目录
- 将 master zip 解压到此目录
- 创建 `vendor/master-branch/README.md`（说明用途和 cherry-pick 状态）

**验收：** `vendor/master-branch/lme_testing/` 存在，不影响主路径 import

### Gate M.2 — Cherry-pick P1：UTC 时间戳

- `storage.py`：`timestamp_slug()` 改为 `datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")`
- 保留 `atomic_write_json()`（Main 独有，Master 没有）
- 更新 `docs/run_directory_structure.md`：说明新时间戳格式（末尾有 `Z`）

**验收：** `python -c "from lme_testing.storage import timestamp_slug; print(timestamp_slug())"` 输出包含 `Z`

### Gate M.3 — Cherry-pick P2：Workflow 中断处理

- `workflow_session.py`：maker 和 checker 步骤加入 `try/except KeyboardInterrupt`
- `workflow_session.py`：加入 `[workflow] Step N/4:` 进度输出
- `pipelines.py`：`run_maker_pipeline` 和 `run_checker_pipeline` 加入 `provider_out: list | None = None` 参数（保持向后兼容）

**验收：** 在 workflow 运行中按 Ctrl+C，有明确提示信息且不留残留进程

### Gate M.4 — Cherry-pick P3：重试配置（可选）

- `config.py` 的 `RoleDefaults`：重新加入 `max_retries: int = 3` 和 `retry_backoff_seconds: float = 2.0`
- `providers.py`：确认 MiniMax provider 使用这两个字段（Main 的 StubProvider 忽略即可）

**验收：** `config.load_project_config()` 后 `config.maker_defaults.max_retries == 3`

### Gate M.5 — 规划 Master 缺失模块为 Stage 2 任务

- `audit_trail.py` 需求文档化：生成审计 HTML，记录 maker→checker→human 决策链
- `case_compare.py` 需求文档化：同一 rule 多次迭代的 case 对比视图
- 在 `TODO.md` 中创建对应 Stage 2 任务条目

**验收：** `docs/stage2_planned_modules.md` 中有两个模块的需求描述

### Stage M Exit

- [ ] vendor/master-branch/ 存在且有 README
- [ ] CI smoke test 在 cherry-pick 后通过
- [ ] `MERGE_STRATEGY.md` 中所有项目标注完成状态

---

## Stage 1 — 真实数据接入与可信基准建立

**时间预估：** 2-4 周（Stage M 完成后开始）  
**目标：** 让 governance 消费真实数据，建立全量质量基准

### Gate 1.1 — Schema Signal 数据源修复

- `validate_schemas.py --output-json` 持久化验证结果
- `_compute_schema_signals()` 读取真实验证文件
- `schema_failure_rate` 不再是空值

**验收：** 故意引入 invalid fixture 时 `schema_failure_rate > 0`

### Gate 1.2 — 全量运行数据路径对齐

- 定位全量 183 条规则的实际运行输出目录
- 创建 `docs/run_directory_structure.md`
- `governance_signals.json` 中 `runs_analyzed > 0`，`total_rules ≥ 180`

### Gate 1.3 — Checker 真实稳定性测量

- 用真实 MiniMax API 对 poc_two_rules 双次运行 checker
- 产出 `stability_report.json`（含 `data_source: "real_api"`）
- 更新 `docs/acceptance.md` Phase 1 Gate 6

**当前 instability_rate：** TBD

### Gate 1.4 — 全量规则质量基准

- 全量 183 条规则 maker + checker 运行（分批，`--batch-size 8`）
- `docs/releases/BASELINE-183-RULES.md`（含人工抽查 ≥10 条）
- Coverage 数字如实记录

### Gate 1.5 — 项目状态声明重写

- README 消除"All Phases Complete"
- 所有 governance 数字有真实数据来源
- `docs/acceptance.md` 每个 gate 有 Verification Type

**Stage 1 Exit：** 所有 gate 完成，governance signals 有真实数据支撑

---

## Stage 2 — 规模化质量提升 + 功能补全

**前置：** Stage 1 完成  
**时间预估：** 4-8 周（取决于 Stage 1 发现）

### 方向 A：基于真实数据的质量提升

根据 Stage 1 的真实 coverage 数字决定：

- 若 coverage < 80%：Maker prompt 调优
- 若 instability > 10%：Checker prompt 稳定性改进
- 识别出的高频确定性规则类型 → Oracle 实测验证

### 方向 B：Master 缺失模块实现（新增）

**B.1 — `lme_testing/audit_trail.py`**

实现 master 分支计划但未完成的审计跟踪功能：
- 输入：session_dir（含所有迭代的 maker/checker/review 数据）
- 输出：`audit_trail.html`（时间线视图：每条 rule 的 maker 输出 → checker 判断 → human 决策）
- `/api/audit_trail` GET 端点在 review_session.py 中已有路由占位，实现后直接生效

**B.2 — `lme_testing/case_compare.py`**

实现 master 分支计划但未完成的 case 对比功能：
- 输入：session_dir 的多个迭代（iteration N 和 N-1 的 maker 输出）
- 输出：`case_compare.html`（并排对比视图，高亮 rewrite 后的变化）
- 在 review_session.py 的 `/api/submit` 后触发

**注：** 这两个功能在 master 的 `review_session.py` 中有调用点和 UI 代码，但依赖的模块从未实现。Main 无需修改 review_session.py，只需创建这两个模块即可激活。

### 方向 C：步骤可见性提升（取决于外部条件）

若 LME VM 访问权限仍未获得，不进行此方向。

---

## Stage 3 — 真实执行环境接入

**前置：** Stage 2 完成 + 获得 LME 内部 VM 访问权限  
**当前 ETA：** 未知

核心工作：
- 用真实 LME API 替换 `samples/ruby_cucumber/lib/lme_*.rb` 模拟实现
- 重建 `lme_testing/step_library.py`（基于真实 API 模式）
- 重新测量 step binding rate（当前 35.4% 基于模拟）
- 在真实环境执行 BDD 场景

---

## 永久冻结

| 项目 | 原因 |
|------|------|
| BDD style learning | 无真实 BDD 样本，自循环优化无意义 |
| Multi-user hosted portal | 超出当前工具定位 |
| Autonomous execution without approval gates | 违反架构原则 |
| 用 AI 代理自行宣告 Phase 完成 | 本次教训 |

---

## 多人协作规则（新增）

基于此次 master 分支合并经验：

1. **PR 之前先做文件级 diff 分析**，不直接 merge 或 rebase
2. **Main 的 BDD/oracle/governance 体系是核心资产**，任何合并不得移除这些模块
3. **master 的改进通过 cherry-pick 合并**，不整体覆盖
4. **broken import（如 audit_trail/case_compare）记录为新任务**，不作为"已完成"合并
5. **文件编码问题（如 providers.py 的 ??? 乱码）在合并前修复**
