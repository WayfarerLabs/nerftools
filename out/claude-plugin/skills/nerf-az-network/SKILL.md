---
name: nerf-az-network
description: "Azure networking inspection tools (VNets, peerings, NSGs, private endpoints, DNS zones)"
targets: ["*"]
---

# nerf-az-network

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for inspecting Azure networking resources: VNets, peerings, subnets,
NSGs, private endpoints, private DNS zones, public IPs, NICs, and route
tables. Use these during validation phases to confirm resources are
configured for private access and that public surface is minimized.
All tools accept --subscription to target a specific subscription.

## nerf-az-network-vnet-list

List virtual networks (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-vnet-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az network vnet list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-network-vnet-show

Show details for a virtual network (address space, subnets, peerings).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-vnet-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az network vnet show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the VNet
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): VNet name

---

## nerf-az-network-vnet-peering-list

List peerings on a virtual network.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-vnet-peering-list --resource-group|-g <resource_group> [--subscription <subscription>] <vnet_name>`
**Maps to:** `az network vnet peering list --resource-group <resource_group> --vnet-name <vnet_name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the VNet
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<vnet_name>` (required): VNet name

---

## nerf-az-network-vnet-peering-show

Show details for a single VNet peering (peering state, address space, gateway transit).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-vnet-peering-show --resource-group|-g <resource_group> --vnet-name <vnet_name> [--subscription <subscription>] <name>`
**Maps to:** `az network vnet peering show --resource-group <resource_group> --vnet-name <vnet_name> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the VNet
- `--vnet-name` (required): VNet that owns the peering
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Peering name

---

## nerf-az-network-subnet-show

Show subnet details (delegations, private link policies, NSG/RT bindings).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-subnet-show --resource-group|-g <resource_group> --vnet-name <vnet_name> [--subscription <subscription>] <name>`
**Maps to:** `az network vnet subnet show --resource-group <resource_group> --vnet-name <vnet_name> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the VNet
- `--vnet-name` (required): VNet that owns the subnet
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Subnet name

---

## nerf-az-network-nsg-list

List network security groups (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-nsg-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az network nsg list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-network-nsg-show

Show NSG details including all security rules.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-nsg-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az network nsg show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the NSG
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): NSG name

---

## nerf-az-network-private-endpoint-list

List private endpoints (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-endpoint-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az network private-endpoint list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-network-private-endpoint-show

Show private endpoint details (target resource, connection state, NIC).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-endpoint-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az network private-endpoint show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the private endpoint
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Private endpoint name

---

## nerf-az-network-private-link-resource-list

List groupIds a resource exposes for private endpoints (e.g. vault, sqlServer).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-link-resource-list [--subscription <subscription>] <resource_id>`
**Maps to:** `az network private-link-resource list --id <resource_id> <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<resource_id>` (required): Full resource ID of the target resource

---

## nerf-az-network-private-dns-zone-list

List private DNS zones (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-dns-zone-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az network private-dns zone list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-network-private-dns-zone-show

Show details for a private DNS zone (record count, registration state).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-dns-zone-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az network private-dns zone show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the zone
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Private DNS zone name (e.g. privatelink.vaultcore.azure.net)

---

## nerf-az-network-private-dns-record-list

List record sets in a private DNS zone (all record types).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-dns-record-list --resource-group|-g <resource_group> [--subscription <subscription>] <zone_name>`
**Maps to:** `az network private-dns record-set list --resource-group <resource_group> --zone-name <zone_name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the zone
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<zone_name>` (required): Private DNS zone name

---

## nerf-az-network-private-dns-link-list

List virtual network links on a private DNS zone.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-dns-link-list --resource-group|-g <resource_group> [--subscription <subscription>] <zone_name>`
**Maps to:** `az network private-dns link vnet list --resource-group <resource_group> --zone-name <zone_name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the zone
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<zone_name>` (required): Private DNS zone name

---

## nerf-az-network-private-dns-link-show

Show details for a single virtual network link on a private DNS zone.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-private-dns-link-show --resource-group|-g <resource_group> --zone-name <zone_name> [--subscription <subscription>] <name>`
**Maps to:** `az network private-dns link vnet show --resource-group <resource_group> --zone-name <zone_name> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the zone
- `--zone-name` (required): Private DNS zone name
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Link name

---

## nerf-az-network-public-ip-list

List public IP addresses (optionally filtered by resource group).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-public-ip-list [--resource-group|-g <resource_group>] [--subscription <subscription>]`
**Maps to:** `az network public-ip list <resource_group> <subscription> --output json`

**Options:**

- `--resource-group|-g` (optional): Filter to a specific resource group
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-network-public-ip-show

Show details for a public IP (allocation method, IP address, associated resource).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-public-ip-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az network public-ip show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the public IP
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Public IP resource name

---

## nerf-az-network-nic-show

Show NIC details (private IPs, subnet, NSG association).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-nic-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az network nic show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the NIC
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): NIC name

---

## nerf-az-network-route-table-show

Show route table details (routes, associated subnets).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-network/scripts/nerf-az-network-route-table-show --resource-group|-g <resource_group> [--subscription <subscription>] <name>`
**Maps to:** `az network route-table show --resource-group <resource_group> --name <name> <subscription> --output json`

**Options:**

- `--resource-group|-g` (required): Resource group containing the route table
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<name>` (required): Route table name

---
