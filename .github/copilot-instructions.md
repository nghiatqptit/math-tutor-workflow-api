# Copilot Instructions

You are working in the Math Tutor Hybrid Workflow Orchestrator, a production FastAPI service for math reasoning, retrieval, verification, formatting, caching, and observability.

## Primary Goal

Keep changes safe, minimal, and aligned with the existing pipeline:

1. validate the request and isolate the exact stage that is being changed
2. preserve deterministic verification and cache behavior
3. keep router, service, schema, and documentation changes consistent
4. add or update tests when behavior changes

## Working Rules

- Prefer the smallest change that fixes the real problem.
- Do not rework unrelated modules while solving a task.
- If a task affects behavior, identify the control point first: router, service, client, middleware, schema, or test.
- If a task spans analysis, design, approval, backlog creation, context building, discovery, implementation, testing, and documentation, use the workflow docs in `.github/workflows/` as the sequence.
- If a task needs specialized reasoning, use the matching agent in `.github/agents/` or the matching skill in `.github/skills/`.
- If evidence is missing, gather it first before editing.
- If the request is ambiguous, ask one focused question only when it blocks a safe change. Otherwise make a grounded assumption and state it clearly.

## Repository Constraints

- Keep the workflow deterministic where possible.
- Preserve the math verification path and any safety guards against prompt injection or unsafe code execution.
- Be careful with streaming responses, cache keys, and schema compatibility.
- Update README or ADR content when a user-facing flow changes.

## Suggested Role Flow

- Use `research-agent` to collect facts and trace the current behavior.
- Use `planner-agent` to break the work into steps, risks, and acceptance criteria.
- Use `architecture-review-agent` when the plan must be checked for scalability, performance, security, cost, maintainability, DDD boundaries, or service boundaries.
- Use `context-builder-agent` to identify the domain, flow, services, source files, and ADRs required for implementation.
- Use `discovery-agent` when the knowledge base or maps are missing or stale.
- Use `jira-agent` when the request should become Jira work such as an epic, story, task, or bug.
- Use `implementation-agent` to make code changes.
- Use `testing-agent` to reproduce issues and verify the fix.
- Use `documentation-agent` to update templates, workflows, and README content.

## Agent Identifiers

- `/research-agent` -> research and evidence gathering
- `/planner-agent` -> scoped planning and acceptance criteria
- `/architecture-review-agent` -> design review before code
- `/architect-agent` -> boundary, contract, and tradeoff review
- `/context-builder-agent` -> build the implementation context package
- `/discovery-agent` -> build or refresh the knowledge base
- `/jira-agent` -> Jira issue creation and lifecycle work
- `/implementation-agent` -> code changes
- `/testing-agent` -> reproduction and validation
- `/documentation-agent` -> docs and workflow updates

## Dev Workflow

Use this sequence for feature work, refactors, and larger fixes:

1. Research
2. Planning
3. Human Approval
4. Jira
5. Context Builder
6. Discovery Agent
7. Implementation Agent
8. Testing Agent
9. Documentation Agent

## Workflow Guide

- Open [dev-workflow.md](./workflows/dev-workflow.md) to follow the phase order.
- Open [workflow-guide.md](./workflows/workflow-guide.md) for the short usage instructions.
- Use `/research-agent`, `/planner-agent`, and `/architecture-review-agent` before implementation when the request is unclear or risky.
- Stop at Human Approval until the user explicitly chooses `Approved`, `Revise`, or `Rejected`.

## Workflow Artifacts

- Research output goes to `.ai/research/<feature-name>.md`
- Planning output goes to `.ai/plans/<feature-name>.md`
- Architecture review output goes to `.ai/reviews/architecture-review.md`
- Jira output goes to `.ai/tickets/ticket.md`
- Context builder output describes required domains, flows, services, files, and ADRs
- Discovery output updates `.ai/system/`, `.ai/domains/`, `.ai/services/`, `.ai/flows/`, `.ai/indexes/`, and `.ai/project-manifest.yaml`

## Jira MCP Usage

- Use the Jira MCP tools for issue creation, lookup, updates, and status transitions when the task needs Jira tracking.
- Prefer an Epic when the request spans multiple stories or a larger milestone.
- Prefer a Story when the work has a user-facing outcome and clear acceptance criteria.
- Prefer a Task when the work is technical and does not need a user story frame.
- Prefer a Bug when the work is a regression or defect with a reproducible failure.
- Before creating Jira work, capture the problem statement, acceptance criteria, dependencies, and validation notes in the Jira template.
- When the request is ambiguous, produce the Jira draft first and ask for confirmation before creating or transitioning issues.

## Output Expectations

- For implementation work, report what changed, how it was validated, and any residual risk.
- For analysis work, return findings, assumptions, and the smallest recommended next step.
- For design work, return the decision, alternatives considered, and the impact on the pipeline.
