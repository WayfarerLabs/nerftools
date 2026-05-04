---
name: nerf-az-pipelines
description: "Azure Pipelines tools for viewing pipeline status and run history"
targets: ["*"]
---

# nerf-az-pipelines

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools query Azure Pipelines. The organization and project are
auto-detected from the git remote; pass --project to target a different
project in the same org. Use az-pipelines-list to see all pipelines,
az-pipelines-runs to see recent runs across all pipelines, and
az-pipelines-check to inspect a specific pipeline with its recent run
history. Use az-pipelines-run-show to drill into a single run.

## nerf-az-pipelines-list

List all pipelines in the Azure DevOps project.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-pipelines/scripts/nerf-az-pipelines-list [--project|-p <project>]`
**Maps to:** `az pipelines list <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

---

## nerf-az-pipelines-runs

List the 20 most recent pipeline runs across all pipelines.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-pipelines/scripts/nerf-az-pipelines-runs [--project|-p <project>]`
**Maps to:** `az pipelines runs list --top 20 <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

---

## nerf-az-pipelines-check

Show details and the 10 most recent runs for a specific pipeline (by ID).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-pipelines/scripts/nerf-az-pipelines-check [--project|-p <project>] <pipeline_id>`
**Maps to:** `az pipelines runs list --pipeline-ids <pipeline_id> --top 10 <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

**Arguments:**

- `<pipeline_id>` (required): Pipeline ID (numeric, from az-pipelines-list). must match `^[0-9]+$`

---

## nerf-az-pipelines-run-show

Show details for a single pipeline run (by run ID). Returns the run's status, result, source branch, queue/start/finish times, requesting identity, and the URL to view it in the Azure DevOps UI..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-pipelines/scripts/nerf-az-pipelines-run-show [--project|-p <project>] <run_id>`
**Maps to:** `az pipelines runs show --id <run_id> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

**Arguments:**

- `<run_id>` (required): Pipeline run ID (numeric, from az-pipelines-runs or az-pipelines-check). must match `^[0-9]+$`

---
