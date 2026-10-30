# Subscription Deployment Identity

## Approved Scope

The owner selected one trusted deployment identity per subscription for the
small Azure fleet, rather than identities per application, repository, or
plan/apply operation. Keep the existing shared runner pool and reusable CD
workflow. Reuse the current runner UAMI and its accepted roles in its existing
subscription. Resolve each additional subscription and tenant before creating
or attaching another identity.

## Observable Contract

- `use_managed_identity` is an optional boolean workflow input, default false.
  Existing callers retain OIDC without changes.
- An opted-in job authenticates directly with the attached identity selected by
  `AZURE_CLIENT_ID`, then selects and verifies `AZURE_SUBSCRIPTION_ID` and
  `AZURE_TENANT_ID`. No per-repository federated credential is required.
- Plan, apply, and optional tag stamping honor the same selection. Terraform
  backend and providers use the authenticated Azure CLI session in direct
  identity mode, not a GitHub token or a client secret.
- Install Azure CLI only where needed, using the official installer already
  used by this workflow. Bound installation and login. Do not rebuild the
  runner image or add a custom token client.
- Keep backend keys, saved-plan application, environment approval gates,
  rollback protection, and resource permissions unchanged.
- Preserve existing federated credentials while consumers migrate. A failed
  qualification does not justify a permissions change or another auth fallback.

## Qualification

1. A real existing ACA runner logs in without GitHub OIDC permission, verifies
   tenant/subscription, and reads existing private state metadata.
2. The real Terraform backend and selected providers complete a bounded plan
   using direct identity. No apply is part of qualification.
3. Focused workflow contracts and actionlint pass for all three job paths;
   default OIDC behavior remains covered.
4. Required CI and independent review precede shared-workflow merge.

The registry consumer is the first opt-in. Registry adoption still requires
its independent one-import/zero-resource-change plan and release approval.
Production MCP, registry settings, and hypothetical subscription identities
are outside this change.