---
name: security-review
description: "Use when reviewing prompt injection risks, unsafe execution, secret exposure, auth boundaries, input sanitization, or general security impact."
argument-hint: "Review the security implications"
user-invocable: true
disable-model-invocation: false
---

# Security Review

Use this skill when a change could affect trust boundaries or unsafe inputs.

## Procedure

1. Identify the input surface and trust boundary.
2. Check sanitization, validation, and escape paths.
3. Review privilege, secrets, and outbound calls.
4. State whether the current guardrails are sufficient.

## Useful Output

- Threats
- Existing controls
- Gaps
- Recommended fixes
