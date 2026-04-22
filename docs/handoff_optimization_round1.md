# Optimization Round 1 — 交接摘要

> 目标受众：Sonnet 4.6 执行 agent。本轮实现 5 项优化（需求 3 已与用户协商跳过，留给后续 PR）。

---

## 3.1 需求说明

| # | 需求 | 关键决策 |
|---|---|---|
| 1 | **Audit Trail 页**：记录所有 iteration 中 checker 与 human 意见**不一致**的 case | 分歧 = (b) `block_recommendation_review == "dismissed"`；**或** (c) checker 有 blocking findings 但 human `approve`；**或** (c) checker 无 blocking 但 human `rewrite`/`reject`。一致的 case 不展示。 |
| 2 | **Compare 页**：rewrite 前后对比 | **side-by-side**；**只展示被改的 case**（按 `case_id` 交集）；对比字段：`given`/`when`/`then` 步骤、`evidence`、`assumptions`、`case_type` |
| 3 | Prompt/atomic/semantic 规则拆分优化 | **本轮跳过**，不要动 |
| 4 | Checker 独立客观 | 现状已合规（`pipelines.py:239-247` 第二轮 checker 不接触 human feedback）；**仅需** 在 `CHECKER_SYSTEM_PROMPT` 末尾加一句独立性声明 |
| 5 | Rewrite 中人类意见优先于 checker | 在 `REWRITE_SYSTEM_PROMPT` 明确 `human > checker` 优先级 |
| 6 | 只 rewrite 被标记的 case + session 记忆 | 6.1 **Case 级 rewrite**：只重写人类标 `rewrite` 的 case；同 rule 未被标记的 case **字节级保留**。一条 rule 下全部 case 都被标时等价于旧的 rule 级行为（fallback）。 6.2 **第二轮 checker 只审被重写 case**；未改 case 的上轮 review 原样继承合并。6.3 **Session memory 路线 A**：不改 `providers.py`，把 `build_rewrite_user_prompt` 改成结构化章节（不再整包 JSON），保持单轮 API 调用 |

---

## 3.2 技术设计

### 涉及文件
- 改 `lme_testing/prompts.py`
- 改 `lme_testing/pipelines.py`
- 改 `lme_testing/review_session.py`
- 改 `lme_testing/reporting.py`
- 新增 `lme_testing/audit_trail.py`
- 新增 `lme_testing/case_compare.py`

### A. `prompts.py`
1. `CHECKER_SYSTEM_PROMPT` 末尾追加：checker 永远不接收 human review，独立评审，仅凭 rule/case/evidence。
2. `REWRITE_SYSTEM_PROMPT` 加入：`"When human feedback conflicts with checker findings, human takes precedence."`
3. `build_rewrite_user_prompt` 重写为结构化章节（关键）：
   ```
   ## Semantic rule
   <semantic_rule JSON>

   ## Cases you generated last iteration (full set for this rule)
   <current_maker_record JSON>

   ## Cases the human asked you to rewrite
   target_case_ids: [...]

   ## Checker findings for target cases
   <checker_reviews filtered to target_case_ids>

   ## Human reviewer feedback for target cases (authoritative; > checker)
   <human_reviews filtered to target_case_ids>

   ## Task
   For each id in target_case_ids, output a rewritten case.
   Do NOT output cases whose id is not in target_case_ids.
   Preserve case_id; update given/when/then/evidence/assumptions/case_type as needed.
   If human feedback conflicts with checker, follow the human.
   ```

### B. `pipelines.py`
1. `_rewrite_target_rule_ids`（~line 454-462）→ 改名/改签名为 `_rewrite_targets(human_payload) -> dict[str, list[str]]`，返回 `{rule_id: [case_id, ...]}`，只收集 `review_decision == "rewrite"` 的 case。
2. `run_rewrite_pipeline`（~line 498+）：
   - 每个 batch 项新增字段 `rewrite_target_case_ids`。
   - `checker_reviews_by_rule`、`human_reviews_by_rule` 按 target case_ids 过滤后再塞进 batch。
   - Merge 逻辑：rewrite 返回的 case 按 `case_id` 替换原数组对应项；未命中的 case 原地保留。
