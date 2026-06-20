# Project Board Guide

Project Board is the internal project case page. It connects goals, Kanban tasks, evidence, research sources, milestones, experience cases, and outputs.

## When To Use It

- A piece of work has grown beyond a single Kanban card and needs longer-term tracking.
- You need to know which tasks, evidence rows, sources, or outputs belong to the same project.
- You want to split a project into visible milestones.
- You want to review how project progress, task completion, and evidence capture fit together over a period of time.

## Reading The First Screen

The compact summary bar combines project status counts and ownership gaps:

- Active / Paused / Completed / Archived: project counts from `project-board.yaml`.
- Unassigned tasks: Kanban tasks without a project owner.
- Unassigned evidence: reviewed evidence rows without a project owner.
- Current-goal projects: projects linked to the current goal.

If unassigned tasks or evidence are non-zero, handle those gaps first. Dashboard, Evidence Review, and project reviews become more useful when ownership links are complete.

## Recommended Workflow

1. Create a project case with status, kind, visibility, and summary.
2. Link the current goal, Kanban tasks, evidence, research sources, and outputs.
3. Add milestones when the project has visible checkpoints, then attach the relevant tasks to those milestones.
4. Use the create-task action for execution work that should live on Kanban.
5. Check the timeline to see whether the project, tasks, and milestones sit in the right time window.
6. Return to Dashboard or Evidence Review to check for remaining ownership gaps.

## Timeline

The timeline is the main Project Board view. Each row is a project: project context on the left, tasks and milestones on the right.

- Scroll to zoom the time range.
- Double-click to reset zoom.
- Right-click to delete supported items.
- In-progress tasks, done tasks, archived tasks, milestones, and today are shown with separate legend markers.
- Tasks without dates are not shown on the timeline; the page reports how many were hidden.

Review mode lets you inspect project progress inside a date window. Set start and end dates to focus on a week, month, or project phase review.

## Project Info

Click a project row to view or edit details. Common fields are:

- Status: `active`, `paused`, `completed`, or `archived`.
- Kind: internal, research, work, side project, or learning.
- Visibility: private internal work or a public candidate.
- Time range: the expected project window.
- Summary and notes: why the project exists, current judgment, and follow-up context.

Project Board is still an internal workflow. Setting visibility to public does not publish a public project page; public-facing output is managed by Output Studio and Public Build.

## Linked Refs

Linked refs mean "this project owns or produced this item." They do not copy source content.

- Goals explain why the project exists.
- Kanban tasks define execution ownership.
- Evidence rows are reviewed facts owned or produced by the project.
- Research sources include papers, URLs, imported material, and source inbox items.
- Experience cases support the project story.
- Outputs include articles, public drafts, or other deliverables.

AI-suggested refs only prefill the form. They are not saved until you review them and save the project.

## Milestones And Tasks

Milestones are visible checkpoints, such as "source review complete," "first demo usable," or "review finished."

- Milestones can own tasks, evidence, research sources, and outputs.
- A Kanban task can belong to a project and optionally to a specific milestone.
- Creating a task writes to `kanban.md` and syncs project ownership back into Project Board.
- Moving a task to Doing records a start date; moving it to Done records a completion date.

## Write Boundaries

This page mainly writes `project-board.yaml`. Creating, moving, or linking tasks can also update `kanban.md`. Linking evidence or research sources keeps refs consistent, but does not rewrite the evidence body or source content.

## Notes

- Do not turn every single action into a project. Work that fits one Kanban card can stay on Kanban.
- If a project has no tasks, evidence, or outputs for a long time, consider pausing, archiving, or splitting it.
- The fewer unassigned tasks and evidence rows remain, the more accurately Dashboard and Review can represent the real work structure.
