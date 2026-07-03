# Jira Workflow

Use this flow when the request must be tracked in Jira as an Epic, Story, Task, or Bug.

## Sequence

1. Classify the work item type.
2. Fill the Jira template with scope, acceptance criteria, and dependencies.
3. Use Jira MCP to create the issue or update an existing one.
4. If the work is large, create an Epic first and then split child stories or tasks beneath it.
5. Link bugs to the affected epic or story when relevant.
6. Keep issue status synchronized with the actual implementation state.

## When to Use Epic vs Story vs Task vs Bug

- Epic: multi-step outcome, large milestone, or cross-cutting initiative.
- Story: user-facing capability with measurable acceptance criteria.
- Task: technical work item without a user-story structure.
- Bug: defect, regression, or broken behavior.

## Required Fields Before Creation

- Summary
- Problem statement
- Scope
- Acceptance criteria
- Dependencies
- Test notes

## Expected Deliverables

- Jira key
- Issue hierarchy
- Acceptance criteria
- Link to implementation or follow-up work