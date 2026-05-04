---
name: nerf-az-postgres
description: "Azure Database for PostgreSQL Flexible Server inspection tools"
targets: ["*"]
---

# nerf-az-postgres

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting PostgreSQL Flexible Server configuration.
az-postgres-flexible-server-show reports the network block, including
delegated subnet, private DNS zone association, and public access
setting. Use during private-networking validation to confirm the
server is correctly attached to its private endpoint topology.
All tools accept --subscription to target a specific subscription.

## nerf-az-postgres-flexible-server-list

List PostgreSQL Flexible Servers (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-postgres/scripts/nerf-az-postgres-flexible-server-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az postgres flexible-server list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-postgres-flexible-server-show

Show PostgreSQL Flexible Server details (network block, SKU, version, HA).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-postgres/scripts/nerf-az-postgres-flexible-server-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az postgres flexible-server show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the server
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Server name

---

## nerf-az-postgres-flexible-server-firewall-rule-list

List firewall rules on a PostgreSQL Flexible Server.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-postgres/scripts/nerf-az-postgres-flexible-server-firewall-rule-list --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az postgres flexible-server firewall-rule list --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the server
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Server name

---
