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

## 2026-11-08 Council HOLD And Local Binding Repair

Shared PR 19 head e07defc9081c72e42b09ea731c15caf4ae459903 passed hosted CI
42497174702, but council panel e03dbeec-f03f-5be9-8b03-5703f3316445 and
reconciliation f87935a1-ebeb-5775-890b-f5e41fb9ee95 ended HOLD (two BLOCK,
one NIT). Official PR comment 6723823069 independently confirms the verdict.
No merge or deployment occurred. Caller draft PR 15 head
0e7e470afbd5182bab85599c8467e5a8885fd705 passed CI 42498094033 and remains
dependent on shared landing.

The local repair binds the existing OIDC/CLI mode, checked-out shared workflow
bytes and the exact executed reusable workflow path/SHA from GitHub's current
run-attempt API. Source and current references must match, and missing/ambiguous
metadata fails closed. This closes a moving-main gap that checkout hashing alone
cannot close. Existing native caller token, metadata CLI and permissions are
reused; no identity/grant, state or infrastructure change is needed.

F1's claimed single-artifact nesting is disproved by the actual v8.0.1 source:
https://raw.githubusercontent.com/actions/download-artifact/v8.0.1/src/download-artifact.ts
Its download path selects resolvedPath when artifacts.length === 1. Explicit
merge-multiple is retained to make the intended layout unambiguous, with the
existing single numeric artifact-ID validation unchanged. The initial YAML
indentation defect was repaired. GitHub-aware actionlint now passes with
ShellCheck disabled; full ShellCheck reports the unchanged plan command SC2086.

Official contract and live caller CI response both expose referenced_workflows
with path/sha/ref. The supported run-attempt endpoint preserves attempt identity:
https://docs.github.com/en/rest/actions/workflow-runs#get-a-workflow-run-attempt
Local validator tests pass the auth-mode, checked-out workflow-byte, executed
revision and current-run provenance checks. New-head CI and a fresh non-author
council remain required before landing. Native token access
and metadata availability during a real retained-plan run remain hosted proof
limits, not claims made from the completed validate-only caller CI.

The completed repair validation passes 20 workflow contract tests and 85
subtests, Ruff on the touched Python slice and actionlint's YAML/expression
checks, patch hygiene and the canonical regression precheck. The fetch-first
shared feature-order check is clear. New-head CI and fresh council approval
are not yet claimed.

## 2026-11-08 Artifact Isolation And Binary-Policy Linkage Repair

Published binding repair 010a37277e28d5f00c3d14c1ebcd4c84b6df164a passed exact-head
hosted CI 42499788310, attempt 1. Fresh Workbench council receipt
47261503-cd6c-5981-aba0-9fa0b025b903 completed two rounds and held PR 19 (one BLOCK,
one NIT, one APPROVE). The blocking findings concern checkout overwrite during
artifact extraction and independent hashes that do not link the binary to the
reviewed JSON or policy check. Neither workflow merged and no resource changed.

The bounded repair keeps the official download action and uses an isolated
runner-temp bundle with an exact four-regular-file allowlist. Hash/context checks
precede exclusive staging; conflicting source lock or plan files are preserved.
After readonly init, native Terraform show renders the staged saved binary.
Canonical typed JSON comparison rejects a substituted review document; empty,
malformed, nonzero and timed-out native rendering fail closed. The existing
conftest version/policies and typed safety parameters are reused for a new OPA
check on that binary-derived JSON before apply. There is no Terraform replan,
new identity/grant, state relocation, provider upgrade or approval mechanism.

Initial focused isolation tests passed 19 tests/58 subtests; the first linkage
check passed 22 tests/64 subtests. The full suite then passed 28 tests/93 subtests.
Actionlint caught two invalid job-level runner.temp expressions; the existing
request step now initializes those paths from RUNNER_TEMP through GITHUB_ENV.
Actionlint and Ruff passed, and the affected rerun passed 24 tests/66 subtests.
Shared and pilot-journal patch hygiene passed. Exact-head CI and fresh non-author
council remain required before landing. Fixtures do not
prove native caller-token artifact access, current-attempt metadata availability
or an actual retained-plan/apply execution. The approved downstream order remains
shared/caller landing, real saved-plan qualification, model addition, existing
dev runtime configuration/release, then July-October hosted acceptance.

