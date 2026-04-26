# Maker / Checker 调用说明

本文档说明当前项目中 `maker`、`checker`、`report` 的调用方式、关键参数、输出目录、严格覆盖判定规则和接手注意事项。

本文档是运行说明，不是架构总览。
运行前请先确认当前输入 artifacts、schema 约束、model/prompt 配置和 phase 边界已经与治理文档一致。

## 1. 相关脚本与目录

- 入口脚本：`main.py`
- CLI 定义：`src/lme_testing/cli.py`
- 配置加载：`src/lme_testing/config.py`
- 模型调用适配：`src/lme_testing/providers.py`
- maker/checker 主流程：`src/lme_testing/pipelines.py`
- 提示词模板：`src/lme_testing/prompts.py`
- 输出结构校验：`src/lme_testing/schemas.py`
- HTML 报表导出：`src/lme_testing/reporting.py`
- 结果读写：`src/lme_testing/storage.py`
- 全量规则输入：`artifacts/lme_rules_v2_2/semantic_rules.json`
- POC 小样本输入：`artifacts/poc_two_rules/semantic_rules.json`
- 模型配置样例：`config/llm_profiles.json`

## 2. 配置文件说明

默认配置文件：

```text
config/llm_profiles.json
```

## 2.1 运行前提与治理约束

在运行 `maker` / `checker` 之前，应先确认以下前提成立：

- 输入 `semantic_rules.json` 来自当前受控 extraction 流程，而不是临时手改或聊天产物
- 上游 `atomic_rule` / `semantic_rule` artifacts 已通过基本校验并可追溯到源文档
- 本次运行使用的 model / prompt / config 可在 repo 中被识别和回溯
- 当前运行目标属于 active roadmap phase，不要把后续 phase 的 planner / normalized BDD / step integration 假设混入 maker/checker baseline

推荐先阅读：

- `docs/planning/roadmap.md`
- `docs/governance/model_governance.md`
- `docs/governance/testing_governance.md`
- `docs/governance/acceptance.md`

## 3. maker 调用方式

### 3.1 小样本联调

```powershell
python main.py --config config/llm_profiles.json maker `
  --input artifacts/poc_two_rules/semantic_rules.json `
  --output-dir runs/poc/maker `
  --batch-size 2
```

### 3.2 全量执行

```powershell
python main.py --config config/llm_profiles.json maker `
  --input artifacts/lme_rules_v2_2/semantic_rules.json `
  --output-dir runs/maker `
  --batch-size 3
```

### 3.3 常用参数

- `--input`
- `--output-dir`
- `--limit`
- `--batch-size`
- `--resume-from`

### 3.4 maker 运行说明

- `maker` 的职责是基于受控 `semantic_rule` 生成 case 候选，不负责修复上游规则质量问题
- 如果输入 rule 的 evidence、traceability 或 classification 明显有问题，应先回到 extraction / semantic artifact 层修正
- baseline 调试默认从小样本开始，不建议直接拿全量规则做 prompt 调参
- `maker` 会在每次运行开始时写出 `maker_input_quality.json`，记录 rule_type 分布、`reference_only` 比例、可进入 maker 的 testable rule 数量，以及被排除的 rule ID
- `maker` 默认只对 testable / coverage-eligible rules 调用 LLM；`reference_only` 或 `coverage_eligible=false` 的规则会写入 `maker_excluded_rules.json`，并在 coverage/report 中保持 `not_applicable`
- 对 testable rules，空 `scenarios` 是硬失败；只有明确的 `reference_only` / non-coverage-eligible rules 可以没有场景

## 4. checker 调用方式

### 4.1 小样本联调

```powershell
python main.py --config config/llm_profiles.json checker `
  --rules artifacts/poc_two_rules/semantic_rules.json `
  --cases runs/poc/maker/<run_id>/maker_cases.jsonl `
  --output-dir runs/poc/checker `
  --batch-size 2
```

### 4.2 全量执行

```powershell
python main.py --config config/llm_profiles.json checker `
  --rules artifacts/lme_rules_v2_2/semantic_rules.json `
  --cases runs/maker/<run_id>/maker_cases.jsonl `
  --output-dir runs/checker `
  --batch-size 3
```

### 4.3 常用参数

- `--rules`
- `--cases`
- `--output-dir`
- `--limit`
- `--batch-size`
- `--resume-from`

### 4.4 checker 运行说明