3. `run_checker_pipeline` 新增参数 `only_case_ids: set[str] | None = None`：
   - 非空时，只送这些 case 给 checker。
   - 未送审的 case 从**上一轮 checker_reviews** 按 case_id 复制继承。
   - 最终输出的 `checker_reviews.jsonl` 仍覆盖所有 case。

### C. `lme_testing/audit_trail.py`（新）
```python
def build_audit_trail(session_dir: Path, output_html_path: Path) -> dict:
    """扫描 session 下所有 iteration，提取 checker/human 分歧，生成 audit_trail.html。"""
```
- 遍历 `session_dir/iterations/*/`
- 每个 iteration 读取 `checker_reviews.jsonl` + `human_reviews_latest.json`
- 按 `case_id` 配对，按 (b)+(c) 规则筛选
- 输出 HTML：按 iteration 分组，每条记录字段：`iteration` / `rule_id` / `case_id` / checker 判断摘要（blocking、findings、coverage_status） / human decision / block_recommendation_review / comment / issue_types
- 一致的 case 不输出

### D. `lme_testing/case_compare.py`（新）
```python
def build_case_compare(
    prev_cases_path: Path,
    next_cases_path: Path,
    rewritten_case_ids: set[str],
    iteration_prev: int,
    iteration_next: int,
    output_html_path: Path,
) -> dict: ...
```
- 交集：`case_id ∈ rewritten_case_ids`
- 对比字段：`given`/`when`/`then`、`evidence`、`assumptions`、`case_type`
- 用 `difflib.SequenceMatcher` 做行级 diff，自写简单 HTML 模板渲染 side-by-side 双栏（左 prev、右 next，差异高亮）
- 文件名：`compare_iter_{prev:03d}_vs_{next:03d}.html`

### E. `review_session.py`
- 每次 rewrite 完成后调用 `build_case_compare`，生成当前 iteration 对应的 compare 文件。
- Finalize 时（或每次 iteration 结束时）调用 `build_audit_trail`，在 session 根目录生成 `audit_trail.html`。
- 最终报告导航加 `Audit Trail` 链接；评审 UI 中每个历史 iteration 行加 `Compare with previous` 按钮跳转。

### F. `reporting.py`
- `generate_html_report` 新增参数 `audit_trail_path: Path | None = None`；非空时顶部导航渲染 Audit Trail 链接。

### 不需要改
- `providers.py`（保持单轮无状态）
- `scripts/extract_matching_rules.py`、`scripts/generate_semantic_rules.py`（规则拆分留给独立 PR）
- `MAKER_SYSTEM_PROMPT` 文案（本轮不做 prompt 优化）
- checker 任何接入人类反馈的路径

### 目录/持久化（现状已满足，无需改）
```
runs/review_sessions/{session_id}/
  iterations/
    000/  maker_cases / checker_reviews / human_reviews_latest
    001/  rewrite/merged_cases / checker/checker_reviews (合并后) / report/ 
          compare_iter_000_vs_001.html   ← 新增
  audit_trail.html                          ← 新增（聚合）
```

---

## 3.3 任务拆分

### Phase 1 — 需求 4 + 5（~20 行改动）
- [ ] `prompts.py`：CHECKER 独立性声明
- [ ] `prompts.py`：REWRITE 优先级声明
- [ ] `prompts.py`：`build_rewrite_user_prompt` 改结构化章节
- [ ] 冒烟：`artifacts/poc_two_rules`，跑 maker → checker → review-session 能启动不崩

### Phase 2 — 需求 6（case 级 rewrite + 合并 review）
- [ ] `pipelines.py::_rewrite_targets` 返回 `{rule_id: [case_id]}`
- [ ] `pipelines.py::run_rewrite_pipeline` 支持 case 级范围 + 未改动 case 原样保留
- [ ] `pipelines.py::run_checker_pipeline` 增加 `only_case_ids` + 继承上轮 review 合并输出
- [ ] 回归测试（poc_two_rules，标 1 个 case rewrite）：
  1. 只目标 case 的产物变化，同 rule 其他 case **字节级相等**
  2. checker 第二轮只审目标 case
  3. 最终 `checker_reviews.jsonl` 包含所有 case（未改的沿用上轮 review）

