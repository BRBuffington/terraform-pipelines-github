# Enforce the per-config remote-state convention: every config gets its OWN
# nested state file `<prefix>/<config>.tfstate`. A flat key (`<name>.tfstate`,
# no slash) is the laptop-style state that silently diverges from the CD
# pipeline's per-config blob — the corpus-search empty-state incident
# (2026-06-17: a CD plan init'd an empty `corpus-search/tier2.tfstate` while the
# live state sat in a flat `corpus-search.tfstate`, so the plan proposed
# rebuilding the whole stack).
#
# Pre-plan check. Input is the backend key the pipeline is about to init against:
#   {"key": "<prefix>/<config>.tfstate"}
package backend_key

import rego.v1

# Valid = at least one nested segment, a slash, then a final config segment
# ending in `.tfstate`. Accepts mixed case (Azure blob names are case-sensitive
# and a TF_BACKEND_KEY_PREFIX may be e.g. `MyStack`) and multi-level prefixes
# (`team/stack/config.tfstate`). The load-bearing invariant is ≥ 1 slash, so a
# flat `name.tfstate` (laptop-style) is still rejected.
_valid if regex.match(`^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)+\.tfstate$`, input.key)

deny contains msg if {
	not _valid
	msg := sprintf(
		"backend key %q must be '<prefix>/<config>.tfstate' (one nested state file per config). A flat or malformed key diverges laptop vs CD state and makes plans run against empty state. See the terraform-deployment skill, section 1.",
		[input.key],
	)
}
