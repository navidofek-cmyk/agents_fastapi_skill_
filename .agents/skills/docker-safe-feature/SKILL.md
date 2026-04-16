---
name: docker-safe-feature
description: Safely implement a small Docker-aware backend feature with summary, test-first planning, explicit file ownership, coding, tests, and review.
---

# docker-safe-feature

Use this skill when adding or changing a backend feature in this repository.

## Workflow
1. Summarize the task, expected behavior, and likely files before coding.
2. Plan the change.
3. Think test-first: identify the failing or missing test that proves the behavior before implementing the fix or feature.
4. Assign explicit file ownership before coding so each agent or step has a clear write scope.
5. Only after steps 1-4 are written down, implement the smallest safe code change.
6. Run tests locally.
7. Review the result for regressions.
8. If Docker files changed, rebuild and verify the service starts.

## Rules
- Mandatory order before coding: summary -> test plan -> file ownership -> code.
- Do not start coding before writing a short summary of the intended change.
- Do not start coding before stating which test should fail first or which missing test must be added first.
- Do not start coding before stating explicit file ownership for code and test changes.
- Prefer minimal write scope and minimal behavior change.
- Avoid unrelated refactors.
- Keep changes small and easy to validate.

## Output
Return:
- summary
- plan
- test plan
- file ownership
- changed files
- tests run
- review notes
- residual risks
