先明确升级的起点

这个框架现在能做的事：

LME 文档 → 脚本提取规则 → maker 生成测试场景
         → checker 审核覆盖率 → 人工 review → rewrite → 报告

它的真实痛点不是”缺少 LLM-as-judge”或”marker 太浅”（那是 ChatGPT 对另一个框架的批评），而是以下几个实际问题。

一、规则提取层（最脆弱的环节）

现状： 规则提取是脚本驱动的，atomic_rules.json 的质量完全依赖脚本和人工，没有验证层。

升级方向：

在原始文档到 semantic_rules.json 之间加一个校验步骤：

文档 → 提取脚本 → atomic_rules.json
                 → [schema 校验]       ← 新增
                 → [规则去重/冲突检测]   ← 新增
                 → semantic_rules.json

具体可以做：

	•	定义 atomic_rule 和 semantic_rule 的 JSON Schema，提取后自动校验格式
	•	检测语义相似的重复规则（可以用 embedding 做相似度对比）
	•	对规则的 rule_type 字段做枚举约束，避免 maker 拿到错误类型后静默生成垃圾用例

二、Maker 的提示稳定性

现状： maker 调用的模型没有版本锁定，prompt 也没有版本化，换模型或改 prompt 会导致输出质量变化但没有基线对比。

升级方向：

	•	给 maker 的 prompt 加版本字段，记录在每次输出的 artifact metadata 里
	•	固定推荐模型（README 里目前完全没提用什么模型）
	•	加一个 POC 级的回归测试：用 poc_two_rules 跑两次，对比 checker 评分变化，超过阈值就报警

三、Checker 的覆盖逻辑

现状： checker 判断一个规则是否 fully_covered 的逻辑是：所有 required_case_types 都被 accept。这个设计本身是对的，但有一个盲区——checker 自己也是 LLM，它的判断可能前后不一致。

升级方向：

	•	对同一批用例跑两次 checker，比较结论是否一致，标记出 unstable 的判断
	•	对 checker 的输出加结构约束（如果还没有的话）：强制输出 JSON 格式，而不是自然语言，减少解析错误
	•	在报告里把 checker 的置信度区分显示：fully_covered / partially_covered / uncertain

四、Human Review 的协作能力

现状： review session 是本地 HTTP server，单人使用，无共享状态。

升级方向（按优先级）：

短期： 把 review 状态持久化到文件（目前看起来已经有 draft 保存），确保中途关闭浏览器不丢失进度。

中期： 支持导出/导入 review 结果，让多个 reviewer 可以异步各自审核，再合并（类似 Git merge review 的思路）。

长期（如果团队用）： 把 review session 改成可部署的 web 服务，加简单的多用户标注，每条用例可以看到不同 reviewer 的决策分歧。

五、框架自身的测试

现状： 有 tests/ 目录但没有 CI，没有任何自动化保障。这是一个测试工具，但自己没有测试——风险最高。

升级方向：

加 GitHub Actions，至少跑：

	1.	用 poc_two_rules 做端到端冒烟测试
	2.	对核心模块（pipeline、reporting、review session）加单元测试
	3.	PR 时自动跑，防止改坏流程

六、报告的可用性

现状： 最终输出是 HTML 报告，包含 Summary / Maker Readable / Checker Readable 三个视图。

升级方向：

	•	加规则覆盖热力图：哪些 rule_type 的覆盖率最低，一眼看出
	•	加历史对比：本次 checker 通过率 vs 上次，反映 maker prompt 改进的效果
	•	支持导出为 JSON/CSV，方便接进外部 BI 或做进一步分析

优先级建议

如果只能做一件事，先做规则提取层的 schema 校验——因为它在整个流水线的最上游，输入质量决定了后面所有环节的上限。其次是框架自身的 CI，因为没有它，任何代码改动都是在裸奔。

其他的升级（checker 稳定性、多人 review、报告增强）可以根据实际使用频率决定顺序。​​​​​​​​​​​​​​​​