**“新 roadmap vs 当前 docs 体系” 对齐矩阵**。

---

## 一、总览结论

当前 docs 体系已经覆盖了新 roadmap 的**大部分方法论骨架**，尤其是：

* phase-based roadmap
* acceptance gates
* model/prompt governance
* architecture boundaries
* testing governance
* prompt lifecycle
* execution-oriented implementation tasks

但还没有做到对 `ROADMAP.pdf` 的**逐 task 显式对齐**。
最明显的缺口在三类：

1. **step integration 的专项落点还没单独成文**
2. **paragraph_id / stable source anchor 还没作为正式硬约束写透**
3. **一些新 roadmap 很强的“任务执行协议”虽然被吸收进 `implementation_plan.md`，但还没显式反向回填到其他 docs 的交叉引用里**

---

## 二、对齐矩阵

### A. Phase 1 — Foundation Hardening

| 新 roadmap 任务                            | 当前覆盖文档                                                                     | 覆盖度 | 说明                                                                                                                  | 建议动作                                                                                         |
| --------------------------------------- | -------------------------------------------------------------------------- | --: | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| 1.1 Rule Schema Validation              | `roadmap.md`, `acceptance.md`, `architecture.md`, `implementation_plan.md` |   高 | 规则 schema、validation gate、phase 1 任务都已覆盖，但 PDF 里那种“先读 input contract、输出 structured report、logs/ 写报告”的执行细节没有完全逐条回填。  | 在 `acceptance.md` 增补“rule validation report”作为显式 evidence                                    |
| 1.2 Prompt and Model Version Locking    | `model_governance.md`, `prompt_lifecycle.md`, `implementation_plan.md`     |   高 | prompt/version/provider metadata、adoption workflow、rollback 都已覆盖。PDF 里的 `config/model-config.json` 这种具体落点没有被固定采用。   | 保持抽象，不锁死路径；在 `README` 或 `implementation_plan` 加推荐位置                                          |
| 1.3 Framework CI                        | `acceptance.md`, `implementation_plan.md`, `roadmap.md`                    |   高 | baseline CI、schema validation、smoke flow 已覆盖。PDF 更强调 stub provider / fixtures 的执行型细节。                               | 在 `implementation_plan.md` 增一条“stub provider / fixture-first CI”建议                           |
| 1.4 Structured Paragraph ID Integration | `architecture.md`, `testing_governance.md`, `implementation_plan.md`       |   中 | 我们已经吸收了“stable source anchor / paragraph-level traceability”的思想，但还没像 PDF 那样把 `paragraph_id` 上升成正式主键并写到所有相关 docs 中。  | 这是优先补项：更新 `architecture.md`、`acceptance.md`、`testing_governance.md`、`implementation_plan.md` |

### B. Phase 2 — Planning / BDD / Review / Governance

| 新 roadmap 任务                                     | 当前覆盖文档                                                             | 覆盖度 | 说明                                                                                                                         | 建议动作                                                                      |
| ------------------------------------------------ | ------------------------------------------------------------------ | --: | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 多文档类型 ingestion                                  | `roadmap.md`, `implementation_plan.md`, `architecture.md`          |   高 | 我们已覆盖多 document classes、parsing strategy、failure modes。PDF 更具体到 domain package/config。                                     | 保持抽象，不直接锁死目录；可在未来 `step_integration_plan.md` 或 `architecture.md` 附录里给参考结构 |
| BDD style learning                               | `roadmap.md`, `implementation_plan.md`                             |  中高 | 已覆盖 style learning 方向，但还没有单独文档承接“团队风格学习”的专项规则。                                                                             | 新增 `docs/step_integration_plan.md` 时重点吸收                                  |
| Step definition registry                         | `roadmap.md`, `implementation_plan.md`                             |  中高 | 已有方向和任务，但没有专门文档落点。PDF 这部分非常强。                                                                                              | 新增 `docs/step_integration_plan.md`                                        |
| Review export / import / merge                   | `testing_governance.md`, `implementation_plan.md`, `acceptance.md` |   高 | 已覆盖 review package exchange、merge、conflict。PDF 的 reviewer JSON merge 例子更具体。                                                | 在 `acceptance.md` 补一个更具体的 merge evidence 模板                               |
| Governance layer / audit trail / change tracking | `testing_governance.md`, `acceptance.md`, `model_governance.md`    |  中高 | audit trail、change impact、rollback、review records 的思想都已覆盖，但 PDF 里那种 `governance/` 目录和 append-only audit trail 还未形成明确推荐结构。  | 建议新增 `docs/index.md` 或 repo structure note，给出推荐落点但不强制路径                   |
| Phase 2 gate                                     | `acceptance.md`                                                    |   中 | 有 phase exit criteria，但没有按 PDF 那样明确列“至少一个非 LME 文档端到端、BDD dry-run、audit trail 至少三条记录”。                                      | 把这些具体门槛补进 `acceptance.md` 的 Phase 2                                       |

