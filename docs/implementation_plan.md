# LME Testing — Revised Implementation Plan

**版本：** 2.0  
**修订日期：** 2026-04-18  
**对应 Roadmap：** Stage 1（真实数据接入与可信基准建立）  
**范围说明：** 本文档只覆盖 Stage 1 的执行任务。Stage 2 任务将在 Stage 1 完成后、基于真实数据另行制定。

---

## 如何使用本文档

每个任务遵循统一结构：

- **任务 ID** — 全局唯一，格式 `S1-Txx`
- **目标** — 一句话说清楚做什么
- **为什么现在做** — 说明优先级依据
- **前置依赖** — 必须先完成的任务
- **输入契约** — 任务开始时必须存在的输入
- **输出契约** — 任务完成时必须产出的输出
- **实现要点** — 关键技术决策和约束
- **验收标准** — 可量化的完成判断
- **自评格式** — PASS / PARTIAL / FAIL
- **不在范围内** — 明确的边界

**治理规则：** 任务未达到 PASS 不得标记完成。PARTIAL 必须记录缺失项和补做计划。

---

## 任务依赖关系

```
S1-T01（Schema signal 修复）  ─┐
S1-T02（Run 路径对齐）        ─┼─→ S1-T04（全量基准运行）─→ S1-T05（状态声明重写）
S1-T03（Session 并发安全）    ─┘
                               ↓
                         S1-T03b（Checker stability）─→ S1-T04 ─→ S1-T05
```

S1-T01、S1-T02、S1-T03 可并行执行。  
S1-T03b（Checker stability）依赖 S1-T02 的路径格式确认。  
S1-T04 依赖 S1-T01 和 S1-T02。  
S1-T05 在所有任务完成后执行。

---

## S1-T01 — Schema Failure Rate 数据源修复

**目标：** 让 `schema_failure_rate` governance signal 消费真实验证数据而非空值。

### 为什么现在做

`_compute_schema_signals()` 的代码注释明确承认当前没有持久化数据源，导致 `schema_failure_rate` 恒为 0.0%，这是一个已知的假数据问题。这是 governance 体系可信度的基础，必须首先修复。

### 前置依赖

无

### 输入契约

- `scripts/validate_schemas.py`（现有）
- `lme_testing/signals/__init__.py` 中的 `_compute_schema_signals()`（现有）
- `schemas/fixtures/` 下的 valid/invalid fixture 集合（现有）

### 输出契约

**代码变更：**
- `scripts/validate_schemas.py`：新增 `--output-json <path>` 可选参数
  - 产出格式：
    ```json
    {
      "validated_at": "2026-04-18T10:00:00Z",
      "total_schemas": 7,
      "total_fixtures": 12,
      "passed": 12,
      "failed": 0,
      "failures": []
    }
    ```
  - 不传 `--output-json` 时行为与现有完全一致（向后兼容）

**CI 变更：**
- `.github/workflows/ci.yml` 的 `schema-validation` job 新增：
  ```
  python scripts/validate_schemas.py --output-json runs/schema_validation_latest.json
  ```

**信号读取变更：**
- `lme_testing/signals/__init__.py` 的 `_compute_schema_signals()`：
  - 优先读取 `runs/schema_validation_latest.json`
  - 若文件不存在，返回 `SchemaSignals()`（空值）并在日志中标注 `data_source: no_data`
  - 在 `GovernanceSignals.to_dict()` 中新增 `schema_signal_source` 字段：`"real_validation"` / `"no_data"`

**文档变更：**
- `docs/architecture.md`：Validation Architecture 小节补充"schema validation 产出持久化结果"的说明

### 实现要点

- `--output-json` 参数使用 `argparse` 添加，`None` 时不写文件
- 写文件前确保目录存在（`Path(output_path).parent.mkdir(parents=True, exist_ok=True)`）
- 文件写入使用原子操作（先写 `.tmp` 再 `rename`），防止 CI 并发写入损坏
- 不修改 schema 验证逻辑本身，只新增输出路径

### 验收标准

