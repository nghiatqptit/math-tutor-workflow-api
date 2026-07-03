# Workflow Guide

Use this guide when you want to run work through the Copilot workflow in this repository.

## How to Start

1. Paste the user request or Jira ticket into the conversation.
2. Run the `Research Agent` first.
3. Move to `Planning Agent` after research is clear.
4. Pause at `Human Approval` until the user chooses a path.
5. If approved, create Jira work items before implementation.
6. Build the context package.
7. Refresh the knowledge base with Discovery if needed.
8. Implement, test, and document the change.

## Suggested Agent Order

- `/research-agent`
- `/planner-agent`
- `/architecture-review-agent`
- `/jira-agent`
- `/context-builder-agent`
- `/discovery-agent`
- `/implementation-agent`
- `/testing-agent`
- `/documentation-agent`

## Rules

- Do not skip Human Approval for work that changes behavior.
- Do not let Discovery rescan the whole repo when a diff-based update is enough.
- Do not let Implementation expand scope beyond the approved ticket.

## Outputs You Should Expect

- `.ai/research/<feature-name>.md`
- `.ai/plans/<feature-name>.md`
- `.ai/reviews/architecture-review.md`
- `.ai/tickets/ticket.md`
- `.ai/project-manifest.yaml`
- `tests/`