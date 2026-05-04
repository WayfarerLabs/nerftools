---
name: nerf-az-keyvault
description: "Azure Key Vault inspection tools (network ACLs, secret metadata)"
targets: ["*"]
---

# nerf-az-keyvault

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting Key Vault configuration and secret metadata.
az-keyvault-show reports network ACLs, public network access, RBAC mode,
and private endpoint connections. az-keyvault-secret-list returns secret
names only (no values). az-keyvault-secret-stats returns length,
content type, and last_modified for a single secret without revealing
the value -- use last_modified to detect rotation.
All tools accept --subscription to target a specific subscription.

## nerf-az-keyvault-list

List Key Vaults (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-keyvault/scripts/nerf-az-keyvault-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az keyvault list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-keyvault-show

Show Key Vault details (network ACLs, publicNetworkAccess, RBAC mode, private endpoints).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-keyvault/scripts/nerf-az-keyvault-show [--resource-group|-g <resource_group>] [--subscription <subscription>] <name>`
**Maps to:** `az keyvault show --name <name> <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Resource group containing the vault (optional, helps with disambiguation)
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Key Vault name

---

## nerf-az-keyvault-network-rule-list

List explicit network rules on a Key Vault.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-keyvault/scripts/nerf-az-keyvault-network-rule-list [--resource-group|-g <resource_group>] [--subscription <subscription>] <vault_name>`
**Maps to:** `az keyvault network-rule list --name <vault_name> <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Resource group containing the vault (optional)
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<vault_name>` (required): Key Vault name

---

## nerf-az-keyvault-secret-list

List secret names in a Key Vault (no values).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-keyvault/scripts/nerf-az-keyvault-secret-list [--subscription <subscription>] <vault_name>`
**Maps to:** `az keyvault secret list --vault-name <vault_name> <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<vault_name>` (required): Key Vault name

---

## nerf-az-keyvault-secret-stats

Show metadata for a secret value (length, content type, last modified) without revealing any characters. Use last_modified to detect rotation. No content-derived fingerprint is emitted: a deterministic fingerprint would let an agent verify guessed values offline.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-keyvault/scripts/nerf-az-keyvault-secret-stats [--subscription <subscription>] <vault_name> <name>`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<vault_name>` (required): Key Vault name
- `<name>` (required): Secret name

---
