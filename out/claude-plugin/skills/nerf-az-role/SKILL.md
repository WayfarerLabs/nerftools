---
name: nerf-az-role
description: "Azure RBAC inspection tools (role assignments, role definitions)"
targets: ["*"]
---

# nerf-az-role

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting Azure RBAC. az-role-assignment-list supports the
reliable "--all --assignee <principal>" form that surfaces orphaned
assignments which other queries miss. az-role-definition-list looks up
role names and their permissions.
All tools accept --subscription to target a specific subscription.

## nerf-az-role-assignment-list

List role assignments. Supports filtering by assignee, scope, role, and resource group. --all is recommended when looking up assignments by principal (catches orphaned assignments at any scope).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-role/scripts/nerf-az-role-assignment-list [--all] [--assignee <assignee>] [--scope <scope>] [--role <role>] [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az role assignment list <all> <assignee> <scope> <role> <resource_group> <subscription> --output json`

**Switches:**

- `--all`: Show assignments at all scopes (recommended with --assignee)

**Options:**

- `--assignee` (optional): User UPN, group object ID, or service principal object ID
- `--scope` (optional): Scope to filter by (full Azure resource ID)
- `--role` (optional): Role name or definition ID to filter by
- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-role-assignment-by-id

Fetch role assignments by full ID. Wraps "az role assignment list --ids" (the Azure CLI does not have a "show" subcommand for role assignments), so the result is always a JSON array -- typically with one element when the ID exists, empty when it does not.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-role/scripts/nerf-az-role-assignment-by-id [--subscription <subscription>] <assignment_id>`
**Maps to:** `az role assignment list --ids <assignment_id> <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<assignment_id>` (required): Full role assignment resource ID

---

## nerf-az-role-definition-list

List role definitions (optionally filtered by name or scope).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-role/scripts/nerf-az-role-definition-list [--custom-role-only] [--name|-n <name>] [--scope <scope>] [--subscription <subscription>]`
**Maps to:** `az role definition list <name> <scope> <custom_role_only> <subscription> --output json`

**Switches:**

- `--custom-role-only`: Show only custom (non-built-in) roles

**Options:**

- `--name|-n` (optional): Role name (e.g. "Network Contributor")
- `--scope` (optional): Scope to filter by (full Azure resource ID)
- `--subscription` (optional): Subscription name or ID (defaults to active)

---