## 2026-11-08 Receipt Environment And Policy-Parameter Repair

Published isolation/linkage head d56d4db3a084492b1e51cd7014edd2ff570c7cbd passed
hosted CI 42502613426, attempt 1. Workbench receipt
3537e7db-30e3-5d6b-9e09-607ff5c289a5 held shared PR 19 with three final BLOCKs.
The receipt step omitted RUN_OPA, which the validator requires; the reviewed
binary gate also emitted root-level flags instead of the existing data.params
envelope. The unchanged Rego policies stay strict when params are missing;
this is broken receipt/override wiring, not an established policy bypass.

Focused regressions reproduced both defects before the two-line workflow repair.
The receipt test now checks actual workflow propagation and runs record() with
explicit enabled/disabled policy environments. The existing Bash gate check
verifies nested typed parameters and propagates nonzero conftest status. A new
test feeds workflow-generated parameters to the actual unchanged Rego policies
for nine strict-default, recreation and manual-only rollback cases. No new test
file, dependency, policy exception, identity, infrastructure or state is added.

Local validation passes 29 tests and 93 subtests, Ruff and actionlint's
YAML/GitHub-expression checks. OPA is absent locally, so its test explicitly
skips here and fails closed if OPA is missing in GitHub Actions. Existing hosted
CI installs OPA 1.4.2 and must execute all nine cases at the new exact head.
Python editor diagnostics are clear; the existing static workflow warning cannot
resolve the reviewed bundle path initialized through GITHUB_ENV.
The refreshed shared feature-order/native worktree inventory is clear.
Leverage scan: no matches. Infra scan: no matches.
New-head CI and a fresh non-author council with the actual policy sources remain
required. Real caller-token artifact access, current-attempt metadata and saved
plan execution remain separate hosted qualifications; no apply has occurred.

## 2026-11-08 Policy Implementation Binding

Exact-head CI run 42505417805 succeeded on
3e493fbc570206a60ae8e7c0b917f6f5713e09ef. Hosted logs show 30 tests passed,
including receipt RUN_OPA propagation and all nine actual-Rego cases without a
skip. The complete-source council's reconciliation run
6b67efee-817d-5f1c-9e6a-8532c8838796 finished HOLD: Sonnet NIT, MAI-Code-2-Flash
BLOCK, Terra APPROVE. The remaining block was missing policy-byte binding.

An isolated reproduction reused the real retained-plan fixture and cloned the
policy checkout into its temporary directory. Changing only a policy file was
accepted while workflow bytes and executed-revision metadata stayed unchanged.
No repository file was modified by that reproduction. Executed workflow
metadata alone does not prove the bytes fetched from a moving checkout ref.

The existing context now records every recursively discovered Rego policy's
relative filename and SHA256, rejecting absent/invalid policy files. The existing
context equality check rejects content changes, additions, removals and renames
before plan staging. The fixture uses an isolated checkout so these tests never
edit the actual policy sources. The focused unchanged-policy and mutation tests
pass (two tests, four subtests). No policy exceptions, new bundle members,
credentials, infrastructure, dependencies or deployment permissions are added.

Full local workflow qualification passes 30 tests and 97 subtests; actual OPA is
explicitly skipped locally because it is absent. Ruff and actionlint pass.
Exact-head hosted CI and a new independent council remain required before
landing. PR15 remains draft and dependent on PR19.
Native caller-token/current-attempt/artifact qualification and the approved dev
apply remain later steps. No merge, model apply or application deploy occurred.
Leverage scan: no matches. Infra scan: no matches (same approved repair scope).