# Guard existing Azure Container Apps against silent image rollback. Terraform
# plan JSON carries both the live image (before) and desired image (after), so
# unrelated applies cannot downgrade a versioned image without an explicit,
# typed workflow-dispatch override.
package main

import rego.v1

_version_rollback_override if {
	data.params.allow_version_rollback == true
	data.params.event_name == "workflow_dispatch"
}

_container_images(state) := {container.name: container.image |
	some template in state.template
	some container in template.container
}

_version_parts(image) := parts if {
	matches := regex.find_all_string_submatch_n(`:v?([0-9]+(?:\.[0-9]+){0,3})(?:[-+][^@]+)?(?:@sha256:[a-fA-F0-9]+)?$`, image, 1)
	count(matches) == 1
	raw_parts := [to_number(part) | some part in split(matches[0][1], ".")]
	padded := array.concat(raw_parts, [0, 0, 0, 0])
	parts := [padded[0], padded[1], padded[2], padded[3]]
}

_version_is_lower(after, before) if after[0] < before[0]

_version_is_lower(after, before) if {
	after[0] == before[0]
	after[1] < before[1]
}

_version_is_lower(after, before) if {
	after[0] == before[0]
	after[1] == before[1]
	after[2] < before[2]
}

_version_is_lower(after, before) if {
	after[0] == before[0]
	after[1] == before[1]
	after[2] == before[2]
	after[3] < before[3]
}

_changed_container_images contains change if {
	some resource in input.resource_changes
	resource.type == "azurerm_container_app"
	resource.change.before != null
	resource.change.after != null
	before_images := _container_images(resource.change.before)
	after_images := _container_images(resource.change.after)
	some name, before_image in before_images
	after_image := after_images[name]
	before_image != after_image
	change := {
		"address": resource.address,
		"container": name,
		"before": before_image,
		"after": after_image,
	}
}

_downgrades contains change if {
	some change in _changed_container_images
	before_version := _version_parts(change.before)
	after_version := _version_parts(change.after)
	_version_is_lower(after_version, before_version)
}

_unverifiable_changes contains change if {
	some change in _changed_container_images
	not _version_parts(change.before)
}

_unverifiable_changes contains change if {
	some change in _changed_container_images
	not _version_parts(change.after)
}

deny contains msg if {
	not _version_rollback_override
	count(_downgrades) > 0
	msg := sprintf(
		"plan rolls back %d container image(s): %v. Version rollback requires the user's explicit consent and a workflow_dispatch with allow_version_rollback=true; push events can never override this guard.",
		[count(_downgrades), _downgrades],
	)
}

deny contains msg if {
	not _version_rollback_override
	count(_unverifiable_changes) > 0
	msg := sprintf(
		"plan changes %d container image(s) whose versions cannot be compared: %v. The gate fails closed; use versioned image references or obtain explicit consent and dispatch with allow_version_rollback=true.",
		[count(_unverifiable_changes), _unverifiable_changes],
	)
}
