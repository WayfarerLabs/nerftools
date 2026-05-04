---
name: nerf-az-monitor
description: "Azure Monitor inspection tools (activity log, metrics, diagnostic settings)"
targets: ["*"]
---

# nerf-az-monitor

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for querying Azure Monitor. az-monitor-activity-log fetches recent
activity-log entries scoped to a resource group or single resource (one
of those is required, time bounded to a configurable hours-back window
with a 168 hour cap). az-monitor-metrics-list pulls a single metric
series. az-monitor-diagnostic-settings-list audits what is wired to
Log Analytics for a given resource.
All tools accept --subscription to target a specific subscription.

## nerf-az-monitor-activity-log

Fetch recent Azure Monitor activity-log entries. Requires either --resource-group or --resource-id (mutually exclusive). Defaults to the last 1 hour; --hours-back can be raised up to 168 (7 days).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-monitor/scripts/nerf-az-monitor-activity-log [--resource-group|-g <resource_group>] [--resource-id <resource_id>] [--hours-back <hours_back>] [--subscription <subscription>]`

**Options:**

- `--resource-group|-g` (optional): Filter to a resource group (mutually exclusive with --resource-id)
- `--resource-id` (optional): Filter to a single resource (mutually exclusive with --resource-group)
- `--hours-back` (optional): How many hours back to query (default 1, max 168). must match `^[0-9]+$`
- `--subscription` (optional): Subscription name or ID (defaults to active)

---

## nerf-az-monitor-metrics-list

Fetch a single metric series for a resource.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-monitor/scripts/nerf-az-monitor-metrics-list --resource <resource_id> [--aggregation <aggregation>] [--interval <interval>] [--start-time <start_time>] [--end-time <end_time>] [--subscription <subscription>] <metric>`
**Maps to:** `az monitor metrics list --resource <resource_id> --metric <metric> <aggregation> <interval> <start_time> <end_time> <subscription> --output json`

**Options:**

- `--resource` (required): Full resource ID to query
- `--aggregation` (optional): Aggregation to apply: Average, Count, Maximum, Minimum, Total. one of `Average`, `Count`, `Maximum`, `Minimum`, `Total`
- `--interval` (optional): ISO8601 interval supported by Azure Monitor metrics. one of `PT1M`, `PT5M`, `PT15M`, `PT30M`, `PT1H`, `PT6H`, `PT12H`, `P1D`, `FULL`
- `--start-time` (optional): ISO8601 start time
- `--end-time` (optional): ISO8601 end time
- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<metric>` (required): Metric name (e.g. CpuPercent, ServerLogins)

---

## nerf-az-monitor-diagnostic-settings-list

List diagnostic settings on a resource (what is wired to Log Analytics, Event Hubs, Storage).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-monitor/scripts/nerf-az-monitor-diagnostic-settings-list [--subscription <subscription>] <resource_id>`
**Maps to:** `az monitor diagnostic-settings list --resource <resource_id> <subscription> --output json`

**Options:**

- `--subscription` (optional): Subscription name or ID (defaults to active)

**Arguments:**

- `<resource_id>` (required): Full resource ID to query

---
