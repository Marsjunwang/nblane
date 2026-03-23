# SKILL.md Format Reference

## Why this format matters

The agent that loads your SKILL.md will use it as a system prompt. The quality of the agent's output is directly proportional to the honesty and specificity of what you write here. Vague entries produce generic outputs. Specific entries produce useful ones.

## Sections

### Identity

Who you are, what domain you're in, where you're headed. One sentence for the North Star — make it concrete enough that you'd know if you hit it.

```markdown
- **Domain**: Robotics (Manipulation, Embodied AI)
- **Journey**: Year 1 of 5
- **North Star**: First-author paper at ICRA 2028, open-source project with 500+ stars
```

### Core Competencies

A table of skill areas with honest status ratings. This calibrates the agent's assumptions — it won't over-explain basics you already know, and won't assume mastery you haven't claimed.

Status options: `locked` | `learning` | `solid` | `expert`

### Skill Tree

A subset of your `skill-tree.yaml` shown inline. List only the nodes actively in play. Full detail lives in the YAML.

### Research Fingerprint

**The most important section for AI co-evolution.** This is where your taste lives. An agent that has read a good Research Fingerprint can:
- Identify weak points in a paper the way you would
- Write in a style you'd recognize
- Prioritize the questions you actually care about

Be specific. "I care about clean ablations" is okay. "I distrust any manipulation paper that doesn't show failure cases on real hardware" is better.

### Current Focus

Weekly-resolution state of what you're doing. Sync this with `kanban.md`. The agent uses this to avoid suggesting things you're already working on.

### Thinking & Communication Style

How you explain things. How you write. What language(s). This is how the agent matches your voice when you use it in `--mode write`.

### Growth Log

A time-ordered table. Append only, never delete. This is the receipts.

Use `nblane log name "event"` to append from the command line.

## agent-profile.yaml (optional)

Sits next to `SKILL.md` and holds a structured **Agent-side** model of
strengths, weaknesses, and working style (see product doc). When present,
`nblane context <name>` appends an **Agent profile (structured)**
block.

Template: `profiles/template/agent-profile.yaml`. Omit the file for legacy
behavior.

## Update Cadence

- **Weekly**: Current Focus, Kanban
- **Monthly**: Skill Tree, Core Competencies
- **Per milestone**: Growth Log, Influence & Output
- **Quarterly**: Research Fingerprint, Identity (North Star evolves)

## The rule about honesty

The system only works if SKILL.md reflects reality. It is not a resume. It is a prior. If you inflate it, the agent will make wrong assumptions and give you worse help. Mark things `locked` when they're locked. The log is how you prove you unlocked them.
