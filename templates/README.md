# Templates

Drop-in starting points for any repo that uses the `terraform-cd` and
`terraform-validate` reusable workflows in this repo. Every placeholder is
a plain `${VAR}` so you can render with `envsubst` (no Python, no
templating engine).

## What's here

| File | Goes in your repo as | Purpose |
|------|---------------------|---------|
| `backend.tf.tpl` | `backend.tf` (verbatim, no rendering) | `terraform {}` + provider versions + empty `backend "azurerm" {}` block |
| `backend.hcl.tpl` | `backend.hcl` (for local init only) | Backend config for `terraform init -backend-config=` when running locally |
| `tfvars.tpl` | `configs/<scope>-<region>-<env>.tfvars` | Per-deployment variable file |
| `caller-cd.yml.tpl` | `.github/workflows/<env>-cd.yml` | Workflow that calls the reusable `terraform-cd.yml` |
| `caller-validate.yml.tpl` | `.github/workflows/terraform-validate.yml` | Workflow that calls the reusable `terraform-validate.yml` on PRs |

## Rendering a template

Use any envsubst-compatible tool. GNU `envsubst` ships in `gettext` and is
available on every CI runner.

### Bash / Linux / macOS / WSL

```bash
export OWNER=BRBuffington
export PIPELINES_REF=main
export ENV_NAME=dev
export CONFIGS_JSON='["myapp-eus-dev"]'
export WORKING_DIR=infra
export TFVARS_DIR=configs
export RUNS_ON='"ubuntu-latest"'

mkdir -p .github/workflows infra/configs
envsubst < templates/caller-cd.yml.tpl > .github/workflows/dev-cd.yml
envsubst < templates/caller-validate.yml.tpl > .github/workflows/terraform-validate.yml

export SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
export LOCATION=eastus
envsubst < templates/tfvars.tpl > infra/configs/myapp-eus-dev.tfvars

cp templates/backend.tf.tpl infra/backend.tf
```

### PowerShell (Windows)

```powershell
$vars = @{
  OWNER         = "BRBuffington"
  PIPELINES_REF = "main"
  ENV_NAME      = "dev"
  CONFIGS_JSON  = '["myapp-eus-dev"]'
  WORKING_DIR   = "infra"
  TFVARS_DIR    = "configs"
  RUNS_ON       = '"ubuntu-latest"'
}
$vars.GetEnumerator() | ForEach-Object { Set-Item "env:$($_.Key)" $_.Value }

New-Item -ItemType Directory -Force .github\workflows, infra\configs | Out-Null
bash -c "envsubst < templates/caller-cd.yml.tpl"       | Set-Content .github\workflows\dev-cd.yml
bash -c "envsubst < templates/caller-validate.yml.tpl" | Set-Content .github\workflows\terraform-validate.yml
```

## Placeholders reference

| Var | Where used | Example | Notes |
|-----|-----------|---------|-------|
| `OWNER` | caller workflows | `BRBuffington` | The GitHub org/user that owns this `terraform-pipelines-github` repo |
| `PIPELINES_REF` | caller workflows | `main` or `v1.2.0` | Pin to a tag/SHA for production stability |
| `ENV_NAME` | caller-cd, tfvars | `dev`, `prod` | One env per caller workflow; matches a GitHub Environment |
| `CONFIGS_JSON` | caller-cd | `["myapp-eus-dev"]` or `["myapp-eus-prd","myapp-wus-prd"]` | JSON array of tfvars basenames (without `.tfvars`), each `<scope>-<region>-<env>` |
| `WORKING_DIR` | caller workflows | `.` or `infra` | Path to your Terraform root |
| `TFVARS_DIR` | caller-cd | `configs` | Subdir of WORKING_DIR containing the `<scope>-<region>-<env>.tfvars` files |
| `RUNS_ON` | caller workflows | `"ubuntu-latest"` or `["self-hosted","my-pool"]` | JSON-encoded runs-on value (note quotes around string form) |
| `RESOURCE_GROUP_NAME` | backend.hcl | `rg-tfstate-mine` | The resource group holding your tfstate storage account |
| `STORAGE_ACCOUNT_NAME` | backend.hcl | `sttfstatemine01` | Must have `shared_access_key_enabled = false` |
| `CONTAINER_NAME` | backend.hcl | `tfstate` | Blob container name |
| `KEY_PREFIX` | backend.hcl | `my-stack` | Prefix for state file keys; one prefix per stack |
| `CONFIG_NAME` | backend.hcl | `myapp-eus-dev` | `<scope>-<region>-<env>`; one state file per config: `${KEY_PREFIX}/${CONFIG_NAME}.tfstate` |
| `SUBSCRIPTION_ID` | tfvars | GUID | Target Azure subscription |
| `LOCATION` | tfvars | `eastus` | Azure region |

