# terraform-pipelines-github

Reusable GitHub Actions workflows for Terraform on Azure. Companion to the
Azure DevOps templates in `terraform-pipelines-azure` — no hardcoded tenants,
subscriptions, or service principal secrets. Auth is OIDC.

## Workflows

- `.github/workflows/terraform-validate.yml` — fmt / init (no backend) / validate / tflint / Checkov. Also enforces two guards on the calling repo: (1) no `terraform workspace select|new` in any `.github/workflows/*.yml` (incompatible with the per-config backend `key` pattern), and (2) any `backend.hcl` under `working_dir` sets `use_azuread_auth = true` and `use_oidc = true`.
- `.github/workflows/terraform-cd.yml` — matrix plan + gated apply (GitHub Environment approval).
- `.github/workflows/terraform-drift-detect.yml` — scheduled scan of the tfstate container; fails the run if any orphan workspace blob (`*env:*` shape) is found. Call on a cron from each consumer repo. See workflow file header for an example caller.

All three are `workflow_call` reusable workflows.

## Templates

[`templates/`](templates/README.md) holds drop-in starting points for each
piece a consumer normally hand-writes: `backend.tf`, `backend.hcl` (for
local init), per-env `tfvars`, and caller workflows for CD and validate.
Every placeholder is plain `${VAR}` — render with `envsubst`, no Python or
templating engine required. The README in that folder lists every
placeholder and the GitHub Environment vars you need.

## Consumer setup

In a consumer repo (e.g. `CHCO-azure-network`), create thin wrapper workflows under
`.github/workflows/` that call these.

### Example: PR validation

```yaml
name: terraform-validate
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: ["feature/**", "hotfix/**", "bug/**"]
jobs:
  validate:
    uses: BRBuffington/terraform-pipelines-github/.github/workflows/terraform-validate.yml@main
    with:
      working_dir: "."
```

### Example: CD (manual dispatch)

```yaml
name: terraform-cd
on:
  workflow_dispatch:
    inputs:
      environment: { type: choice, options: [dev, staging, prod], default: dev }
      configs:    { type: string, default: '["dev"]' }
      plan_only:  { type: boolean, default: true }
      destroy:    { type: boolean, default: false }
jobs:
  cd:
    uses: BRBuffington/terraform-pipelines-github/.github/workflows/terraform-cd.yml@main
    with:
      environment: ${{ inputs.environment }}
      configs:     ${{ inputs.configs }}
      plan_only:   ${{ inputs.plan_only }}
      destroy:     ${{ inputs.destroy }}
      working_dir: "."
      tfvars_dir:  "environments"
    permissions:
      id-token: write
      contents: read
      pull-requests: write
```

## One-time per environment

For each GitHub Environment (`dev`, `staging`, `prod`, plus `*-apply` twins for approval gates):

1. **Entra app reg** + service principal. Grant Contributor on target sub, Storage Blob Data
   Contributor on tfstate storage account.
2. **Federated credential** on the app reg: GitHub Actions, this repo, entity = Environment, value = `dev` (and `dev-apply`).
3. **GitHub Environment** (`Settings -> Environments`). Add required reviewers on the `*-apply` ones.
4. **Environment vars** on the consumer repo:

   | Variable | Purpose |
   |---|---|
   | `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID` | OIDC + provider |
   | `TF_BACKEND_RESOURCE_GROUP` / `TF_BACKEND_STORAGE_ACCOUNT` / `TF_BACKEND_CONTAINER` | azurerm backend |
   | `TF_BACKEND_KEY_PREFIX` | state key becomes `<prefix>/<config>.tfstate` |

5. Consumer's `providers.tf` must declare `terraform { backend "azurerm" {} }`.
   The workflow injects all backend args via `-backend-config=`.

## Inputs

### terraform-validate

| Input | Default | Notes |
|---|---|---|
| `working_dir` | `.` | Where the root module lives. |
| `terraform_version` | `""` | Empty = read `.terraform-version`, fallback `1.9.5`. |
| `run_tflint` | `true` | Soft-fail. |
| `run_checkov` | `true` | Soft-fail. |

### terraform-cd

| Input | Default | Notes |
|---|---|---|
| `environment` | required | GitHub Environment (must match a federated cred). |
| `configs` | required | JSON array string, e.g. `'["dev"]'`. Each maps to `<tfvars_dir>/<config>.tfvars`. |
| `plan_only` | `true` | When false, gated apply runs after plan. |
| `destroy` | `false` | Adds `-destroy`. |
| `working_dir` | `.` | |
| `tfvars_dir` | `environments` | Relative to `working_dir`. |
| `terraform_version` | `""` | |
| `max_parallel_plan` | `4` | |
| `apply_timeout_minutes` | `60` | |
| `run_checkov` | `true` | |

## Versioning

Pin consumers to a tag once stable:

```yaml
uses: BRBuffington/terraform-pipelines-github/.github/workflows/terraform-cd.yml@v1.0.0
```

Until then, `@main` is fine.

## What was dropped vs the ADO original

- `replacetokens` (octopus tokens in tfvars) — use plain tfvars + GitHub vars instead.
- `yor` auto-tagging — re-add with a step if needed.
- ADO branch-name routing (`-sb`, `-dev`, `-prd`...) — replaced by GitHub Environment + protection rules.
- ADO `pre-release` cancel-previous stage — handled by `concurrency:` in the consumer wrapper.
- ADO `pat` for cross-repo module pulls — not needed for public modules / AVM.
- OPA / conftest — out of scope for now (will add when policy repo is ready).