- [ ] `python scripts/validate_schemas.py --output-json /tmp/test.json` 产出合法 JSON
- [ ] CI `schema-validation` job 产出 `runs/schema_validation_latest.json`
- [ ] `python main.py governance-signals` 后，`governance_signals.json` 中 `schema_signal_source` 为 `"real_validation"`
- [ ] 将 `schemas/fixtures/atomic_rule_invalid.json` 故意传入验证时，`failures` 非空，`schema_failure_rate > 0`
- [ ] `--output-json` 不传时，现有行为无变化（回归测试通过）

**自评：** PASS / PARTIAL / FAIL

### 不在范围内

- 修改 schema 内容
- 修改 fixture 内容（除非发现现有 fixture 有 bug）
- 改变 CI 对 schema 失败的响应方式（仍然是 hard fail）

---

## S1-T02 — 全量运行数据路径对齐

**目标：** 让 governance signals 系统能够正确读取全量 183 条规则的已有运行数据。

### 为什么现在做

全量运行数据已经存在，但 `compute_governance_signals()` 的目录扫描路径与实际输出路径不匹配，导致所有基于真实数据的 signal 失效。这是让现有工作产生价值的最快路径。

### 前置依赖

无（但需要先手动定位实际运行输出目录）

### 输入契约

**第一步（人工）：** 找到全量运行的实际输出目录，确认其结构：
```
runs/
  <run_type>/          # maker / checker / bdd / step-registry
    <run_id>/          # 时间戳格式
      maker_cases.jsonl / checker_reviews.jsonl / coverage_report.json 等
```

若实际结构不同，以实际结构为准，不强行对齐代码。

### 输出契约

**文档产出（必须先于代码变更）：**
- `docs/run_directory_structure.md`（新建）：
  - 标准运行输出目录结构
  - 每种 pipeline（maker/checker/bdd/step-registry）的输出文件清单
  - 历史运行的实际结构（如果与标准不同，记录差异和原因）

**代码变更（基于文档中确认的实际结构）：**
- `lme_testing/signals/__init__.py`：
  - `_compute_coverage_signals()`：确保扫描路径与实际 checker 输出路径一致
  - `_compute_step_binding_signals()`：确保扫描路径与实际 step-registry 输出路径一致
  - `_compute_checker_instability_signals()`：确保扫描路径与 checker_stability.py 输出路径一致
  - 每个 `_compute_*` 函数新增 `data_source` 字段在返回值中

**验证产出：**
- `governance_signals.json` 在修复后的 `runs_analyzed > 0`
- `coverage_signals.total_rules` 接近 183

### 实现要点

- **先写文档，后改代码**：路径结构先在 `run_directory_structure.md` 中确认，避免猜测式修改
- 若发现历史运行结构与预期不同，在文档中记录差异，选择：a）重命名历史目录适配代码，或 b）调整代码适配历史目录——优先选 b）
- 路径扫描逻辑应具备容错性：目录不存在时返回空信号而非 crash
- 新增 `--runs-dir` CLI 参数到 `governance-signals` 命令，允许指定非默认的 runs 目录

### 验收标准

- [ ] `docs/run_directory_structure.md` 存在，描述了真实的目录结构
- [ ] `python main.py governance-signals` 输出中 `runs_analyzed > 0`
- [ ] `coverage_signals.total_rules` 在全量运行数据可读时接近 183
- [ ] 若全量运行数据目录不存在，`governance-signals` 不 crash，输出空信号并有明确日志
- [ ] `python main.py governance-signals --runs-dir <path>` 支持指定目录

**自评：** PASS / PARTIAL / FAIL

### 不在范围内

- 重新运行全量 pipeline（这是 S1-T04 的工作）
- 修改 runs 目录的命名约定（保持向后兼容）

---

## S1-T03 — Session Snapshot 原子写入

**目标：** 修复 review_session.py 的 session snapshot 写入，防止快速连续操作导致数据损坏。

### 为什么现在做

已知缺陷：Web UI 的 Save 操作直接覆盖写入 JSON 文件，无并发保护。虽然当前是单用户场景，但快速点击 Save 可能产生部分写入。这是低成本、低风险的基础数据完整性修复。

### 前置依赖

无

### 输入契约

- `lme_testing/review_session.py` 中所有写入 session snapshot 的路径：
  - `save_bdd_edits()` → `human_bdd_edits_latest.json`
  - `save_scripts_edits()` → `human_scripts_edits_latest.json`
  - session state 持久化

### 输出契约

