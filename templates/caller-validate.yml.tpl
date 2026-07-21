# Caller workflow that consumes the reusable terraform-validate.yml on PR.
# Drop this in your repo at .github/workflows/terraform-validate.yml
#
# Render with envsubst:
#   export OWNER=BRBuffington
#   export PIPELINES_REF=main
#   export WORKING_DIR=.
#   export RUNS_ON='"ubuntu-latest"'
#   envsubst < templates/caller-validate.yml.tpl > .github/workflows/terraform-validate.yml

name: terraform-validate

on:
  pull_request:
    paths:
      - "${WORKING_DIR}/**"
      - ".github/workflows/terraform-validate.yml"
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  validate:
    uses: ${OWNER}/terraform-pipelines-github/.github/workflows/terraform-validate.yml@${PIPELINES_REF}
    with:
      working_dir: ${WORKING_DIR}
      runs_on: '${RUNS_ON}'
