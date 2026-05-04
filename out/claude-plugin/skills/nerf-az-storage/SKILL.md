---
name: nerf-az-storage
description: "Azure Storage Account inspection tools (network rules, public access, private endpoints)"
targets: ["*"]
---

# nerf-az-storage

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting storage account configuration. az-storage-account-show
reports network rules, allowBlobPublicAccess, and private endpoint
connections. Useful for auditing tfstate accounts and verifying public
access is appropriately restricted.
All tools accept --subscription to target a specific subscription.

## nerf-az-storage-account-list

List storage accounts (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-storage/scripts/nerf-az-storage-account-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az storage account list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-storage-account-show

Show storage account details (network rules, public access, private endpoints).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-storage/scripts/nerf-az-storage-account-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az storage account show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the storage account
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Storage account name

---

## nerf-az-storage-account-network-rule-list

List explicit network rules on a storage account.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-storage/scripts/nerf-az-storage-account-network-rule-list --resource-group|-g <resource_group> [--subscription <subscription>] <account_name>`
**Maps to:** `az storage account network-rule list --resource-group <resource_group> --account-name <account_name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the storage account
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<account_name>` (required): Storage account name

---