- `checker` 的职责是评审 `maker` 产物与规则覆盖关系，不应被当成上游 rule 质量缺陷的替代修复层
- checker 的稳定性应优先在小型 governed baseline 上观察，而不是默认要求全量重复跑
- 如果 checker 输出持续暴露同类上游问题，应优先回看 `semantic_rules.json` 而不是继续追加下游补丁

## 5. report 调用方式

`report` 用于把 `maker_cases.jsonl + checker_reviews.jsonl + summary.json + coverage_report.json` 渲染成人类可读 HTML，并自动额外输出 maker/checker 各自的可读页面。

### 5.1 小样本 HTML

```powershell
python main.py report `
  --maker-cases runs/poc/maker/<run_id>/maker_cases.jsonl `
  --checker-reviews runs/poc/checker/<run_id>/checker_reviews.jsonl `
  --maker-summary runs/poc/maker/<run_id>/summary.json `
  --checker-summary runs/poc/checker/<run_id>/summary.json `
  --coverage-report runs/poc/checker/<run_id>/coverage_report.json `
  --output-html reports/poc_two_rules/report.html
```

### 5.2 全量 HTML

```powershell
python main.py report `
  --maker-cases runs/maker/<run_id>/maker_cases.jsonl `
  --checker-reviews runs/checker/<run_id>/checker_reviews.jsonl `
  --maker-summary runs/maker/<run_id>/summary.json `
  --checker-summary runs/checker/<run_id>/summary.json `
  --coverage-report runs/checker/<run_id>/coverage_report.json `
  --output-html reports/full_rules/report.html
```

### 5.3 report 输出文件

执行一次 `report` 会得到三份 HTML：

- `report.html`
  - 总览报表，支持按 `Overall`、`Coverage` 和关键词筛选
  - 显示 rule 级的 `rule_coverage_status`、`rule_pass_status`、required/present/accepted/missing case types
- `maker_readable.html`
  - 只看 maker 结果，方便检查 rule 是否遗漏、scenario 数是否合理、`given / when / then / evidence` 是否完整
- `checker_readable.html`
  - 只看 checker 审核结果，方便检查 review 是否遗漏、`scores / findings / coverage reason` 是否合理

### 5.4 report 的使用边界

- `report` 用于提高结果可读性，不替代 schema 校验、artifact 审查或 acceptance gate
- 报表里看到的 coverage / pass 结果依赖上游 artifacts 的质量，因此不能把 HTML 视为独立真相来源

## 6. 当前 prompt / schema 约束

### 6.1 maker

- 每条输入 `semantic_rule_id` 必须恰好返回一个 `result`
- 不能漏掉 batch 内 rule，也不能返回额外 rule
- 每个 scenario 必须声明 `case_type`
- 对每条 rule，maker 必须按 `required_case_types` 生成完整 case 组
- 对每条 rule，必须做到 `required_case_types` 中每种类型恰好一个 scenario，不可缺失、不可重复
- `case_type` 只能取以下受控枚举：
  - `positive`
  - `negative`
  - `boundary`
  - `exception`
  - `state_transition`
  - `data_validation`
- `requirement_ids` 必须能映射回 source `atomic_rule_ids`
- `quote` 必须短、逐条对应、不能多条证据混成一个长 quote
- 代码层会二次校验：若返回数量不对、rule 对不上、`case_type` 非法、quote 太长或 evidence 没覆盖 requirement，直接报错

### 6.2 checker

- batch 内每个 `case_id` 必须恰好返回一个审核结果
- 不能漏掉 case，也不能返回额外 case
- `semantic_rule_id` 必须和输入 case 对应关系一致
- 必须返回以下严格字段：
  - `case_type`
  - `case_type_accepted`
  - `coverage_relevance`
  - `blocking_findings_count`
  - `is_blocking`
  - `coverage_assessment.status`
- `coverage_assessment.status` 只能取：
  - `covered`
  - `partial`
  - `uncovered`
  - `not_applicable`
- 代码层会二次校验：若出现缺失、重复、额外 `case_id` 或非法枚举值，直接报错

## 7. 严格覆盖判定规则

### 7.1 当前不再使用“任意一个 case 命中就算整条 rule covered”的宽松口径

现在覆盖率按 `semantic_rule` 聚合，并结合该 rule 的 `required_case_types` 计算：

- `rule_coverage_status`
  - `fully_covered`
  - `partially_covered`
  - `uncovered`
  - `not_applicable`
- `rule_pass_status`
  - `pass`
  - `fail`
  - `not_applicable`

### 7.2 accepted case type 的判定条件

某个 case type 只有在同时满足以下条件时，才会被计入某条 rule 的 `accepted_case_types`：