**代码变更：**
- `lme_testing/storage.py` 新增 `atomic_write_json(path, data)` 工具函数：
  ```python
  def atomic_write_json(path: Path, data: dict) -> None:
      """写入 JSON 文件，使用 tmp + rename 保证原子性。"""
      tmp_path = path.with_suffix('.tmp')
      tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
      tmp_path.replace(path)  # os.replace，原子操作
  ```
- `review_session.py` 中所有 session snapshot 写入替换为 `atomic_write_json()`

**文档变更：**
- `docs/architecture.md` Review modules 小节新增设计约束：
  > "Session snapshot 使用原子写入（tmp + rename）。系统设计为单用户使用，不支持多用户并发访问。"

### 实现要点

- `os.replace()` / `Path.replace()` 在 POSIX 和 Windows 上均为原子操作（同一文件系统内）
- `tmp_path` 与目标路径在同一目录，确保同一文件系统
- 不引入文件锁（过度设计），原子写入对单用户场景足够
- 写入失败（如磁盘满）应抛出异常而非静默失败

### 验收标准

- [ ] `storage.py` 中存在 `atomic_write_json()` 函数
- [ ] `review_session.py` 中没有直接的 `json.dump()` / `.write_text()` 写入 snapshot 文件
- [ ] 模拟快速连续 POST `/api/bdd/save`（5 次）后 snapshot 文件合法（`json.loads()` 不抛出异常）
- [ ] `docs/architecture.md` 明确声明单用户设计约束
- [ ] 现有 review session 功能回归测试通过

**自评：** PASS / PARTIAL / FAIL

### 不在范围内

- 多用户并发支持
- 数据库存储（过度设计）
- 文件锁机制（对单用户场景过度）

---

## S1-T03b — Checker 真实稳定性测量

**目标：** 用真实 MiniMax API 测量 checker 在相同输入上的重复一致性，替换当前基于 stub 的假数据。

### 为什么现在做

当前 `checker_instability = 0%` 基于 StubProvider（确定性）测量，完全不代表真实 LLM 行为。这个数字是整个 checker governance 体系的核心信任基础，必须用真实数据重建。

### 前置依赖

- S1-T02 完成（确认 stability_report 的标准输出路径）
- MiniMax API key 可用

### 输入契约

- `logs-from-backup-run/maker_cases.jsonl`（已有的 5 个 maker case）
- `artifacts/poc_two_rules/semantic_rules.json`（对应的 semantic rules）
- `config/llm_profiles.minimax.json`（MiniMax 真实配置）
- `scripts/checker_stability.py`（现有脚本）

### 输出契约

**运行产出：**
- `runs/stability_real/run_a/checker_reviews.jsonl`
- `runs/stability_real/run_b/checker_reviews.jsonl`（相同输入，独立运行）
- `runs/stability_real/stability_report.json`：
  ```json
  {
    "data_source": "real_api",
    "model": "MiniMax-M2.7",
    "prompt_version": "...",
    "total_cases": 5,
    "stable_cases": N,
    "unstable_cases": N,
    "instability_rate": 0.XX,
    "unstable_case_ids": [...]
  }
  ```

**文档更新：**
- `docs/acceptance.md` Phase 1 Gate 6 Evidence 更新：
  - 旧：`checker instability: 0% (stub-only runs are deterministic)`
  - 新：`checker instability: X% (real MiniMax-M2.7, poc_two_rules, 2 runs, 2026-04-xx)`
- 若 `instability_rate > 0.05`：`docs/model_governance.md` 新增 MiniMax 稳定性实测记录，包括不稳定 case 分析

**Governance signal 更新：**
- `governance_signals.json` 中 `checker_instability_rate` 来自真实 stability_report

### 实现要点

- 两次运行必须使用完全相同的：输入文件、prompt version、model、temperature
- 两次运行间隔 ≥ 5 分钟，避免模型缓存干扰
- `stability_report.json` 必须新增 `data_source: "real_api"` 字段（区分 stub 运行）
- 若两次运行结果完全相同（instability=0%），在报告中保留原始输出供审查，不直接声称"稳定"

### 验收标准

- [ ] 两次 checker 运行使用真实 MiniMax API（日志中有真实 HTTP 调用记录）
- [ ] `stability_report.json` 包含 `data_source: "real_api"`
- [ ] `docs/acceptance.md` Phase 1 Gate 6 Evidence 更新为真实数字
- [ ] `governance_signals.json` 的 `checker_instability_rate` 来自真实 stability_report
- [ ] 若 instability > 5%：`docs/model_governance.md` 有分析记录

