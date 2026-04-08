## 一、系统定位

这个 repo 现在更像一个**测试设计系统**，不是完整的**测试执行系统**，也还谈不上真正的**测试编排平台**。README 直接把它定义为 “document-driven test design prototype”，当前主流程是：抽规则、归一化成 `atomic_rule` / `semantic_rule`、maker 生成结构化测试场景、checker 审查质量和覆盖、人工 review、rewrite、再出 HTML report。主入口也集中在 CLI、pipelines、review session、workflow session、reporting、provider adapter 这些设计与审核模块上。

它当前最容易被高估成“AI 自动化测试框架”。原因是 `semantic_rule` 已经有 `execution_mapping`、`observable_outputs`、`system_events`、`dsl_assertions` 这些字段，看起来很像能直接接执行层；但设计文档明确说 `semantic_rule` 是“语义层和半执行层”，要“对未来可执行测试保持足够接近，但不直接等于测试脚本”。也就是说，这些更像桥接结构，不是现成执行器。

它实际还缺的关键能力，是：真正的执行引擎、环境准备与编排、系统驱动层、运行时 oracle、执行结果回流与稳定的可观测性。这些在公开主流程和入口说明里都没有出现。

## 二、升级核心问题

### 1. 如何从“测试设计”补到“测试执行”

最关键的一跳，不是继续强化 maker/checker，而是新增一个**执行中间层**。
建议把 `semantic_rule` 编译成统一的 `ExecutableScenario` 或类似 IR，里面固定表达：

* preconditions
* inputs / test data
* actions
* expected events / observable outputs
* deterministic assertions
* cleanup

这样 `execution_mapping` 和 `dsl_assertions` 才真正变成执行入口，而不是停留在表达意图。这个方向和仓库已有 rule model 是顺的，因为设计文档已经把 `execution_mapping` 定义成“连接未来可执行测试层的桥接字段”。

然后在 IR 下面接 **runner adapter**。不要一开始追求全能，先选一个最重要的执行域，例如 API / service，或者如果你的真实场景是 FIX，就先做 FIX runner。每个 runner 统一实现 `prepare -> execute -> observe -> assert -> cleanup` 接口。这样系统才会从“AI 设计测试”升级成“AI 驱动测试设计 + 可运行执行”。

### 2. 如何从“LLM 驱动”补到“确定性执行 + 确定性校验”

这个 repo 当前已经做了很多约束：maker 必须对每个输入规则返回恰好一个结果，每个 required case type 恰好一个 scenario；checker 必须对每个输入 case 返回恰好一个 review，且 `semantic_rule_id` 必须匹配。`pipelines.py` 还把不同 `rule_type` 映射成 required/optional case types，再直接传给 maker，避免模型自己猜。

但这些只是把 **LLM 输出收紧**，不是把系统变成确定性系统。升级时应该把判断拆成两类：

* **继续允许 LLM 做的事**：规则归一化、场景草拟、歧义提示、测试设计建议
* **必须确定性化的事**：字段格式校验、状态转换检查、时间窗口判断、计算结果校验、枚举合法性、覆盖统计、traceability 验证

尤其对 `data_constraint`、`deadline`、`calculation`、`enum_definition` 这类结构化规则，优先把 oracle 做成代码而不是再交给模型二次判断。因为仓库的 rule_type 已经分得很细，这正好可以作为“哪些先 deterministic 化”的切入点。

### 3. 如何从“本地工具/原型”补到“团队可协作系统”

README 里把 `review_session.py` 明确成 **local HTTP review session service**，页面可以保存 draft、提交 review、触发 `rewrite -> checker -> report`、finalize 并跳转报告。这很适合 PoC 和单机验证，但不适合团队级协作。

升级方向应该是把 review-session 服务化，至少补这几层：

* 身份与权限
* 审核任务分派
* 多人并发审查
* 审计日志与决策历史
* 评论线程 / 差异对比
* 版本冻结与回滚

也就是说，review 要从“本地页面”升级成“工作流系统的一环”。

### 4. 如何从“设计 coverage”补到“执行 coverage”

当前 repo 的 coverage 主要是**设计层 coverage**：一条规则只有在其所有 required case types 都被 checker 接受时，才算 fully covered。这个设计在测试设计阶段是合理的，而且 `pipelines.py` 已经把 `rule_type -> required_case_types` 机制固化了。

但平台化后至少要拆成四层：

* **document coverage**：文档规则有没有被抽出来
* **design coverage**：规则有没有被设计成场景
* **executable coverage**：设计出的场景里有多少能真正运行
* **runtime coverage**：运行后有多少通过，失败分布是什么

否则你只能知道“设计上好像覆盖了”，不知道“系统实际上有没有被测到”。

## 三、升级优先级

### 基础层：不做就无法继续升级的能力

**1. 固化 rule schema 与版本管理**
现在 `atomic_rule` / `semantic_rule` 已经是整个系统的主干，设计文档还显式建议 `semantic_rule.version = 1.0`。下一步应该把 schema 抽成正式契约，单独版本化、做兼容规则和回归样本。否则一旦改 prompt、换模型、换字段，后面 maker/checker/execution 都会一起抖。

