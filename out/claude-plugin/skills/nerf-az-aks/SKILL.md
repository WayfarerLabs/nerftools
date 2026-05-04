---
name: nerf-az-aks
description: "Azure Kubernetes Service inspection and access tools"
targets: ["*"]
---

# nerf-az-aks

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting AKS clusters and fetching cluster credentials.
az-aks-show reports the apiServerAccessProfile (private cluster flag,
private FQDN). az-aks-get-credentials merges the cluster's kubeconfig
into ~/.kube/config so that kubectl tools can target the cluster.
az-aks-command-invoke runs a command via the AKS run-command API
(works without VNet access; useful for break-glass diagnostics).
All tools accept --subscription to target a specific subscription.

## nerf-az-aks-list

List AKS clusters (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az aks list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-aks-show

Show AKS cluster details (network profile, private cluster flag, FQDN).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az aks show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the cluster
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): AKS cluster name

---

## nerf-az-aks-nodepool-list

List node pools on an AKS cluster.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-nodepool-list --resource-group|-g <resource_group> [--subscription <subscription>] <cluster_name>`
**Maps to:** `az aks nodepool list --resource-group <resource_group> --cluster-name <cluster_name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the cluster
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<cluster_name>` (required): AKS cluster name

---

## nerf-az-aks-nodepool-show

Show details for a single node pool (size, autoscaler config, taints).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-nodepool-show --resource-group|-g <resource_group> --cluster-name <cluster_name> [--subscription <subscription>] <name>`
**Maps to:** `az aks nodepool show --resource-group <resource_group> --cluster-name <cluster_name> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the cluster
- `--cluster-name` (required): AKS cluster name
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Node pool name

---

## nerf-az-aks-get-versions

List supported AKS Kubernetes versions in a region.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-get-versions [--subscription <subscription>] <location>`
**Maps to:** `az aks get-versions --location <location> <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<location>` (required): Azure region (e.g. eastus2)

---

## nerf-az-aks-get-credentials

Merge AKS cluster credentials into ~/.kube/config so kubectl can target the cluster. Uses Azure AD/Entra; subsequent kubectl calls are scoped by the principal's Azure RBAC. Use az-aks-get-credentials-admin (separate tool, admin threat) when you need the local-account cluster-admin kubeconfig..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-get-credentials [--overwrite-existing] --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az aks get-credentials --resource-group <resource_group> --name <name> <overwrite_existing> <subscription>`

**Switches:**

- `--overwrite-existing`: Overwrite an existing kubeconfig entry with the same name

**Options:**

- `--resource-group|-g` (required): Resource group containing the cluster
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): AKS cluster name

---

## nerf-az-aks-get-credentials-admin

Fetch the cluster-admin (local accounts) kubeconfig for an AKS cluster. The fetched credentials grant cluster-admin via static client cert and bypass Azure RBAC entirely, so subsequent kubectl calls operate at the cluster-admin level. Marked admin so the harness can default-deny; only use for clusters where local accounts are intentionally enabled and admin access is required..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-get-credentials-admin [--overwrite-existing] --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az aks get-credentials --admin --resource-group <resource_group> --name <name> <overwrite_existing> <subscription>`

**Switches:**

- `--overwrite-existing`: Overwrite an existing kubeconfig entry with the same name

**Options:**

- `--resource-group|-g` (required): Resource group containing the cluster
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): AKS cluster name

---

## nerf-az-aks-command-invoke

Run a kubectl/shell command on the cluster via the AKS run-command API. The command runs server-side as a managed pod with cluster-admin service-account bindings, so this is full RCE on whichever cluster --resource-group / --name (and --subscription if set) resolve to. Marked admin: ensure the harness only allows it for clusters the agent is intentionally authorized to operate on..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-aks/scripts/nerf-az-aks-command-invoke --resource-group|-g <resource_group> --name|-n <cluster_name> [--subscription <subscription>] <command...>`

**Options:**

- `--resource-group|-g` (required): Resource group containing the cluster
- `--name|-n` (required): AKS cluster name
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<command...>` (required): Command and args to run on the cluster (e.g. kubectl get pods -A)

---
