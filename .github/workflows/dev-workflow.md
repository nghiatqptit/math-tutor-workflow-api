# Dev Workflow

Use this flow for feature work, refactors, and larger bug fixes.

## Sequence

1. Research
2. Planning
3. Human Approval
4. Jira
5. Context Builder
6. Discovery Agent
7. Implementation Agent
8. Testing Agent
9. Documentation Agent

## Phase Contracts

### Research

- Understand the problem precisely
- Collect assumptions, missing information, and constraints
- Accept input from either a Jira ticket or a user chat prompt
- No code

### Planning

- Propose options
- Compare trade-offs
- Estimate complexity and risk

### Human Approval

- User must select one of: `Approved`, `Revise`, or `Rejected`
- If there is no user choice yet, stop here and wait
- If not approved, do not continue to Jira or implementation; return to Planning only after the user provides a new choice

### Jira

- Convert the approved plan into Epic, Story, Task, or Sub-task backlog items
- Push the issue set to Jira through MCP

### Context Builder

- Determine required domains, flows, services, files, and ADRs
- Produce the implementation context package

### Discovery Agent

- Build or refresh the knowledge base under `.ai/`
- Compare the codebase against the previous indexed commit
- Update only the maps and indexes affected by changed files
- Write the new indexed commit back to `.ai/project-manifest.yaml`

### Implementation Agent

- Load the manifest and required maps first
- Stop and call Discovery if the knowledge base is missing
- Implement only the approved scope

### Testing Agent

- Add unit, integration, and regression coverage as needed
- Validate the implementation result

### Documentation Agent

- Update docs and `.ai/` knowledge artifacts when the code or flow changed

## Expected Outputs

- `.ai/research/<feature-name>.md`
- `.ai/plans/<feature-name>.md`
- `.ai/reviews/architecture-review.md`
- `.ai/tickets/ticket.md`
- `.ai/system/overview.md`
- `.ai/system/architecture.md`
- `.ai/domains/`
- `.ai/services/`
- `.ai/flows/`
- `.ai/indexes/`
- `.ai/project-manifest.yaml`
- `tests/`
