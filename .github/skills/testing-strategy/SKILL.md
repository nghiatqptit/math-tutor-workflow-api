---
name: testing-strategy
description: "Use when deciding test layers, writing regression coverage, choosing unit versus integration scope, or validating a fix for the workflow API."
argument-hint: "Define the test strategy"
user-invocable: true
disable-model-invocation: false
---

# Testing Strategy

Use this skill when a request needs a clear validation plan.

## Procedure

1. Identify the behavior that must not regress.
2. Pick the lightest test layer that covers it.
3. Add edge cases for failure handling and boundaries.
4. Define how to confirm the fix locally.

## Useful Output

- Test layers
- Regression cases
- Edge cases
- Validation command