**自评：** PASS / PARTIAL / FAIL

### 不在范围内

- 基于稳定性测量结果修改 prompt（这是 Stage 2 的工作）
- 修改 checker instability 阈值（先收集数据，再决定）
- 对全量 183 条规则做稳定性测量（成本过高，poc baseline 足够）

---

## S1-T04 — 全量规则集质量基准建立

**目标：** 建立第一个基于真实数据的、有文档记录的全量质量基准，成为后续所有质量提升的参照点。

### 为什么现在做

这是 Stage 1 最核心的任务。在此之前，系统的真实能力边界是未知的。这个基准将回答："当前系统对 LME 全量匹配规则的测试设计能力到底是什么水平？"

### 前置依赖

- S1-T01 完成（schema signal 有真实数据）
- S1-T02 完成（路径结构明确）
- S1-T03b 完成（了解 checker 真实稳定性，评估 baseline 可信度）

### 输入契约

- `artifacts/lme_rules_v2_2/semantic_rules.json`（183 条规则）
- `config/llm_profiles.minimax.json`（MiniMax 真实配置）
- `docs/run_directory_structure.md`（S1-T02 产出，确认路径格式）

### 输出契约

**运行产出（使用标准路径）：**
```
runs/baseline_full/
  maker/
    <run_id>/
      maker_cases.jsonl
      summary.json
  checker/
    <run_id>/
      checker_reviews.jsonl
      coverage_report.json
      summary.json
```

**报告产出：**
- `reports/baseline_full_<date>.html`

**关键文档（必须产出）：**
- `docs/releases/BASELINE-183-RULES.md`，内容包括：
  - 运行日期、模型版本、prompt version
  - `coverage_percent`（真实数字，不管是否好看）
  - 各 rule_type 的覆盖率分布
  - 人工随机抽查记录（≥ 10 条规则，逐条评估 maker 输出质量）
  - **已知问题列表**（quality 低的规则类型、常见失败模式）
  - 与 poc_two_rules baseline 的对比

### 实现要点

**运行策略（避免一次性全量失败）：**
```bash
# 分批运行，支持断点续传
python main.py maker \
  --input artifacts/lme_rules_v2_2/semantic_rules.json \
  --output-dir runs/baseline_full/maker \
  --batch-size 8 \
  --resume-from <existing_jsonl_if_any>

python main.py checker \
  --rules artifacts/lme_rules_v2_2/semantic_rules.json \
  --cases runs/baseline_full/maker/<run_id>/maker_cases.jsonl \
  --output-dir runs/baseline_full/checker \
  --batch-size 8
```

**人工抽查方法：**
- 随机选取 10 条规则（覆盖不同 rule_type）
- 对每条规则：阅读 semantic rule → 阅读 maker 生成的 scenarios → 主观评估"这个场景对规则的覆盖是否合理"
- 评级：Good / Acceptable / Poor
- 记录 Poor 的原因

**质量结果处理原则：**
- coverage < 60%：明确记录，分析失败模式，**不调整阈值掩盖问题**
- coverage 60-80%：记录并分析，在 Stage 2 决定是否做 prompt 调优
- coverage > 80%：记录，与 poc_two_rules 对比是否有显著差距

### 验收标准

- [ ] `coverage_report.json` 包含 ≥ 180 条规则的状态（允许少量提取失败）
- [ ] `governance_signals.json` 中 `coverage_signals.total_rules ≥ 180`
- [ ] `docs/releases/BASELINE-183-RULES.md` 存在，包含所有必需章节
- [ ] 人工抽查 ≥ 10 条规则，评估记录在 `BASELINE-183-RULES.md` 中
- [ ] `reports/baseline_full_<date>.html` 可在浏览器正常打开
- [ ] 不论 coverage 数字是否好看，文档如实记录（不掩盖问题）

**自评：** PASS / PARTIAL / FAIL

### 不在范围内

- 基于结果调整 prompt（Stage 2）
- 对全量规则做稳定性双次运行（成本过高）
- 将本次结果作为"最终质量声明"（这只是第一个基准，会迭代）