### C. Phase 3 — Enterprise AI Testing Platform

| 新 roadmap 任务                    | 当前覆盖文档                                                             | 覆盖度 | 说明                                                                                                                          | 建议动作                                                                                |
| ------------------------------- | ------------------------------------------------------------------ | --: | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Domain-agnostic pipeline        | `roadmap.md`, `architecture.md`, `implementation_plan.md`          |   高 | 已覆盖 domain abstraction、多文档、domain config 概念。PDF 更具体到 `--domain {name}`。                                                     | 在 `implementation_plan.md` 增加“CLI invocation contract may include domain selection” |
| Auto Step Definition Generation | `roadmap.md`, `implementation_plan.md`                             |   中 | 已作为长期 optional / future direction，但 PDF 把它列成明确 Task 3.2。                                                                    | 先不要主线化；写入未来 `step_integration_plan.md`                                              |
| CI/CD Quality Gate              | `acceptance.md`, `model_governance.md`, `implementation_plan.md`   |   高 | gate threshold、promotion blocking、regression governance 已有骨架。PDF 的 baseline/current compare、exit code 0/1、PR comment 更执行化。  | 在 `implementation_plan.md` 增一个 gate subtask 示例                                      |
| Cross-Run Regression Analysis   | `testing_governance.md`, `acceptance.md`, `implementation_plan.md` |   高 | drift/regression/trend metrics 已覆盖，PDF 给了更明确的 time-series 指标。                                                               | 补到 `testing_governance.md` 的 minimum metrics 中                                      |
| Self-Improving Prompt System    | `prompt_lifecycle.md`, `model_governance.md`                       |  中低 | 我们刻意把它降级成 optional / exploratory，这是合理的，因为当前 repo 阶段还不适合主线化。                                                                 | 保持降级，不建议升为主线                                                                        |
| Phase 3 gate                    | `acceptance.md`                                                    |   中 | 有长期 exit criteria，但没像 PDF 那样把“至少两个 domain、10 历史 run、2 reviewer、多用户 session”等写得这么硬。                                          | Phase 3 接近时再硬化，不必现在全写死                                                              |

---

## 三、按文档看：哪些已经对齐，哪些没对齐

### `README.md`

**覆盖度：中**

它已经作为项目入口足够清楚，但没有显式反映新 roadmap 的执行型特征，例如：

* LLMs read roadmap as execution context
* task-contract discipline
* phase gate sign-off mentality

**建议：**
只补一小段“Execution model”，不要把 README 写重。

---

### `docs/roadmap.md`

**覆盖度：中高**

已覆盖战略主线，但和 PDF 相比有两个差别：

* 我们更抽象，更像战略路线图
* PDF 更像“给 LLM 读的执行蓝图” 

**建议：**
保持现在的抽象层，不要把它改成 task 脚本。
但要补三个显式条目：

* paragraph_id / stable source anchor
* BDD style learning + step registry
* quality gate + regression analysis

---

### `docs/implementation_plan.md`

**覆盖度：高**

这是最贴近新 roadmap 的文档。
它已经承接了：

* Task ID
* Input / Output Contract
* Validation
* Acceptance evidence
* Out-of-scope
* phase-based execution tasks

但仍有三个可补点：

1. 更明确引用 phase gate sign-off 逻辑
2. 更明确写“缺 prerequisite 就停止，不得 fabricate”
3. 加入 paragraph_id 作为全链路显式要求

