# SKILL.md 格式说明

## 为何重要

加载你 `SKILL.md` 的 Agent 会把它当作系统提示。输出质量与你在文中写的
诚实度、具体度成正比。笼统描述 → 笼统回答；具体描述 → 有用回答。

## 章节

### Identity（身份）

你是谁、领域、去向。北极星用一句话写清，具体到你**能判断是否达成**。

```markdown
- **Domain**: Robotics (Manipulation, Embodied AI)
- **Journey**: Year 1 of 5
- **North Star**: First-author paper at ICRA 2028, open-source project with 500+ stars
```

### Core Competencies（核心能力）

技能域与诚实状态表。用于校准 Agent：已会的不会过度讲解，未宣称的熟练度
不会默认你已掌握。

状态取值：`locked` | `learning` | `solid` | `expert`

### Skill Tree（技能树）

从 `skill-tree.yaml` 摘一部分内联展示。只列**正在推进**的节点，完整内容在
YAML。

### Research Fingerprint（研究指纹）

**共进化里最重要的一节**，你的品味在这里。读过好的 Research Fingerprint
的 Agent 可以：

- 像你一样找论文薄弱点
- 用你认得出的风格写作
- 优先排你真正关心的问题

要具体。「我在意干净消融」可以；「我不信不展示真机失败案例的操作论文」更好。

### Current Focus（当前焦点）

周粒度在做什么。与 `kanban.md` 同步。Agent 据此避免重复建议你已在做的事。

### Thinking & Communication Style（思维与表达）

你怎么讲、怎么写、用什么语言。在 `--mode write` 时用于贴近你的声音。

### Growth Log（成长日志）

按时间追加的表。只增不删，作为证据。

命令行追加：`python nblane.py log <name> "事件"`

## agent-profile.yaml（可选）

与 `SKILL.md` 并列，用于**结构化**表达 Agent 侧对你强项、弱项与协作风格
的建模（产品手册中的 Agent profile）。存在时，`python nblane.py context
<name>` 会在输出中追加 **Agent profile (structured)** 区块。

模板见 `profiles/template/agent-profile.yaml`。不需要可删除该文件，行为与
旧版一致。

## 更新节奏

- **每周**：Current Focus、Kanban
- **每月**：Skill Tree、Core Competencies
- **里程碑**：Growth Log、Influence & Output
- **每季**：Research Fingerprint、Identity（北极星会演变）

## 诚实原则

只有 `SKILL.md` 反映真实，系统才有效。它不是简历，是**先验**。夸大则 Agent
假设错误，帮助变差。该锁就标 `locked`。日志用来证明你何时点亮了节点。
