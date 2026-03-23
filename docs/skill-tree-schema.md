# Skill Tree Schema Guide

## Overview

A schema defines all possible nodes in a domain's skill tree. Think of it as the complete level map. Each person's `skill-tree.yaml` is a personal overlay that records which nodes they've lit.

Schemas live in `schemas/`. The current schema is `schemas/robotics-engineer.yaml`.

## Schema Structure

```yaml
schema_version: "1.0"
domain: "Robotics Engineer"

nodes:
  - id: ros2_basics          # unique identifier, used in skill-tree.yaml
    label: ROS2 Basics       # human-readable name
    level: 1                 # 1=foundation, 2=intermediate, 3=advanced, 4=expert
    category: middleware     # grouping for visualization
    requires: [linux_basics] # prerequisite node IDs (optional)
```

## Personal skill-tree.yaml Structure

```yaml
profile: "alice"
schema: "robotics-engineer"
updated: "2026-03-21"

nodes:
  - id: ros2_basics
    status: solid
    note: "completed 2025-09"

  - id: moveit2
    status: learning
    note: "working through manipulation tutorial"

  - id: sim2real
    status: locked
    note: "planned Q3 2026"
```

**You only need to list nodes you want to track.** Unlisted nodes are implicitly `locked`.

## Status Values

| Status | Meaning | Icon |
|--------|---------|------|
| `expert` | Deep, transferable mastery | ★ |
| `solid` | Can use reliably in real work | ● |
| `learning` | Actively working on it | ◐ |
| `locked` | Not started | ○ |

## Adding a New Domain Schema

Copy `schemas/robotics-engineer.yaml` as a starting point. Structure the nodes as a DAG (directed acyclic graph): foundation nodes at level 1, with `requires` pointing to their prerequisites.

Guidelines:
- Keep node IDs lowercase with underscores
- A node should represent a coherent skill that takes 1–8 weeks to reach `solid`
- Don't over-decompose — 40–80 nodes is a reasonable tree size
- The `requires` field is advisory (for visualization); full DAG enforcement is
  not the goal

## Validation (shipped)

`nblane validate` checks that node IDs in your `skill-tree.yaml` exist
in the referenced schema and that statuses are legal. It can **warn** when a
node is `solid` / `expert` but a listed prerequisite is still `locked` or
`learning`.

## Visualization (future)

`tools/visualize.py` (planned) will render the skill tree as a static SVG showing:
- Lit nodes (solid/expert) in color
- In-progress nodes with a partial fill
- Locked nodes in grey
- Dependency edges

For now, `nblane status` gives a text summary.
