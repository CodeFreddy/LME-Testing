# LME Testing

`LME-Testing` 是一个围绕 LME 官方规则文档构建的测试设计原型项目。

它的目标不是直接执行撮合测试，而是先把官方文档中的规则抽取出来，转换成结构化的 `atomic_rule` / `semantic_rule`，再利用两个大模型角色完成一条可追溯的测试设计链路：

- `maker`
  - 负责解析结构化规则，生成 BDD 风格测试场景和测试案例
- `checker`
  - 负责审核 maker 产物，判断 case 是否合理、证据是否一致、覆盖是否完整
- `report`
  - 负责把 JSON/JSONL 产物转成人类更容易阅读的 HTML 报表

项目当前重点在三个方向：

- 文档到规则的稳定抽取
- maker / checker 双模型协作生成测试案例
- 基于 `required_case_types` 的严格覆盖率判定

## 项目适合谁看

这份 README 面向第一次接手这个项目的人。你不需要先理解所有脚本细节，只需要先知道：

1. 输入是什么
2. 中间产物是什么
3. 哪些脚本是关键入口
4. 运行顺序是什么

更细的命令、参数和产物结构，统一参考 [docs/maker_checker_usage.md](docs/maker_checker_usage.md)。

## 项目当前在做什么

当前实现的是一个“文档驱动测试设计”流水线：

1. 从 LME 官方 PDF / 文本中抽取规则
2. 把规则拆分成机器更容易处理的结构化单元
3. 用 maker 按规则生成测试案例
4. 用 checker 审核测试案例
5. 统计每条规则的覆盖状态
6. 输出 HTML 报表，方便人工审核

这里的“覆盖”不是简单地有一个 case 命中就算通过。
当前版本已经升级成更严格的规则：

- 不同 `rule_type` 会映射到不同的 `required_case_types`
- 只有所有必选 case type 都被有效覆盖，rule 才会是 `fully_covered`
- 否则只能是 `partially_covered` 或 `uncovered`

## 目录概览

### 业务入口

- `main.py`
  - 项目命令行入口
- `lme_testing/cli.py`
  - 注册 `maker`、`checker`、`report`、`planner`、`bdd`、`step-registry`、`governance-signals` 命令

### 核心实现

- `lme_testing/config.py`
  - 加载模型配置、角色绑定、API key
- `lme_testing/providers.py`
  - 统一模型调用适配层，目前走 OpenAI-compatible 接口
- `lme_testing/prompts.py`
  - maker / checker 的系统提示词和批量用户提示词
- `lme_testing/schemas.py`
  - 校验 maker / checker 输出 JSON 是否满足严格 schema
- `lme_testing/pipelines.py`
  - maker / checker 主流程、覆盖率汇总、批处理、续跑逻辑
- `lme_testing/reporting.py`
  - 生成 HTML 总览页、maker 可读页、checker 可读页
- `lme_testing/storage.py`
  - JSON / JSONL 读写工具

### 文档解析与规则建模

- `scripts/extract_matching_rules.py`
  - 从源文档抽取 clause / atomic rule
- `scripts/generate_semantic_rules.py`
  - 从 atomic rule 进一步生成 semantic rule
- `docs/rule_model_and_parsing_design.md`
  - 规则模型设计说明
- `docs/rule_extraction_script_guide.md`
  - 文档抽取脚本说明

### 输入与产物

- `artifacts/lme_rules_v2_2/`
  - 当前全量规则输入与抽取产物
- `artifacts/poc_two_rules/`
  - 用于快速联调的 POC 小样本，只包含两条 rule
- `runs/`
  - maker / checker 原始运行产物
- `reports/`
  - HTML 报表输出

## 核心调用链路

如果你只想知道项目是怎么跑起来的，可以按这条链路理解：

### 1. 文档抽取阶段

```text
docs / 原始 PDF
  -> scripts/extract_matching_rules.py
  -> atomic_rules.json
  -> scripts/generate_semantic_rules.py
  -> semantic_rules.json
```

### 2. 双模型测试设计阶段

```text
semantic_rules.json
  -> maker
  -> maker_cases.jsonl
  -> checker
  -> checker_reviews.jsonl + coverage_report.json
  -> report
  -> report.html / maker_readable.html / checker_readable.html
```

### 3. 人工审核阶段

```text
HTML 报表
  -> 人工查看 maker 生成是否合理
  -> 人工查看 checker 审核是否合理
  -> 再决定是否继续收紧 prompt、schema 或 coverage 规则
```

## 四个最重要的命令

### 1. maker

作用：根据 `semantic_rules.json` 生成测试场景。

典型输入：

- `artifacts/poc_two_rules/semantic_rules.json`
- `artifacts/lme_rules_v2_2/semantic_rules.json`

典型输出：

- `maker_cases.jsonl`
- `summary.json`
- `maker_raw_responses.jsonl`

### 2. checker

作用：审核 maker 输出，并给出规则级覆盖状态。

典型输出：

- `checker_reviews.jsonl`
- `coverage_report.json`
- `summary.json`
- `checker_raw_responses.jsonl`

### 3. report

作用：把结构化输出渲染为 HTML。

典型输出：

- `report.html`
- `maker_readable.html`
- `checker_readable.html`

### 4. governance-signals

作用：计算平台治理信号，供发布审查参考。

典型输出：

- `runs/governance_signals.json`
- schema failure rate、checker instability rate、coverage trend、step binding rate

## 推荐上手顺序

第一次接手，不要直接跑全量规则。建议按下面顺序：

