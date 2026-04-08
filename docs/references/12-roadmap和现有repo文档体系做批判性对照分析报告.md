## 总体判断

这份新 roadmap 的最大优点是：**它比我们前面整理的文档更像“可直接驱动 LLM/Agent 按任务执行的实施蓝图”**。它一开始就把文档目的写成“给 LLM 作为执行上下文”，并要求每个任务都带 Input Contract、Output Contract、Acceptance Criteria、自检清单和 phase gate，这一点非常强。

但它的主要问题也很明显：**它把很多“长期应该有的能力”过早收敛成非常具体的目录结构、文件名、实现路径和任务序列**。这对执行型 Agent 很友好，但对一个仍处于原型到试点过渡期的 repo 来说，会带来一定的架构锁死和维护负担。

一句话说：

**这份 roadmap 更强于“任务执行编排”，我们之前那套更强于“系统分层和治理骨架”。最优方案不是替换，而是把它降解吸收成“执行层附录”，而不是直接取代主架构文档。**

---

## 它比现有方案强的地方

### 1. 对 LLM/Agent 非常友好

这是它最突出的优势。
它明确规定：

* 实施前先识别 task ID
* 先读 Input Contract
* 必须输出 Output Contract 指定文件
* 必须自评 Acceptance Criteria
* 缺前置依赖就停止，不得伪造输入
* 跨模型执行时，所有 prompt/config/schema 都必须落在仓库文件里，而不能依赖对话上下文

这比我们之前的 `roadmap + acceptance + agent_guidelines` 组合更“可操作”。
我们之前的文档更像治理体系，这份更像“任务执行协议”。

**建议吸收：**
把它这套 `Input Contract / Output Contract / Acceptance Criteria / Self-evaluation` 四件套，纳入 `docs/agent_guidelines.md` 和 `docs/acceptance.md`。

### 2. Phase 和 task 粒度非常落地

它不是只说“短期做 schema 和 CI”，而是直接拆到：

* Task 1.1 Rule Schema Validation
* Task 1.2 Prompt and Model Version Locking
* Task 1.3 Framework CI
* Task 1.4 Structured Paragraph ID Integration

后面又细化到：

* 多文档类型 ingestion
* BDD style learning
* step definition registry
* checker stability layer
* multi-user review
* governance layer
* domain packages
* auto step definition generation
* quality gate
* regression analysis
* prompt optimizer

这比我们之前的 phase 文档更适合直接开干。

**建议吸收：**
不要把它原样塞进 `docs/roadmap.md`，但可以新增一个：

* `docs/implementation_plan.md`
  或者
* `docs/task_breakdown.md`

主 roadmap 讲方向，这份讲任务。

### 3. paragraph_id 作为核心 traceability 主键，这个很强

它把 `paragraph_id` 上升成贯穿系统的统一追踪键，要求在 rule、maker、checker、report、step stub 里全链路传播，还要求 uniqueness check 和报告可排序。

这个比我们之前文档里泛泛说“要 traceability”更落地。
它把 traceability 从原则变成了具体机制。

**建议吸收：**
这是最值得直接采纳的内容之一。
应该补到：

* `architecture.md`
* `acceptance.md`
* `testing_governance.md`

### 4. 对 BDD 风格学习和 step registry 的桥接设计更务实

我们之前提过“normalized BDD → step mapping → execution-ready contract”，但偏架构。
这份 roadmap 进一步具体化了：

* 从现有 `.feature` 里学习团队风格
* 输出 `template-profiles.json`
* 生成 `style-guide.md`
* 解析现有 step definitions，生成 `step-registry.json`
* 生成 diff report 标出 matched / new steps
* 新步骤打 `@needs-implementation`
* 长期再自动生成 stub step definitions

这套桥接路径很适合企业里的现实落地，比直接谈“execution integration”更接地气。

**建议吸收：**
大部分应该保留，但放进：

* `roadmap.md` 中期/长期
* `step_integration_plan.md`
  而不是全塞在主 README 或 architecture 主干里。

---

## 它相对现有方案的不足

### 1. 过早把实现形态写死

它很早就指定了很多具体路径和文件结构，比如：

* `config/schemas/...`
* `tests/bdd/learned/template-profiles.json`
* `tests/bdd/step-registry.json`
* `governance/audit-trail.md`
* `tests/bdd/diff-reports/`
* `tests/bdd/steps/generated/`
* `domains/{domain-name}/domain-config.json`

这对立即执行很方便，但也意味着：

* 一旦 repo 真实结构演化，路线图会很快过时
* 文档和实现的耦合度变高
* 你会被目录结构反过来绑架

而我们之前那套文档的优点，是保留了足够的抽象层，不容易过早锁死。

**建议：**
保留“应该有什么能力与输出”，弱化“必须放在哪个路径”。

