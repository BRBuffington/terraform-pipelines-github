# Drop this file into the root of your Terraform stack as `backend.tf` (or
# merge into your existing `versions.tf`). The `backend "azurerm" {}` block
# is intentionally empty -- all values come from `terraform init -backend-config=...`
# at runtime so the same stack can target multiple state files (one per config).
#
# This file is verbatim -- there are NO placeholders to substitute. The
# parameterization lives in the backend.hcl that the reusable CD workflow
# passes via `-backend-config=`.
#
# Required: the consuming pipeline must always pass:
#   use_azuread_auth = true   (MSAL auth to the state blob; shared keys MUST be off)
#   use_oidc         = true   (federated identity from GitHub Actions, no client secret)
# The reusable CD workflow at .github/workflows/terraform-cd.yml does this for you.

terraform {
  required_version = ">= 1.9.0"

  backend "azurerm" {}

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}
