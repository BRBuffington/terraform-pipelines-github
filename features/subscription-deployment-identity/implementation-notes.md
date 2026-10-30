# Subscription Deployment Identity Implementation Notes

## 2026-10-30 - Approved Direction And First Qualification

The owner rejected unnecessary repository/application isolation for this
trusted small fleet, selected one deployment identity per subscription, and
approved proceeding. This is a scoped extension of the existing runner and
reusable workflow, not a new identity platform or a fleet-wide role redesign.

Base: fetched `origin/main` at
`5523ea6e1610e3eb67e899b47950d1a660b5b34e` in
`BRBuffington/terraform-pipelines-github`. Native worktree inventory showed
only a clean primary main checkout. Implementation is isolated on
`feat/subscription-managed-identity`.

Leverage scan: no matches. Infra scan: reuse `bbuf-runners` and the existing
UAMI inventory. Preserve the runner's trusted subscription permissions.

Official surfaces: Azure CLI managed-identity login; AzureRM4.73.0's documented
CLI login with a managed identity; Terraform's documented pre-authenticated
CLI backend mode. Azure Login's VM-specific identity examples do not establish
ACA support. Use an actual existing ACA runner for qualification instead.

Runner PR29's `netcheck.yml` now has an opt-in bounded qualification job with
contents read only and no `id-token` permission. Run41140380789, head
`0dbce556da1f7032e16f09585cea3fc0c5f9c142`, job124352946796, failed at
`command -v az` before login: CLI is absent from the existing image. This is
not an identity or permissions failure. The exact log has46 lines.

Head`a369856911d627ef71ced79f216d83369238eccc` reuses the existing official
CLI installer inside the disposable job, with a240-second bound. Retry
run41140668071, job124353864918, installed CLI2.72.0 successfully, then
failed at direct login with HTTP405 before state access. The Focal package
feed selected this older CLI; the125-line receipt is retained. The separate
network job124353864570 succeeded.

Source verification before another probe: the exact Azure CLI2.72.0
`src/azure-cli-core/azure/cli/core/_profile.py` selects legacy
`MSIAuthenticationWrapper` by default. Its built-in MSAL path is selected by
`core.use_msal_managed_identity`. Current CLI source uses that MSAL path
directly. Official MSAL source selects the App Service-compatible2019-08-01
GET endpoint when `IDENTITY_ENDPOINT` and `IDENTITY_HEADER` are present, as
documented by Container Apps. Next select the built-in MSAL path with the
job-local CLI configuration environment variable, assert those platform
variables exist without printing them, and rerun the same smoke. Identity,
roles, runner image and global configuration remain unchanged.

References:
- https://raw.githubusercontent.com/Azure/azure-cli/azure-cli-2.72.0/src/azure-cli-core/azure/cli/core/_profile.py
- https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli-core/azure/cli/core/_profile.py
- https://raw.githubusercontent.com/AzureAD/microsoft-authentication-library-for-python/dev/msal/managed_identity.py
- https://learn.microsoft.com/azure/container-apps/managed-identity

Run41141144468, head`984b7eff88ff4013842484bb523031b1d8e6e688`,
job124355420646, passed on the actual ACA runner. Azure CLI installed, the
built-in MSAL path logged in with the expected tenant/subscription, and the
private existing runner state metadata read succeeded. GitHub permissions
were contents/metadata read only, with no OIDC token permission. This proves
the direct-login and private-read slice, not Terraform backend/provider auth.

The owner then requested updating the differing Terraform versions. Official
latest release lookup returned stable1.17.1 (October28); the1.17.0 release
notes were read. Both active caller validation/CD pins now use1.17.1, and
the registry root constraint/version file match. A portable binary was
downloaded from HashiCorp and verified against published SHA256; the actual
registry adoption tests both pass with unchanged locked provider versions.
The machine-wide1.16.6 install and other consumer pins remain untouched.

Next qualify actual Terraform backend/providers using the opt-in shared
workflow mode. No apply, credential deletion, role change, registry import,
or production workload change has run.