### 2. 有些中后期能力写得过早、过满

比如 Phase 3 同时推进：

* domain-agnostic pipeline
* auto step definition generation
* CI/CD quality gate
* cross-run regression analysis
* self-improving prompt system

这些方向都对，但对当前 repo 来说，后两个尤其容易变成“平台化愿景优先于基础质量”：

* `prompt_optimizer.py`
* 全自动 prompt 改进候选系统

这类功能很容易在数据还不够、治理还不稳时，做成复杂但不可靠的层。

**建议：**

* `quality gate` 和 `regression analysis` 保留
* `self-improving prompt system` 明确降级为探索项或 Phase 3 optional

### 3. 对“deterministic vs LLM-assisted”边界不如我们现有体系清楚

新 roadmap 很强于任务编排，但它整体仍偏“让 LLM 做更多事，再加 gate”。
相比之下，我们已有文档更明确强调：

* 哪些责任必须 deterministic
* 哪些只是 LLM-assisted
* 模块边界不能被 provider logic 污染

新 roadmap 里虽然也要求 schema/config/prompt 文件化，但在方法论上没有我们现有体系那么强调“系统边界和责任归属”。

**建议：**
用我们的 `architecture.md` 和 `model_governance.md` 继续做主骨架，不要被这份 roadmap 的执行细节替代掉。

---

## 取长补短：推荐怎么合并

## 直接采纳

这些我建议几乎原样吸收：

* `paragraph_id` 贯穿式追踪主键。
* Task 级 `Input Contract / Output Contract / Acceptance Criteria` 模式。
* `providers_stub.py + fixture-based e2e smoke` 这种 CI 设计。
* `BDD style learning + step registry + diff report + @needs-implementation` 这条桥接链。
* `checker_stability` 的多次运行和 variance 标记机制。
* `quality gate` 和 `cross-run regression analysis`。

## 修改后采纳

这些方向对，但表达和落点要改：

* 多文档 ingestion：保留能力目标，不要过早锁死 adapter 细节和目录结构。
* multi-user review：保留“export/import/merge/conflict”逻辑，但先弱化“共享网络盘并发”等具体部署假设。
* governance 目录：保留 audit/change tracking 思想，但不一定全都先用 `.md` 固定。
* domain packages：保留 `--domain` 和 domain config 设计，但目录和命名可抽象一点。

## 延后采纳

这些值得有，但不该现在就当主线：

* auto step definition generation。
* self-improving prompt system / prompt optimizer。

它们更适合放到：

* `roadmap.md` 长期 optional
* `prompt_lifecycle.md` 的 future section
  而不是当前执行主线。

## 不建议原样采纳

* 把最终目录树完全写死成“end state”。
* 把所有 task 都要求固定文件名和路径。
* 让主 roadmap 直接承担“执行脚本级蓝图”角色。

因为这样会让文档维护成本太高，而且一旦实现偏离，文档很快失真。

---

## 推荐的文档落点

### `docs/roadmap.md`

保留主方向和阶段目标。
吸收：

* paragraph_id
* style learning / step registry / quality gate / regression analysis 的阶段目标
  不要吸收太多具体文件路径。

### `docs/acceptance.md`

强烈建议吸收：

* task 级 Input Contract / Output Contract / Acceptance Criteria 模式
* phase gate sign-off 要求
* checker stability、quality gate、regression evidence 的验收项

### `docs/architecture.md`

吸收：

* paragraph_id 作为正式 traceability 主键
* BDD style profile、step registry、ExecutableScenario 之间的关系
* domain package / domain config 的抽象概念
  不要吸收具体目录树。

### `docs/model_governance.md`

吸收：

* model-config 文件化
* prompt 文件化
* checker_stability 配置块
* different LLMs must rely on repo-readable context 的原则。

### `docs/testing_governance.md`

吸收：

* audit trail
* diff reports
* matched/new steps
* governance/change tracking 思想
* multi-review conflict handling

### `docs/prompt_lifecycle.md`

吸收：

* candidate prompt addendum 不自动晋升
* prompt version change 必须进 audit trail。

### 建议新增

我建议再新增一份：

* `docs/implementation_plan.md`

专门承接这份新 roadmap 最有价值的部分：
**把 phase 分解为 task，并给出 Input / Output / Acceptance 合同。**

这样做的好处是：

* 主文档保持稳定
* 执行文档可逐步演化
* 很适合 AI agent

---

## 一句话结论

**这份新 roadmap 适合做“执行层蓝图”，不适合替代“架构与治理主文档”；最佳做法是保留我们现有文档体系做骨架，再把它最强的 task-contract、paragraph_id、BDD bridge、quality gate、regression 这些内容吸收进 acceptance / implementation_plan / step integration 相关文档。**