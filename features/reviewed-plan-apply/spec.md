# Explicit Reviewed Saved-Plan Apply

## Approved Scope

On 2026-11-08 the owner approved adapting the existing Terraform lane so a manual
apply consumes an exact previously reviewed saved plan. The immediate caller is
the existing corpus-search model stack. GitHub Free/private repository limits
prevent environment required reviewers. Do not change the GitHub plan, repository
visibility, identities, grants, runner infrastructure, provider constraints,
backend topology or production resources to obtain a review pause.

## Observable Contract

- The existing caller can opt in to require an explicit retained-plan reference.
- A policy-checked, non-destroy main plan-only run for one configuration retains
  the binary plan, JSON, provider lock and source/context/hash receipt.
- The operator reviews the exact artifact and approves a separate manual apply.
- Apply requires exact source run, immutable artifact ID and binary SHA256.
- Unsuccessful, expired, incomplete or mismatched provenance fails closed before
  application. Source metadata rejection precedes artifact extraction.
- Source commit, workflow, configuration, environment, state location/key,
  identity, authentication mode, Terraform version, safety flags, executed
  reusable workflow revision, checked-out workflow bytes and validator bytes
  must still match. Missing/ambiguous reusable workflow metadata fails closed.
- The plan, JSON and provider lock must match the retained receipt. A conflicting
  source lock is never overwritten; a missing one is restored from reviewed bytes.
- Apply uses the saved binary and readonly provider lock selection, not a new plan.
- A stale state failure requires a new reviewed plan, never an automatic retry
  with different plan bytes. Unconfigured callers retain existing behavior.
- The native caller token supplies only the opt-in artifact reads. No new stored
  credential is created; legacy callee permissions remain unchanged.

## Verification

The existing workflow test file exercises real selection scripts and the actual
validator with exact/invalid references, source/backend/identity/safety/attempt
changes, absent/malformed metadata and plan/JSON/lock/validator tampering.
It also rejects changed executed reusable workflow revisions and auth modes.
Use actionlint for GitHub expressions, existing Ruff, patch/regression gates,
hosted CI and non-author PR council. Then validate the opt-in caller with a real
retained artifact and source-bound manual apply on the approved dev deployment.

## Boundaries

Review is an operator action, not inferred from a successful plan or a hash.
This change adds no global deployment policy or independent approval identity.
Keep the default single-run path, OPA rules, matrix behavior and tag stamping.
Do not deploy the application or claim hosted Engagement Explorer acceptance from
a workflow unit test, plan artifact or model deployment alone.