---

### `docs/acceptance.md`

**覆盖度：中高**

有 phase gate 和 evidence，但还没完全吸收 PDF 里的**更硬、更可量化**的 exit criteria，例如：

* Phase 2: 至少一个非 LME 文档类型端到端成功
* generated `.feature` dry-run 通过
* governance audit trail 至少三条 run
* Phase 3: 两个 domain、10 历史 run、2 reviewers、多用户 review 体验等

**建议：**
这是最值得更新的文件之一。

---

### `docs/model_governance.md`

**覆盖度：高**

大方向已对齐：

* provider abstraction
* prompt versioning
* benchmark policy
* rollout / rollback
* structured output policy

但 PDF 强调一个非常实际的点：

**所有 prompts/config/schema 都必须是 repo-readable，不能依赖对话上下文。** 

我们虽然表达过类似意思，但还可以更明确。

**建议：**
补一个小节：`Repository-readable context requirement`。

---

### `docs/agent_guidelines.md`

**覆盖度：高**

已非常接近 PDF 的 LLM execution rules。
尤其是：

* 不要 silently 扩 scope
* 不要 fabricate missing prerequisites
* 必须更新 docs/tests/schema/prompt references

但还没像 PDF 那样明确写：

* “Before writing any code, identify task ID”
* “Read Input Contract”
* “Read Acceptance Criteria”
* “Check prior phase gate sign-off”
* “Session must end with PASS/PARTIAL/FAIL self-evaluation”

**建议：**
这是另一个非常值得小幅增强的文件。

---

### `docs/architecture.md`

**覆盖度：中高**

它比 PDF 强在系统边界清晰，但还没完全吸收：

* paragraph_id/stable source anchor 作为核心 traceability 主键
* BDD style learner / step registry / gap analysis 这些更务实的桥接层

**建议：**
补“Traceability Key Strategy”和“BDD-to-Step Bridge Layer”。

---

### `docs/testing_governance.md`

**覆盖度：高**

它已经很接近 tester 视角，覆盖了：

* review
* confidence
* failure analysis
* pre/post validation
* incremental / parallel / recovery / metrics

它和 PDF 的差距主要在于：

* PDF 的 audit/change-tracking 更具体
* PDF 的 diff report / governance directory 更实操化

**建议：**
在 testing governance 里补“minimum governance artifacts”。

---

### `docs/prompt_lifecycle.md`

**覆盖度：高**

它已经很好地吸收了测试视角和 PDF 中关于 prompt 资产的核心精神。
最大的缺口只在于：

* candidate prompt 不自动晋升
* applied candidate prompt 必须进 audit trail
  这两点可以写得更直白。 

---

### 缺失文件：`docs/step_integration_plan.md`

**覆盖度：缺失**

这是最明确的缺口。
因为 PDF 在这部分非常强，当前 docs 体系还没有一个专门落点承接：

* style learning
* step registry
* step mapping
* gap analysis
* `@needs-implementation`
* stub generation
* execution handoff bridge 

**建议：**
这是下一份最该补的文件。

---

## 四、优先更新顺序

如果现在要做“真正对齐新 roadmap”的文档更新，我建议顺序是：

### P0

1. `docs/acceptance.md`
2. `docs/agent_guidelines.md`
3. `docs/implementation_plan.md`

因为这三份最直接承接新 roadmap 的执行逻辑、phase gate 和 task contract。

### P1

4. `docs/architecture.md`
5. `docs/model_governance.md`
6. `docs/testing_governance.md`

因为这三份需要吸收 paragraph_id、repo-readable context、audit/change tracking 等增强项。

### P2

7. 新增 `docs/step_integration_plan.md`
8. 再小修 `docs/roadmap.md`
9. 最后微调 `README.md`

---

## 五、一句话结论

**当前 docs 体系已经覆盖了新 roadmap 的大部分骨架，但还没有完成“逐 task、逐 gate、逐 deliverable”的正式对齐；最关键的缺口是 `acceptance.md`、`agent_guidelines.md`、`implementation_plan.md` 的细化，以及新增 `step_integration_plan.md` 来承接 BDD/step bridge。**