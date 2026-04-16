# Agent Execution Matrix

This document defines how agent roles are split in this repository when using the structured workflow.

| Role | Responsibility | Inputs | Outputs | Done When |
|---|---|---|---|---|
| Planner | Narrow scope, define the smallest safe change, identify tests first, assign file ownership | User request, current repo state | Summary, plan, test plan, file ownership | The implementation scope is clear and bounded |
| Coder | Implement the requested change only in the assigned files | Planner output, current code | Code changes | The feature or fix is implemented in the agreed write scope |
| Tester | Mandatory verification step: add or adjust tests and run the relevant verification commands | Planner output, coder changes | Test changes, command results | The behavior is verified with concrete test output and the task cannot close without it |
| Reviewer | Look for bugs, regressions, scope leaks, and documentation drift | Diff, test results, current repo state | Findings, review notes, residual risks | No critical or unresolved issue remains |
| Main Rollout | Integrate results, resolve review findings, update docs/logs, provide final status | All role outputs | Final state, docs updates, final summary | The task is closed end-to-end |

## Role Rules

### Planner
- Must not write code.
- Must state the intended behavior before implementation.
- Must identify the failing or missing tests that should prove the change first.
- Must assign explicit file ownership before coding starts.

### Coder
- Must stay within the assigned write scope.
- Must avoid unrelated refactors.
- Must implement the smallest safe change.
- Must preserve existing architecture patterns unless the task requires otherwise.

### Tester
- Is mandatory for every code change in this repository.
- Must focus on behavior, not implementation details.
- Must run the relevant commands and report exact results.
- Must prefer the smallest test change that proves the requested behavior.
- Must flag gaps when behavior is only partially covered.

### Reviewer
- Must prioritize bugs and regressions over style opinions.
- Must call out scope leaks explicitly.
- Must check whether tests and docs still match the implementation.
- Must report residual risks even when no blocking issue is found.

### Main Rollout
- Must verify the final integrated state.
- Must resolve reviewer findings or clearly document why they remain.
- Must update repository docs when the behavior or workflow changes.
- Must provide a concise end-state summary.