### Phase 3 — 需求 1 + 2（报告层，可并行）
- [ ] 新建 `audit_trail.py`：分歧检测 + HTML 渲染
- [ ] 新建 `case_compare.py`：side-by-side diff HTML
- [ ] `review_session.py` 每轮 rewrite 完成后生成 compare 文件
- [ ] `review_session.py` finalize 时生成 audit_trail.html
- [ ] `reporting.py` 顶部导航加 Audit Trail 链接
- [ ] 评审页每个历史 iteration 加 Compare 按钮
- [ ] 端到端冒烟：poc_two_rules 标 1 个 case rewrite → finalize → 打开报告验证：
  - Audit Trail 页（人造一条分歧能显示）
  - Compare 页（只显示被改的 case，side-by-side 渲染正确）
  - 主 report 正常

---

## 3.4 给 Sonnet 的交接摘要（可直接复制给 agent）

> **角色**：你是 Sonnet 4.6 执行 agent。项目路径 `F:/Develop/python/LME-Testing`，分支 `feature/code_optimization`。
>
> **任务**：实现本文档第 3.3 节 Phase 1 → Phase 2 → Phase 3 的全部 checklist。
>
> **关键决策**（已与用户确认，**不要再提问**）：
> 1. 分歧定义用 (b)+(c) 组合，见 3.1。
> 2. Compare 只展示被改的 case，side-by-side，字段见 3.1。
> 3. 规则拆分优化 / atomic / semantic / MAKER prompt **完全不碰**，留给独立 PR。
> 4. Checker 独立——**只改 prompt 文案，不给 checker 任何人类反馈或 session memory**。
> 5. Rewrite prompt 加 "human > checker" 优先级。
> 6. Case 级 rewrite，路线 A（结构化单轮），不改 `providers.py`。
>
> **必读**：本文档 3.2（技术设计）是唯一权威实现规范。重点文件锚点：
> - `lme_testing/prompts.py` — `CHECKER_SYSTEM_PROMPT`、`REWRITE_SYSTEM_PROMPT`、`build_rewrite_user_prompt`
> - `lme_testing/pipelines.py:454-462` — `_rewrite_target_rule_ids`（改签名）
> - `lme_testing/pipelines.py:498-534` — rewrite batch 组装
> - `lme_testing/pipelines.py:239-247` — 第二轮 checker 调用
> - `lme_testing/review_session.py:387` — iterations 目录结构
> - `lme_testing/reporting.py:137+` — `generate_html_report`
>
> **冒烟样本**：`artifacts/poc_two_rules/semantic_rules.json`。入口：
> ```
> python main.py maker --input artifacts/poc_two_rules/semantic_rules.json --output-dir runs/maker_poc
> python main.py checker --rules artifacts/poc_two_rules/semantic_rules.json --cases <maker output> --output-dir runs/checker_poc
> python main.py review-session --cases <maker output> --checker-reviews <checker output>
> ```
>
> **Phase 2 关键断言**：标 1 个 case rewrite 后，同 rule 其他 case 产物**字节级不变**；checker 第二轮只收到目标 case；合并后的 `checker_reviews.jsonl` 仍覆盖全部 case。
>
> **验收清单**：
> 1. Phase 1 三处 prompt 改动到位
> 2. Phase 2 case 级 rewrite + 增量 checker + review 继承合并行为正确
> 3. `audit_trail.html` 在 poc 中人造一条分歧能正确显示
> 4. `compare_iter_xxx_vs_yyy.html` 只显示被改 case、side-by-side 正常
> 5. 主报告导航含 Audit Trail；评审页历史 iteration 行含 Compare 按钮
> 6. poc_two_rules 端到端跑通
>
> **不要做**：
> - 不要重构未列在 3.2 的任何模块
> - 不要改 `providers.py`、`scripts/*`、`MAKER_SYSTEM_PROMPT`
> - 不要给 checker 引入 session memory 或 human feedback
> - 不要一次性提交，按 Phase 1 → 2 → 3 分步验证后再进入下一阶段
