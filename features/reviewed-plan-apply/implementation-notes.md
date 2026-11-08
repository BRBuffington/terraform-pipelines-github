# Reviewed-Plan Apply Implementation Notes

## 2026-11-08 Initial Implementation

Owner approval followed verified GitHub Free/private reviewer-gate unavailability.
Reuse terraform-cd.yml, the existing actions/download-artifact v8.0.1 contract,
GitHub CLI metadata reads, provider/state identity and the existing test/CI home.
Leverage scan: no matches. Infra scan: no matches; no resource is created here.
Official REST/action and workflow permission contracts were read before the
custom validation adapter. No new API client, SDK or credential store is added.

The initial contract probe failed because the workflow had no reviewed-plan inputs.
The implemented opt-in path retains a single-config policy-checked plan-only
artifact, then applies only an explicit run/artifact/binary-hash reference.
Metadata rejection precedes extraction; bytes, backend/source/identity/safety
context, attempt, provider lock and validator implementation are bound.
Legacy permission maps remain unchanged. The opting-in caller passes its native
token through an optional named secret rather than elevating all callee jobs.

Focused validation currently passes 12 tests and 58 subtests. Existing direct
identity tests passed separately after one unchanged Windows Bash case timed out;
do not weaken the timeout or infer a deployment/auth failure from that fixture.
Ruff passed after a trailing-newline repair. Initial actionlint checks passed for
the shared workflow and caller; final checks/CI/council remain pending.

The shared branch is feat/reviewed-plan-apply from fetched main 632b3acc547e8914a0cb8975a5770a859c1af324.
The caller branch fix/reviewed-model-plan is isolated at corpus-search-reviewed-plan
from fetched main 124f3877f3ed612c93b6515a6ca3195e7d38fdfb. Preserve all other caller
worktrees, the user's primary checkout and the application's pre-existing journal.
No commit, PR, live plan/apply, identity change or production mutation has occurred
in this implementation slice yet. Finish review/merge before the real model plan.

The dev application image is already independently verified published on source
20734f735bc3103701024fb2da9796146375d278 by publisher 42459369565, artifact 13621648132.
It remains undeployed. Model apply, approved dev runtime settings, dev release and
complete July-October hosted generation/publication checks remain later steps.

Final execution validation passed all 15 workflow tests and 73 subtests, Ruff,
actionlint for shared CD/CI and caller workflows, and patch hygiene in both
repositories. Source metadata rejection precedes extraction, invalid plan-only
tuples fail positively, and validator changes require a fresh reviewed plan.
The next gates are task-only staging/regression precheck, exact-head CI and
non-author council review. The native caller-token cross-run path remains a
hosted proof limit until the real retained-plan/apply execution is verified.