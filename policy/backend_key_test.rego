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

test_mixed_case_prefix_allowed if {
	# A mixed-case TF_BACKEND_KEY_PREFIX (e.g. a repo name) is valid.
	count(deny) == 0 with input as {"key": "MyStack/Dev.tfstate"}
}

test_multi_level_prefix_allowed if {
	# A slash-containing prefix (team/stack) yields a multi-segment key.
	count(deny) == 0 with input as {"key": "team/corpus-search/tier2.tfstate"}
}

test_missing_tfstate_suffix_denied if {
	count(deny) > 0 with input as {"key": "corpus-search/tier2"}
}
