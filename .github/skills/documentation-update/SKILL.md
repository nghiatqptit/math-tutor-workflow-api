---
name: documentation-update
description: "Use when updating README files, workflow docs, ADRs, templates, or user-facing guidance after a change."
argument-hint: "Update the docs to match the code"
user-invocable: true
disable-model-invocation: false
---

# Documentation Update

Use this skill when code changes should be reflected in docs.

## Procedure

1. Identify the audience and the doc that is now stale.
2. Update only the sections that changed.
3. Keep terminology aligned with the codebase.
4. Add examples only when they reduce ambiguity.

## Useful Output

- Docs touched
- Summary of changes
- Remaining gaps
