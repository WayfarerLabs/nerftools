---
name: nerf-az-pipelines
description: "Azure Pipelines tools for viewing pipeline status and run history"
targets: ["*"]
---

# nerf-az-pipelines

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools query Azure Pipelines. The organization and project are
auto-detected from the git remote. Use az-pipelines-list to see all
pipelines, az-pipelines-runs to see recent runs across all pipelines,
and az-pipelines-check to inspect a specific pipeline with its recent
run history.

## nerf-az-pipelines-list

List all pipelines in the Azure DevOps project.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-pipelines/scripts/nerf-az-pipelines-list`
**Maps to:** `az pipelines list --output json`

No arguments.

---

## nerf-az-pipelines-runs

List the 20 most recent pipeline runs across all pipelines.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-pipelines/scripts/nerf-az-pipelines-runs`
**Maps to:** `az pipelines runs list --top 20 --output json`

No arguments.

---

## nerf-az-pipelines-check

Show details and the 10 most recent runs for a specific pipeline (by ID).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-pipelines/scripts/nerf-az-pipelines-check <pipeline_id>`
**Maps to:** `az pipelines runs list --pipeline-ids <pipeline_id> --top 10 --output json`

**Arguments:**

- `<pipeline_id>` (required): Pipeline ID (numeric, from az-pipelines-list). must match `^[0-9]+$`

---
