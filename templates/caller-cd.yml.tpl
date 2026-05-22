# Caller workflow that consumes the reusable terraform-cd.yml.
# Drop this in your repo at .github/workflows/<ENV_NAME>-cd.yml
#
# Render with envsubst:
#   export OWNER=BRBuffington
#   export PIPELINES_REF=main          # or a pinned tag/sha
#   export ENV_NAME=dev
#   export CONFIGS_JSON='["dev"]'      # JSON array of tfvars basenames
#   export WORKING_DIR=.
#   export TFVARS_DIR=environments
#   export RUNS_ON='"ubuntu-latest"'   # or '["self-hosted","my-pool"]'
#   envsubst < templates/caller-cd.yml.tpl > .github/workflows/dev-cd.yml
#
# Required GitHub Environment vars (configure both `${ENV_NAME}` and
# `${ENV_NAME}-apply` Environments in repo Settings):
#   AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
#   TF_BACKEND_RESOURCE_GROUP, TF_BACKEND_STORAGE_ACCOUNT
#   TF_BACKEND_CONTAINER, TF_BACKEND_KEY_PREFIX
# Configure required reviewers on `${ENV_NAME}-apply` to gate the apply step.

name: ${ENV_NAME}-cd

on:
  push:
    branches: [main]
    paths:
      - "${WORKING_DIR}/**"
      - "${WORKING_DIR}/${TFVARS_DIR}/${ENV_NAME}.tfvars"
      - ".github/workflows/${ENV_NAME}-cd.yml"
  workflow_dispatch:
    inputs:
      plan_only:
        description: "Plan only (no apply)"
        type: boolean
        default: false

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  cd:
    uses: ${OWNER}/terraform-pipelines-github/.github/workflows/terraform-cd.yml@${PIPELINES_REF}
    with:
      environment: ${ENV_NAME}
      configs: '${CONFIGS_JSON}'
      plan_only: ${{ github.event_name == 'workflow_dispatch' && inputs.plan_only || false }}
      working_dir: ${WORKING_DIR}
      tfvars_dir: ${TFVARS_DIR}
      runs_on: '${RUNS_ON}'