## Required GitHub Environment vars (per env)

In your repo Settings → Environments, create two Environments per env:
`${ENV_NAME}` (plan) and `${ENV_NAME}-apply` (gated). Configure required
reviewers on `${ENV_NAME}-apply`. Both Environments need these vars:

| Var | What |
|-----|------|
| `AZURE_CLIENT_ID` | The OIDC-federated client/app ID that has Terraform deploy permissions |
| `AZURE_TENANT_ID` | Tenant GUID |
| `AZURE_SUBSCRIPTION_ID` | Target subscription GUID |
| `TF_BACKEND_RESOURCE_GROUP` | Same as `RESOURCE_GROUP_NAME` above |
| `TF_BACKEND_STORAGE_ACCOUNT` | Same as `STORAGE_ACCOUNT_NAME` above |
| `TF_BACKEND_CONTAINER` | Same as `CONTAINER_NAME` above |
| `TF_BACKEND_KEY_PREFIX` | Same as `KEY_PREFIX` above |

## Rules these templates encode

These are not optional. The reusable workflows assume them and the
`terraform-validate.yml` reusable workflow's guard step will fail PRs that
break them:

1. **Per-config backend `key`, NEVER `terraform workspace`.** The CD
   workflow gives each config its own state file via
   `key = "${KEY_PREFIX}/${CONFIG_NAME}.tfstate"`. Adding a
   `terraform workspace select` step on top creates an orphan workspace
   blob at `<key>env:<config>`, separate from the real state in workspace
   `default`. Every subsequent plan refreshes the empty orphan and proposes
   re-creates for your entire stack. Pick one separation mechanism, not
   both. See [the matching regression rule](https://github.com/BRBuffington/MSX_LLM/tree/main/regressions/terraform-workspace-orphan-on-per-config-key).
2. **`use_azuread_auth = true` and `use_oidc = true` are non-negotiable.**
   Storage shared keys must be disabled on the tfstate SA; auth is AAD
   only; runners federate via OIDC (no client secret).
3. **Caller workflows must reference both `${ENV_NAME}` and
   `${ENV_NAME}-apply` Environments.** Plan runs in the first, apply in
   the second; required reviewers go on the apply environment.
4. **The OPA policy gate is on by default (`run_opa = true`).** The CD plan
   job runs hard-fail `conftest` checks (not soft like checkov):
   - **backend-key convention** — the init key must be
     `<prefix>/<config>.tfstate` (one nested state file per config). Catches a
     flat/laptop-style key that would diverge from the per-config CD blob.
   - **no unexpected destroy/recreate** — denies a plan that deletes/replaces
     live resources or mass-creates against empty/wrong state (the
     "plan wants to rebuild the whole stack" signature). Override a genuinely
     intentional destructive or large first-apply plan with the `allow_recreate`
       input (or the `destroy` input for a destroy run).
    - **no container image rollback** — denies an existing Azure Container App
       image change unless the new version is provably equal-or-newer. Unknown or
       digest-only version changes fail closed. A rollback requires explicit user
       consent, a manual `workflow_dispatch`, and `allow_version_rollback=true`;
       push events cannot activate the override. Policies live in
     [`policy/`](../policy) and are unit-tested by the `policy-test` workflow.
5. **Config & tfvars naming: `configs/<scope>-<region>-<env>.tfvars`.**
   Per-config tfvars live in `infra/configs/` and are named descriptively, NOT
   `tier1`/`tier2`/`environments`. Format:
   - **scope** — the workload/sub-stack (`corpus`, `policy`, `gi-mdm-data`).
   - **region** — the CAF region alias: `eus`=eastus, `eus2`=eastus2,
     `wus`=westus, `cus`=centralus, `ncus`=northcentralus, etc.
   - **env** — the lifecycle suffix, kept **last** so `*-prd.tfvars` /
     `*-dev.tfvars` glob across regions: `dev`, `tst`, `si`, `qa`, `uat`,
     `prd`, `dr`.

   Examples: `corpus-eus-prd.tfvars`, `gi-mdm-data-eus2-tst.tfvars`. The state
   key (rule 1) mirrors the basename: `${KEY_PREFIX}/<scope>-<region>-<env>.tfstate`.

   **A security posture / feature flag is a VARIABLE on one config, NOT a
   second config.** Two configs mean two genuinely separate deployments
   (different resources/region/env), each with its own state file. A
   lockdown switch, a public-access toggle, etc. that mutates the SAME
   resources must be a `var` in the single config — never a `tier1`/`tier2`
   split (that was the corpus-search empty-state incident: two state files
   fighting over one physical stack).

   Shared (non-config) files use a `z_` prefix so they sort to the bottom of
   `configs/`: `z_backend.tfvars`, `z_common.tfvars`, `z_tags.yaml`.
