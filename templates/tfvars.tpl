# Per-environment variables. One file per config:
#   environments/dev.tfvars
#   environments/prod.tfvars
#
# Render with envsubst:
#   export SUBSCRIPTION_ID=<your-sub-guid>
#   export LOCATION=eastus
#   export ENV_NAME=dev
#   envsubst < templates/tfvars.tpl > environments/dev.tfvars
#
# Add your own stack-specific variables below the standard block.

subscription_id = "${SUBSCRIPTION_ID}"
location        = "${LOCATION}"
environment     = "${ENV_NAME}"

# --- stack-specific variables go here ---
# Example:
#   project_name = "myapp"
#   instance_count = 2
