package main

import rego.v1

_strict := {"allow_recreate": false, "destroy_mode": false}

test_small_create_passes if {
	# A routine feature add (e.g. a DNS zone + link) is a small all-create diff.
	plan := {"resource_changes": [
		{"address": "azurerm_private_dns_zone.sql", "change": {"actions": ["create"]}},
		{"address": "azurerm_private_dns_zone_virtual_network_link.sql", "change": {"actions": ["create"]}},
	]}
	count(deny) == 0 with input as plan with data.params as _strict
}

test_noop_and_update_pass if {
	plan := {"resource_changes": [
		{"address": "a", "change": {"actions": ["no-op"]}},
		{"address": "b", "change": {"actions": ["update"]}},
	]}
	count(deny) == 0 with input as plan with data.params as _strict
}

test_delete_denied if {
	plan := {"resource_changes": [{"address": "azurerm_storage_account.this", "change": {"actions": ["delete"]}}]}
	count(deny) > 0 with input as plan with data.params as _strict
}

test_replace_denied if {
	# Replace == delete+create; recreating a live resource is destructive.
	plan := {"resource_changes": [{"address": "azurerm_private_endpoint.aoai", "change": {"actions": ["delete", "create"]}}]}
	count(deny) > 0 with input as plan with data.params as _strict
}

test_override_allows_delete if {
	plan := {"resource_changes": [{"address": "a", "change": {"actions": ["delete"]}}]}
	count(deny) == 0 with input as plan with data.params as {"allow_recreate": true, "destroy_mode": false}
}

test_destroy_mode_allows_delete if {
	plan := {"resource_changes": [{"address": "a", "change": {"actions": ["delete"]}}]}
	count(deny) == 0 with input as plan with data.params as {"allow_recreate": false, "destroy_mode": true}
}

test_mass_create_denied if {
	# 21 creates (> threshold 20) with zero deletes = empty-state rebuild tell.
	chs := [{"address": sprintf("r%d", [i]), "change": {"actions": ["create"]}} | some i in numbers.range(1, 21)]
	count(deny) > 0 with input as {"resource_changes": chs} with data.params as _strict
}

test_mass_create_override_passes if {
	chs := [{"address": sprintf("r%d", [i]), "change": {"actions": ["create"]}} | some i in numbers.range(1, 21)]
	count(deny) == 0 with input as {"resource_changes": chs} with data.params as {"allow_recreate": true, "destroy_mode": false}
}

test_missing_params_fails_safe if {
	# No params document at all => override undefined => guard stays active.
	plan := {"resource_changes": [{"address": "a", "change": {"actions": ["delete"]}}]}
	count(deny) > 0 with input as plan
}