**2. 建立 benchmark 与 regression 评测**
仓库现在推荐从 `artifacts/poc_two_rules/semantic_rules.json` 开始，说明它已有最小样例入口。下一步应该扩成正式 benchmark：人工维护一批 gold `semantic_rule`、gold scenarios、gold review 结果，每次改模型或 prompt 都先跑回归。

**3. 把文档抽取变成可审计 ETL**
设计文档和脚本指南都强调 `PDF -> pages -> clauses -> atomic_rule -> semantic_rule` 的分层，并列出 `pages.json`、`clauses.json`、`atomic_rules.json`、`semantic_rules.json` 等中间产物。升级时要把这些中间层全部持久化、可 diff、可追溯。这样后续执行层一旦出问题，才能定位到底是 PDF 解析漂了，还是 semantic normalization 漂了。

这层做完，系统的质变是：从“容易漂的原型链路”变成“可追责、可回归的设计流水线”。

### 闭环层：让系统真正形成可运行闭环的能力

**1. 新增 execution IR / compiler**
把 `semantic_rule` 编译成内部可执行中间表示，而不是直接让 LLM 产出最终脚本。这样可以把设计层和执行层隔开，减少后续 runner 扩展成本。证据基础是仓库已经有 `execution_mapping` 和 `dsl_assertions` 这些桥接字段。

**2. 先接一个最小 runner**
建议先做一个垂直场景最强相关的 runner，而不是全栈支持。这样能尽快验证“从 rule 到 runnable scenario”这条主链路是否成立。

**3. 新增 deterministic oracle 层**
checker 现在负责的是“场景设计质量与覆盖判断”，不是系统运行后的真 oracle。执行层必须单独引入确定性断言模块。仓库现有 checker 约束清楚说明了这一点：它返回的是结构化 blocking 与 coverage 字段，不是最终业务执行真值。

这层做完，系统的质变是：从“设计闭环”变成“设计 + 运行闭环”。

### 平台层：产品化、治理、可观测性、扩展性能力

**1. review-session 服务化**
把 local HTTP 工具升级成团队协作服务。

**2. 多模型策略层**
现在 provider 是 OpenAI-compatible adapter with retry support，适合 PoC。平台化时应把 maker/checker/rewrite 的模型选择独立出来，支持按 rule_type 路由、A/B、灰度、回滚。

**3. 可观测性与治理**
现在有 logging 和 recoverable retry，但平台还需要更完整的指标：抽取漂移率、rule-to-scenario 转化率、checker block 率、人审重写率、可执行率、执行通过率。仓库当前只有基础日志和 retry，不足以支撑平台治理。

这层做完，系统的质变是：从“可跑的闭环”变成“可维护的平台”。

## 四、风险与取舍

最容易浪费时间的方向，是**继续堆 prompt 和 maker/checker 复杂度**，把它做成一个更贵的“测试设计系统”。因为它当前最大缺口不在设计层，而在执行层和确定性 oracle 层。仓库已经把设计层约束做得不算弱了：required case types、exactly-one constraints、schema validation、human review、retry/resume 都已经在。继续只加这层，收益会递减。

第二个不该太早做的，是“平台化大一统”。在还没有 execution IR 和最小 runner 前，就去做复杂权限、多租户、重前后端改造，容易把项目拖死。因为仓库当前连正式 release 都没有，主页显示只有 2 commits、0 stars、0 forks，而且 README 推荐从 two-rule POC 起步。现阶段更需要验证主链路，而不是先堆平台壳子。

第三个关键取舍是：**哪些能力该优先确定性化**。
我会优先做：

* data constraints
* deadlines
* calculations
* enum validations
* traceability / coverage accounting

而 workflow、复杂歧义归纳、测试设计提示、自然语言 review comment 这类仍可保留 LLM 辅助。这个取舍直接利用了现有 rule_type 分类。

如果只能做一个最小版本，最该优先验证的是：

**`semantic_rule -> execution IR -> 一个 runner -> deterministic oracle -> execution report`**

只要这条链跑通，系统才真正迈出“从测试设计到测试执行”的那一步。

## 五、输出格式

### 1. 当前阶段判断

它现在是**文档驱动的测试设计/审核原型**，不是完整测试执行系统。

### 2. 最大短板

最大短板不是 maker/checker 不够复杂，而是**没有执行闭环**，同时关键质量仍重度依赖 LLM 和人工 review。

### 3. 分层升级方案

基础层：schema 版本化、benchmark、可审计抽取 ETL。
闭环层：execution IR、最小 runner、deterministic oracle。
平台层：review-session 服务化、多模型策略、可观测性和治理。
这些层次都能从仓库当前的 rule model、pipeline、review-session 和 provider 结构自然延伸出来。

### 4. 最容易走偏的方向

继续只强化 prompt / schema / checker 复杂度，而不补执行层；或者在主链路未跑通前过早做重平台化。

### 5. 最小可行升级路径

先稳 schema 和抽取，再做 benchmark，然后新增 execution IR，接一个 runner，最后引入 deterministic oracle 和 execution report。

### 6. 最终建议

**别把它升级成“更复杂的 maker/checker 系统”，而要把它升级成“以 rule model 为核心、以 execution IR 为桥、以 deterministic oracle 为落点”的测试平台。** 这是它从 PoC 走向可试点方案的最短路径。
