---
name: nerf-az-resource
description: "Generic Azure resource and resource group inspection tools"
targets: ["*"]
---

# nerf-az-resource

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Generic tools for listing and inspecting Azure resources and resource groups.
Use az-resource-list to find resources by group, type, or tag.
Use az-resource-show to fetch a resource by full ID.
Use az-group-list and az-group-show for resource groups.
All tools accept --subscription to target a specific subscription.

## nerf-az-resource-list

List Azure resources, optionally filtered by group, type, or tag.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-resource/scripts/nerf-az-resource-list [--resource-group|-g <resource_group>] [--resource-type <resource_type>] [--tag <tag>] [--subscription <subscription>]`
**Maps to:** `az resource list <resource_group> <resource_type> <tag> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--resource-type` (optional): Filter by resource type (e.g. Microsoft.KeyVault/vaults)
- `--tag` (optional): Filter by tag (e.g. env=staging)
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-resource-show

Show full details for a resource by ID.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-resource/scripts/nerf-az-resource-show [--subscription <subscription>] <resource_id>`
**Maps to:** `az resource show --ids <resource_id> <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<resource_id>` (required): Full resource ID (/subscriptions/.../resourceGroups/.../providers/...)

---

## nerf-az-group-list

List resource groups in a subscription.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-resource/scripts/nerf-az-group-list [--subscription <subscription>]`
**Maps to:** `az group list <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-group-show

Show details for a single resource group.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-resource/scripts/nerf-az-group-show [--subscription <subscription>] <name>`
**Maps to:** `az group show --name <name> <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Resource group name

---
