# Per-config variables. One file per config under infra/configs/, named
# <scope>-<region>-<env>.tfvars (the fleet convention):
#   configs/myapp-eus-dev.tfvars
#   configs/myapp-eus-prd.tfvars
# region alias: eus=eastus, eus2=eastus2, wus=westus, cus=centralus, ...
# env suffix LAST so `*-dev.tfvars` / `*-prd.tfvars` glob across regions.
# Shared (non-config) files use a z_ prefix so they sort to the bottom:
#   z_backend.tfvars, z_common.tfvars, z_tags.yaml
#
# Render with envsubst:
#   export SUBSCRIPTION_ID=<your-sub-guid>
#   export LOCATION=eastus
#   export ENV_NAME=dev
#   envsubst < templates/tfvars.tpl > configs/myapp-eus-dev.tfvars
#
# Add your own stack-specific variables below the standard block.

subscription_id = "${SUBSCRIPTION_ID}"
location        = "${LOCATION}"
environment     = "${ENV_NAME}"

# --- stack-specific variables go here ---
# Example:
#   project_name = "myapp"
#   instance_count = 2
