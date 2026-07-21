package main

import rego.v1

_strict_versions := {
	"allow_recreate": false,
	"allow_version_rollback": false,
	"destroy_mode": false,
	"event_name": "push",
}

_container_plan(before_image, after_image) := {"resource_changes": [{
	"address": "azurerm_container_app.corpus_mcp",
	"type": "azurerm_container_app",
	"change": {
		"actions": ["update"],
		"before": {"template": [{"container": [{
			"name": "corpus-mcp",
			"image": before_image,
		}]}]},
		"after": {"template": [{"container": [{
			"name": "corpus-mcp",
			"image": after_image,
		}]}]},
	},
}]}

test_container_image_downgrade_is_denied if {
	plan := _container_plan(
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.29",
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.27",
	)
	count(deny) > 0 with input as plan with data.params as _strict_versions
}

test_container_image_upgrade_passes if {
	plan := _container_plan(
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.27",
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.29",
	)
	count(deny) == 0 with input as plan with data.params as _strict_versions
}

test_semantic_minor_upgrade_passes if {
	plan := _container_plan(
		"registry.example/app:1.9.9",
		"registry.example/app:1.10.0",
	)
	count(deny) == 0 with input as plan with data.params as _strict_versions
}

test_stable_to_prerelease_is_denied if {
	plan := _container_plan(
		"registry.example/app:1.0.0",
		"registry.example/app:1.0.0-alpha",
	)
	count(deny) > 0 with input as plan with data.params as _strict_versions
}

test_prerelease_to_stable_passes if {
	plan := _container_plan(
		"registry.example/app:1.0.0-alpha",
		"registry.example/app:1.0.0",
	)
	count(deny) == 0 with input as plan with data.params as _strict_versions
}

test_ambiguous_prerelease_change_is_denied if {
	plan := _container_plan(
		"registry.example/app:1.0.0-alpha.2",
		"registry.example/app:1.0.0-alpha.1",
	)
	count(deny) > 0 with input as plan with data.params as _strict_versions
}

test_same_version_build_change_is_denied if {
	plan := _container_plan(
		"registry.example/app:1.0.0+build.2",
		"registry.example/app:1.0.0+build.1",
	)
	count(deny) > 0 with input as plan with data.params as _strict_versions
}

test_explicit_rollback_override_passes if {
	plan := _container_plan(
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.29",
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.27",
	)
	params := {
		"allow_recreate": false,
		"allow_version_rollback": true,
		"destroy_mode": false,
		"event_name": "workflow_dispatch",
	}
	count(deny) == 0 with input as plan with data.params as params
}

test_push_cannot_enable_rollback_override if {
	plan := _container_plan(
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.29",
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.27",
	)
	params := {
		"allow_recreate": false,
		"allow_version_rollback": true,
		"destroy_mode": false,
		"event_name": "push",
	}
	count(deny) > 0 with input as plan with data.params as params
}

test_missing_params_keeps_rollback_guard_active if {
	plan := _container_plan(
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.29",
		"acrbbufhandoffeus.azurecr.io/corpus-mcp:0.27",
	)
	count(deny) > 0 with input as plan
}

test_unverifiable_digest_change_is_denied if {
	plan := _container_plan(
		"registry.example/app@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
		"registry.example/app@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
	)
	count(deny) > 0 with input as plan with data.params as _strict_versions
}

test_unchanged_digest_passes if {
	image := "registry.example/app@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
	plan := _container_plan(image, image)
	count(deny) == 0 with input as plan with data.params as _strict_versions
}

test_initial_container_app_create_passes if {
	plan := {"resource_changes": [{
		"address": "azurerm_container_app.new",
		"type": "azurerm_container_app",
		"change": {
			"actions": ["create"],
			"before": null,
			"after": {"template": [{"container": [{
				"name": "app",
				"image": "registry.example/app:1.0.0",
			}]}]},
		},
	}]}
	count(deny) == 0 with input as plan with data.params as _strict_versions
}

test_non_container_resource_is_ignored if {
	plan := {"resource_changes": [{
		"address": "azurerm_linux_web_app.example",
		"type": "azurerm_linux_web_app",
		"change": {
			"actions": ["update"],
			"before": {"image": "registry.example/app:2.0.0"},
			"after": {"image": "registry.example/app:1.0.0"},
		},
	}]}
	count(deny) == 0 with input as plan with data.params as _strict_versions
}
