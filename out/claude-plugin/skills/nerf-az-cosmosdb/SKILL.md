---
name: nerf-az-cosmosdb
description: "Azure Cosmos DB account inspection tools (network access, VNet rules, databases)"
targets: ["*"]
---

# nerf-az-cosmosdb

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting Cosmos DB account configuration. az-cosmosdb-show
reports publicNetworkAccess, isVirtualNetworkFilterEnabled,
virtualNetworkRules, and the private endpoint connections list.
Use during private-networking validation to confirm VNet filtering
is active and the public surface is restricted.
All tools accept --subscription to target a specific subscription.

## nerf-az-cosmosdb-list

List Cosmos DB accounts (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-cosmosdb/scripts/nerf-az-cosmosdb-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az cosmosdb list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-cosmosdb-show

Show Cosmos DB account details (network access, VNet rules, private endpoints).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-cosmosdb/scripts/nerf-az-cosmosdb-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az cosmosdb show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the account
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Cosmos DB account name

---

## nerf-az-cosmosdb-database-list

List SQL databases in a Cosmos DB account.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-cosmosdb/scripts/nerf-az-cosmosdb-database-list --resource-group|-g <resource_group> [--subscription <subscription>] <account_name>`
**Maps to:** `az cosmosdb sql database list --resource-group <resource_group> --account-name <account_name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the account
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<account_name>` (required): Cosmos DB account name

---

## nerf-az-cosmosdb-network-rule-list

List virtual network rules on a Cosmos DB account.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-cosmosdb/scripts/nerf-az-cosmosdb-network-rule-list --resource-group|-g <resource_group> [--subscription <subscription>] <account_name>`
**Maps to:** `az cosmosdb network-rule list --resource-group <resource_group> --name <account_name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the account
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<account_name>` (required): Cosmos DB account name

---
