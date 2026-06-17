package backend_key

import rego.v1

test_nested_key_allowed if {
	count(deny) == 0 with input as {"key": "corpus-search/tier2.tfstate"}
}

test_nested_key_with_dash_allowed if {
	count(deny) == 0 with input as {"key": "handoff-infra/synthesizer.tfstate"}
}

test_flat_laptop_key_denied if {
	# The corpus-search incident: a flat key with no nested config segment.
	count(deny) > 0 with input as {"key": "corpus-search.tfstate"}
}

test_changeme_default_denied if {
	count(deny) > 0 with input as {"key": "changeme/tfstate"}
}

test_missing_tfstate_suffix_denied if {
	count(deny) > 0 with input as {"key": "corpus-search/tier2"}
}