1. 先看 `artifacts/poc_two_rules/`
2. 先跑基础治理检查
3. 再看 `docs/maker_checker_usage.md`
4. 用 POC 小样本跑一遍 maker
5. 再跑 checker
6. 最后生成 HTML 报表
7. 确认逻辑正确后，再考虑跑全量 `artifacts/lme_rules_v2_2/`

基础治理检查命令：

```powershell
python scripts/check_docs_governance.py
python scripts/check_artifact_governance.py
python scripts/check_release_governance.py
```

如果本机 `python` 不在 `PATH`，请改用你环境里的 Python 可执行路径运行同样命令。

启用本地 git hooks 后，每次提交会自动刷新 `docs/session_handoff.md`：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_git_hooks.ps1
```

## 当前项目里最值得关注的几个事实

- maker 和 checker 不是自由文本聊天，而是受 schema 约束的结构化调用
- checker 现在已经按更严格的 `required_case_types` 判断 rule 是否真正被覆盖
- POC 小样本是默认回归入口，避免每次都跑全量文档
- 运行结果允许持久化，因此 `runs/` 和 `reports/` 会保留历史结果，方便比较不同 prompt / schema 版本
- docs 和 baseline artifacts 现在都有独立治理检查，修改文档或基线产物前后都应先跑一遍

## 你下一步应该看什么

如果你是新开发者，建议按这个顺序读：

1. `README.md`
2. `docs/maker_checker_usage.md`
3. `lme_testing/pipelines.py`
4. `lme_testing/prompts.py`
5. `lme_testing/schemas.py`

这样能最快理解：

- 输入是什么
- maker / checker 分别做什么
- 严格覆盖是怎么判定的
- 输出应该去哪里看

## 相关文档

- 详细调用方式与参数说明： [docs/maker_checker_usage.md](docs/maker_checker_usage.md)
- 规则模型设计： [docs/rule_model_and_parsing_design.md](docs/rule_model_and_parsing_design.md)
- 规则抽取脚本说明： [docs/rule_extraction_script_guide.md](docs/rule_extraction_script_guide.md)

## Phase 3 新增内容（2026-04-14 完成）

### 新增 CLI 命令

```powershell
# governance-signals: 计算治理信号（Phase 3 Gate 4）
python main.py governance-signals --repo-root . --output runs/governance_signals.json

# step-registry: BDD step 与步骤定义库的匹配分析（Phase 3 Gate 1）
python main.py step-registry --bdd-cases runs/acceptance_e2e/20260413T134346Z/normalized_bdd.jsonl --output-dir runs/step-registry
```

### 新增治理检查

```powershell
# Release Governance 检查（Phase 3 Gate 5）
python scripts/check_release_governance.py
```

### 可执行场景模式（Phase 3 Gate 2）

`schemas/executable_scenario.schema.json` 在 BDD 场景基础上扩展了：

- 环境依赖（environment）
- 输入数据（input_data）
- Setup / Cleanup Hooks
- 确定性断言（assertions）
- Step 定义绑定（step_bindings）

支持断言类型：field_validation、state_validation、calculation_validation、deadline_check、event_sequence、pass_fail_accounting、null_check、compliance_check。

### 确定性 Oracle 框架（Phase 3 Gate 3）

`lme_testing/oracles/` 下有 8 个确定性 Oracle 模块：

| Oracle | 作用 |
|--------|------|
| field_validation | 字段类型、枚举、范围、格式校验 |
| state_validation | 系统状态期望值、允许/禁止状态 |
| calculation_validation | 数值计算、公式误差校验 |
| deadline_check | 时间窗口、截止时间校验 |
| event_sequence | 事件顺序校验 |
| pass_fail_accounting | 通过/失败计数门槛 |
| null_check | 空值/非空断言 |
| compliance_check | 义务/禁止/权限合规状态 |

用法示例：

```python
from lme_testing.oracles import evaluate_assertion

result = evaluate_assertion(
    {'assertion_id': 't1', 'type': 'null_check',
     'parameters': {'field': 'result', 'expected': 'non_null'}},
    {'input_data': {'result': 'ok'}}, None, {}
)
print(result.status)  # pass / fail / unable_to_determine / error
```

### 治理信号（Phase 3 Gate 4）

`lme_testing/signals/` 计算四类平台运营信号：

- **Schema 信号**：schema 校验失败率
- **Checker 不稳定信号**：重复运行结果差异率
- **覆盖率信号**：最新覆盖率及趋势（improving/declining/stable）
- **Step 绑定信号**：step 绑定成功率（exact + parameterized / unique patterns）

当前运行数据：

```
schema_failure_rate:    0.0%
checker_instability:   0.0%
coverage_percent:       100.0%
step_binding_rate:     35.4%
coverage_trend:         improving
```

### Release 治理（Phase 3 Gate 5）

`config/` 目录下新增三个配置文件：

- `approved_providers.json` — Tier-1/2/3 模型分级，当前：stub（Tier 1）、MiniMax-M2.7（Tier 1）、qwen3.5-plus（Tier 2 实验性）
- `compatibility_matrix.json` — 模型 × 阶段 × Pipeline 兼容性矩阵
- `benchmark_thresholds.json` — 数值化治理门槛（schema failure = 0 阻断、coverage ≥ 80% 阻断、instability ≤ 5% 警告）

`docs/releases/RELEASES.md` 记录每个正式版本的完成状态和 Benchmark 证据。

CI 新增 `Release Governance` job，每次 push/PR 均检查：
- approved_providers.json 格式和字段
- compatibility_matrix.json 完整性
- benchmark_thresholds.json 数值合理性
- docs/releases/ 有至少一个版本记录
- governance_signals.json 已生成且未超阈值
