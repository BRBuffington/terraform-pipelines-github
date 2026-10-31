# Subscription Deployment Identity Implementation Notes

## 2026-10-31 - Actual legacy and direct-identity candidate plans pass

Immutable candidate56c68181cdba335df7d5659b7b155bafad64c68a was qualified
through two isolated caller fixtures from fresh default branches. Each fixture
changes only the reusable workflow ref; no authentication, Terraform version,
resource configuration or production branch was changed.

Handoff run41172079263/job124451997981, caller2ce0a66941eca1ae1a3d6d07bade357a9e2a0651,
selected Terraform1.9.5, ARM_USE_OIDC=true/ARM_USE_CLI=false and the existing
handoff-infra/synthesizer.tfstate key. Initialization and plan pass; the full
plan says No changes. Both the backend-key test and all4post-plan OPA tests pass.
The complete749line UTF8/LF log SHA256 is
6f9185f663a1716ffd88d00acc860d148136b61cb7e90fa77dad117af2ad8f5e.

Runner run41172088271/job124452027626, caller2e1631c9abcd09b9a508e3f2340e7e42b87b1451,
selected Terraform1.17.1, ARM_USE_OIDC=false/ARM_USE_CLI=true and the existing
bbuf-runners/runners-eus-prd.tfstate key. Initialization and plan pass with
No changes; backend-key and all4post-plan OPA tests pass. Its complete813line
UTF8/LF log SHA256 is
87405cc77329d4dd31225d92563ed2bd35eb84145cf9bd200a339e6905b5397d.

GitHub independently reports exact reusable SHA56c68181 for both runs.
Apply and LastApplied stamping were skipped in both. The fixed workflow blob
is52cfb42f89f29802dfbf5220b6d1b3650a156044; this results-only documentation
commit must leave those exact workflow bytes and all other runtime code intact.
Candidate CI41170358138 passes opa-test and action-ref-smoke. Normal independent
review and final current-head CI remain required; no review exception transfers.
No resource/network/identity/state-content change or workload apply occurred.

## 2026-10-30 - Preserve legacy OIDC backend compatibility

The owner approved removing only the redundant `use_cli` backend arguments
from plan/apply init. Handoff plan41150661556/job124386140487 failed on the
unchanged Terraform1.9.5/OIDC caller because its backend rejects that argument
even when false. No plan or apply was produced.

Official HashiCorp backend documentation and versioned1.9.5/1.17.1 source
confirm current backends accept `ARM_USE_CLI`;1.9.5 has no `use_cli` schema key.
Both jobs already set `ARM_USE_CLI` and `ARM_USE_OIDC`, so preserve those values,
the opt-in default, all three login paths, versions, identities, roles, state
keys, saved-plan and safety gates. The existing contract now rejects the
unsupported argument in both init jobs while retaining authentication checks.

Leverage scan: no matches. Infra: reuse existing bbuf-runners; defer Corpus,
synthesizer and indexer changes. Canonical runner inventory documents private
state reachability; do not infer a network blocker or introduce a PNA fallback.
Local validation, normal CI/independent review and real plan-only qualification
of legacy OIDC and current direct identity remain required before deployment.

Local validation passes all3workflow contracts and15subtests, including the
actual login scripts' success/failure/authority checks and rejection of the
unsupported argument in both init jobs. Ruff and patch hygiene pass.
Raw actionlint on both this change and immutable basea217eb1 reports only the
same pre-existing SC2086 plan-script warning; excluding that exact diagnostic
leaves actionlint clean. No workflow checks or safety policies were disabled.

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