# Backend config for `terraform init -backend-config=<this file>`.
# Render with envsubst (no Python required):
#
#   export RESOURCE_GROUP_NAME=rg-tfstate-mine
#   export STORAGE_ACCOUNT_NAME=sttfstatemine01
#   export CONTAINER_NAME=tfstate
#   export KEY_PREFIX=my-stack
#   export CONFIG_NAME=myapp-eus-dev    # <scope>-<region>-<env>, matches the tfvars basename
#   envsubst < templates/backend.hcl.tpl > backend.hcl
#
# After rendering:
#   terraform init -backend-config=backend.hcl
#
# In the reusable CD workflow you do NOT use this file directly -- the
# workflow passes `-backend-config=key=value` flags from GitHub Environment
# vars (TF_BACKEND_RESOURCE_GROUP, TF_BACKEND_STORAGE_ACCOUNT,
# TF_BACKEND_CONTAINER, TF_BACKEND_KEY_PREFIX). This file is for LOCAL
# init only.

resource_group_name  = "${RESOURCE_GROUP_NAME}"
storage_account_name = "${STORAGE_ACCOUNT_NAME}"
container_name       = "${CONTAINER_NAME}"
key                  = "${KEY_PREFIX}/${CONFIG_NAME}.tfstate"

# Non-negotiable defaults. Do NOT remove these:
#  - use_azuread_auth: shared-key auth must be disabled on the SA; AAD only.
#  - use_oidc: federated identity (no client secret on the runner).
use_azuread_auth = true
use_oidc         = true