---

## S1-T05 — 项目状态声明重写

**目标：** 用有数据支撑的、诚实的状态描述替换所有误导性"Complete"声明。

### 为什么现在做

这是 Stage 1 的收尾任务，也是对外诚实沟通的基础。在有真实数字之前不写，有了之后必须写。

### 前置依赖

所有 S1-T01 至 S1-T04 完成

### 输入契约

- S1-T01 产出的真实 schema failure rate
- S1-T02 产出的真实 runs_analyzed
- S1-T03b 产出的真实 checker instability rate
- S1-T04 产出的真实 coverage_percent 和人工抽查结论

### 输出契约

**`README.md` Project Status 小节重写：**
```markdown
## Project Status

**框架实现：** ✅ 完成（maker / checker / BDD / oracle / governance signals）

**验证状态：**

| 维度 | 状态 | 数据 |
|------|------|------|
| Schema 契约验证 | ✅ 通过 | schema_failure_rate: X% |
| POC 端到端（2条规则）| ✅ 通过 | coverage: 100% |
| 全量规则集质量基准 | ✅ 已建立 | coverage: X%，详见 BASELINE-183-RULES.md |
| Checker 稳定性 | ✅ 已测量 | instability: X%（真实 MiniMax API）|
| 真实执行环境接入 | ⏳ 待外部条件 | 需要 LME VM 访问权限 |
| 多用户协作 | ❌ 非当前阶段 | 设计为单用户工具 |
```

**`TODO.md` 重写：** 区分"代码实现 ✅"和"真实验证 ✅/🔄"

**`docs/acceptance.md` 每个 gate 补充 `Verification Type` 字段：**
- `code_implementation` — 代码写出来了
- `stub_verified` — 用 stub 验证通过
- `real_data_verified` — 用真实 API 和真实规模验证通过

### 验收标准

- [ ] `README.md` 中不存在"All Phases Complete"表述
- [ ] `README.md` Project Status 中所有数字有对应的数据来源文件
- [ ] `TODO.md` 中清晰区分代码完成 vs 验证完成
- [ ] `docs/acceptance.md` 每个 gate 有 `Verification Type` 标注
- [ ] 没有任何文档声称"100% coverage"而不注明"基于 X 条规则"

**自评：** PASS / PARTIAL / FAIL

---

## Stage 1 完成检查清单

在宣告 Stage 1 完成之前，确认所有项目：

### 必须完成（blocking）

- [ ] S1-T01：`schema_failure_rate` 有真实数据
- [ ] S1-T02：`runs_analyzed > 0`，`total_rules ≥ 180`
- [ ] S1-T03：Session snapshot 使用原子写入
- [ ] S1-T03b：`checker_instability_rate` 有真实 API 数据
- [ ] S1-T04：`BASELINE-183-RULES.md` 存在，有人工抽查记录
- [ ] S1-T05：README 状态声明有数据支撑

### 建议完成（non-blocking）

- [ ] `docs/run_directory_structure.md` 存在且准确
- [ ] CI governance-signals job 输出真实数字（非 stub）
- [ ] 所有 governance signal 有 `data_source` 字段标注

### Stage 1 不需要完成的事

- ❌ 提升 coverage 数字（Stage 2）
- ❌ 改进 prompt（Stage 2，且需要基于 Stage 1 数据决定）
- ❌ 接入真实 LME API（Stage 3）
- ❌ 新增 oracle（Stage 2，基于 Stage 1 失败模式分析后决定）

---

## 附录：被暂缓的 Stage 2 任务占位符

以下任务在 Stage 1 完成后，基于真实数据重新制定计划：

| 任务 ID | 方向 | 触发条件 |
|---------|------|---------|
| S2-T01 | Maker prompt 质量提升 | Stage 1 coverage < 80% 或抽查 Poor 率 > 30% |
| S2-T02 | Checker 稳定性改进 | Stage 1 instability > 10% |
| S2-T03 | Oracle 实测验证 | Stage 1 识别出高频确定性规则类型 |
| S2-T04 | 全量规则 BDD 生成验证 | Stage 1 基准建立后的 BDD 质量评估 |

**Stage 2 的具体任务不在本文档中制定。** 在 Stage 1 的真实数字出来之前，任何 Stage 2 计划都是基于未知的猜测。