- checker 返回的 `case_type` 合法
- `case_type_accepted = true`
- `coverage_relevance = direct`
- `is_blocking = false`

### 7.3 fully_covered 的判定条件

某条 rule 只有在“所有必选 case type 都至少有一个被 checker 接受”的情况下，才会被记为 `fully_covered`，并同时得到 `rule_pass_status = pass`。

如果只覆盖了部分必选类型，则是 `partially_covered`。
如果一个必选类型都没有被接受，则是 `uncovered`。
如果 rule 被标记为 `reference_only` 或 `coverage_eligible = false`，则是 `not_applicable`。

### 7.4 rule_type 到必选 case type 的映射

当前内置映射如下：

- `obligation`
  - required: `positive`, `negative`
  - optional: `boundary`, `exception`
- `prohibition`
  - required: `negative`, `positive`
  - optional: `exception`
- `permission`
  - required: `positive`
  - optional: `negative`, `exception`
- `deadline`
  - required: `positive`, `boundary`, `negative`
  - optional: `exception`
- `state_transition`
  - required: `positive`, `state_transition`
  - optional: `negative`, `exception`
- `data_constraint`
  - required: `positive`, `negative`, `data_validation`
  - optional: `boundary`
- `enum_definition`
  - required: `positive`, `negative`
- `workflow`
  - required: `positive`, `negative`, `exception`
  - optional: `state_transition`
- `calculation`
  - required: `positive`, `boundary`, `data_validation`
  - optional: `negative`
- `reference_only`
  - not applicable

## 8. 推荐执行顺序

1. 先跑 `artifacts/poc_two_rules/semantic_rules.json`
2. 确认本次 run 的 config、model、prompt 口径明确且可追溯
3. 先看 maker run 下的 `maker_input_quality.json`；如果 `reference_only_ratio` 异常偏高，应回到 extraction / classification 层修复，不要继续把空场景送入 BDD
4. 看 maker / checker 原始输出是否稳定
5. 生成 HTML 做人工快速审核
6. 再跑全量规则
7. 如果中途中断，用 `--resume-from` 续跑，不要从头重跑

## 8.1 计算指南类 PDF 注意事项

对公式、参数文件、字段布局、风控计算说明一类文档，优先使用 extraction 的 `calculation_guide` document class：

```powershell
python scripts/extract_matching_rules.py `
  --document-class calculation_guide `
  --input artifacts/im_hk_v13/source_from_pdf.md `
  --input-format md `
  --output-dir artifacts/im_hk_v13 `
  --doc-id im_hk_v13 `
  --doc-title "Initial Margin Calculation Guide HKv13" `
  --doc-version HKv13
```

该 class 会把公式和 margin requirement 说明优先归为 `calculation`，把 CSV/file/field/layout 说明优先归为 `data_constraint`，并把目录/纯引用内容保留为 `reference_only`。

## 9. 当前已生成的真实产物

### 9.1 小样本 POC

- maker：`runs/poc/maker/20260322T143032Z/maker_cases.jsonl`
- checker：`runs/poc/checker/20260322T143139Z/checker_reviews.jsonl`
- POC 总览 HTML：`reports/poc_two_rules/report.html`
- POC maker 可读 HTML：`reports/poc_two_rules/maker_readable.html`
- POC checker 可读 HTML：`reports/poc_two_rules/checker_readable.html`

### 9.2 全量样本

- maker 合并产物：`runs/maker/20260322T132322Z_full/maker_cases.jsonl`
- checker 合并产物：`runs/checker/20260322T140332Z_full/checker_reviews.jsonl`
- 全量总览 HTML：`reports/full_rules/report.html`
- 全量 maker 可读 HTML：`reports/full_rules/maker_readable.html`
- 全量 checker 可读 HTML：`reports/full_rules/checker_readable.html`

## 10. 接手开发注意事项

- 如果修改了 `lme_testing` 下脚本的调用方式、关键参数、输出结构，必须同步更新本文档。
- 如果修改了 maker/checker 的 schema，也必须同步更新 `prompts.py` 中的 schema 示例和本文档。
- 如果修改了 `rule_type -> required_case_types` 映射，也必须同步更新本文档第 7 节。
- 以后任何真实联调，默认先走 `artifacts/poc_two_rules` 小样本，不要直接全量跑。
- 如果修改了 run metadata、model/profile 记录方式或报表口径，也必须同步检查 `docs/governance/model_governance.md`、`docs/governance/testing_governance.md` 与本文档是否仍一致。




