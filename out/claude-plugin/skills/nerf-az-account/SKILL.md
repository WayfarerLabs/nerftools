---
name: nerf-az-account
description: "Azure subscription and identity context tools"
targets: ["*"]
---

# nerf-az-account

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting and switching the active Azure subscription.
az-account-show reports the active subscription and signed-in identity.
az-account-list enumerates all subscriptions the principal can see.
az-account-set switches the active subscription for the session.

Scope note: every az-* tool accepts --subscription. The wrappers do
not enforce a subscription allow-list; the principal's Azure RBAC is
the actual boundary. If the signed-in identity has access to
multiple subscriptions or guest access in other tenants, those are
all reachable via --subscription. Restrict the principal at the
Entra/RBAC layer if you need a tighter scope than "everything the
identity can see."

## nerf-az-account-show

Show the currently active subscription and signed-in identity.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-account/scripts/nerf-az-account-show`
**Maps to:** `az account show --output json`

No arguments.

---

## nerf-az-account-list

List all Azure subscriptions accessible to the signed-in principal.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-account/scripts/nerf-az-account-list`
**Maps to:** `az account list --output json`

No arguments.

---

## nerf-az-account-set

Switch the active Azure subscription for this session.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-account/scripts/nerf-az-account-set <subscription>`
**Maps to:** `az account set --subscription <subscription>`

**Arguments:**

- `<subscription>` (required): Subscription name or ID

---
