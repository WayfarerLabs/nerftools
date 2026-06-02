---
name: nerf-az-pipelines
description: "Azure Pipelines tools for viewing pipeline status and run history"
targets: ["*"]
---

# nerf-az-pipelines

These tools are available as scripts within this skill. Call them using the paths shown in each usage line.

These tools query Azure Pipelines. The organization and project are
auto-detected from the git remote in the current directory. Pass
--project to target a different project, or -C <directory> to resolve
the project from the git remote of a sub-directory (useful when
multiple repos live under one workspace root and you don't want to cd
around). Use az-pipelines-list to see all pipelines, az-pipelines-runs
to see recent runs across all pipelines, and az-pipelines-check to
inspect a specific pipeline with its recent run history. Use
az-pipelines-run-show to drill into a single run.
Use az-pipelines-run-timeline to see step-by-step status for a failed
run and az-pipelines-run-log to fetch a specific step's log content.

## nerf-az-pipelines-list

List all pipelines in the Azure DevOps project.

**Usage:** `scripts/nerf-az-pipelines-list [--project|-p <project>] [-C <directory>]`
**Maps to:** `az pipelines list <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

---

## nerf-az-pipelines-runs

List the 20 most recent pipeline runs across all pipelines.

**Usage:** `scripts/nerf-az-pipelines-runs [--project|-p <project>] [-C <directory>]`
**Maps to:** `az pipelines runs list --top 20 <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

---

## nerf-az-pipelines-check

Show details and the 10 most recent runs for a specific pipeline (by ID).

**Usage:** `scripts/nerf-az-pipelines-check [--project|-p <project>] [-C <directory>] <pipeline_id>`
**Maps to:** `az pipelines runs list --pipeline-ids <pipeline_id> --top 10 <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<pipeline_id>` (required): Pipeline ID (numeric, from az-pipelines-list). must match `^[0-9]+$`

---

## nerf-az-pipelines-run-show

Show details for a single pipeline run (by run ID). Returns the run's status, result, source branch, queue/start/finish times, requesting identity, and the URL to view it in the Azure DevOps UI.

**Usage:** `scripts/nerf-az-pipelines-run-show [--project|-p <project>] [-C <directory>] <run_id>`
**Maps to:** `az pipelines runs show --id <run_id> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<run_id>` (required): Pipeline run ID (numeric, from az-pipelines-runs or az-pipelines-check). must match `^[0-9]+$`

---

## nerf-az-pipelines-run-timeline

Fetch the stage/job/task tree for a pipeline run, highlighting failures. Failed tasks include their log ID for use with az-pipelines-run-log. Pass --json for raw timeline output instead of the formatted tree.

**Usage:** `scripts/nerf-az-pipelines-run-timeline [--json] [--project|-p <project>] [-C <directory>] <run_id>`

**Switches:**

- `--json`: Output raw timeline JSON instead of the formatted tree

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the run, or from the git remote if -C is passed)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<run_id>` (required): Pipeline run ID (numeric, from az-pipelines-runs or az-pipelines-check). must match `^[0-9]+$`

---

## nerf-az-pipelines-run-log

Fetch log content for a specific task in a pipeline run. By default shows ##[error] lines plus the last 100 lines. Use --tail N for a different window, --errors-only to filter to error/exception lines, or --full for the complete log. The log ID for a failed task comes from az-pipelines-run-timeline.

**Usage:** `scripts/nerf-az-pipelines-run-log [--full] [--errors-only] [--tail <tail>] [--project|-p <project>] [-C <directory>] <run_id> <log_id>`

**Switches:**

- `--full`: Show the complete log instead of the default error+tail view
- `--errors-only`: Show only lines containing errors/exceptions

**Options:**

- `--tail` (optional): Number of trailing lines to show in the default view (default 100). must match `^[1-9][0-9]*$`
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the run, or from the git remote if -C is passed)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<run_id>` (required): Pipeline run ID (numeric, from az-pipelines-runs or az-pipelines-check). must match `^[0-9]+$`
- `<log_id>` (required): Log ID (numeric, from az-pipelines-run-timeline output). must match `^[0-9]+$`

---

_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? Use the `nerf-report` skill._
