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
  - 注册 `maker`、`checker`、`report` 三个命令

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

## 三个最重要的命令

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
