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
- No code

### Planning

- Propose options
- Compare trade-offs
- Estimate complexity and risk

### Human Approval

- User selects the option or requests revision
- If not approved, return to Planning

### Jira

- Convert the approved plan into Epic, Story, Task, or Sub-task backlog items
- Push the issue set to Jira through MCP

### Context Builder

- Determine required domains, flows, services, files, and ADRs
- Produce the implementation context package

### Discovery Agent

- Build or refresh the knowledge base under `.ai/`
- Update maps and indexes when missing or stale

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
