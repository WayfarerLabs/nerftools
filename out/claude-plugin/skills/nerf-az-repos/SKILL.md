---
name: nerf-az-repos
description: "Azure Repos tools for viewing and creating pull requests"
targets: ["*"]
---

# nerf-az-repos

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools interact with Azure Repos pull requests. The organization
and project are auto-detected from the git remote; pass --project to
target a different project in the same org. Use az-repos-pr-list to
see open PRs, az-repos-pr-show to inspect a specific PR, and
az-repos-pr-create to create a new PR from the current branch.
az-repos-pr-set-status changes a PR's lifecycle state
(active / abandoned / completed). az-repos-pr-vote casts or resets
a review vote on a PR.

## nerf-az-repos-pr-list

List pull requests in the project as JSON.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-list [--status <status>] [--top <top>] [--creator <creator>] [--reviewer <reviewer>] [--project|-p <project>]`
**Maps to:** `az repos pr list <status> <top> <creator> <reviewer> <project> --output json`

**Options:**

- `--status` (optional): Filter by status (default: active). one of `active`, `abandoned`, `completed`, `all`
- `--top` (optional): Maximum number of PRs to return (default 10). must match `^[0-9]+$`
- `--creator` (optional): Filter by PR creator
- `--reviewer` (optional): Filter by reviewer
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

---

## nerf-az-repos-pr-show

Show full details for a pull request as JSON.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-show [--project|-p <project>] <pr_id>`
**Maps to:** `az repos pr show --id <pr_id> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`

---

## nerf-az-repos-pr-comments

List all comment threads on a pull request as JSON. Project and repository are auto-detected from the git remote (origin); pass --project to override the project (the repository is always taken from origin)..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-comments [--project|-p <project>] <pr_id>`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (overrides auto-detection from the origin remote)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`

---

## nerf-az-repos-pr-create

Create a pull request from the current branch to the default target branch. Source branch is auto-detected from HEAD. Cannot be run from detached HEAD or from main..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-create [--draft] [--project|-p <project>] <title> <description>`
**Maps to:** `az repos pr create --title <title> --description <description> <draft> <project> --output json`

**Switches:**

- `--draft`: Create the PR as a draft

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

**Arguments:**

- `<title>` (required): PR title
- `<description>` (required): PR description (body text; supports markdown)

---

## nerf-az-repos-pr-set-status

Update a pull request's lifecycle status. Use "abandoned" to close a PR without merging, "active" to reactivate an abandoned PR, or "completed" to merge it (Azure DevOps will reject "completed" if required approvals or policies are not satisfied)..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-set-status [--project|-p <project>] <pr_id> <status>`
**Maps to:** `az repos pr update --id <pr_id> --status <status> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`
- `<status>` (required): New status. one of `active`, `abandoned`, `completed`

---

## nerf-az-repos-pr-vote

Cast or reset a review vote on a pull request. The signed-in identity must be a reviewer (or able to add itself) on the PR. Use "reset" to clear an existing vote..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-vote [--project|-p <project>] <pr_id> <vote>`
**Maps to:** `az repos pr set-vote --id <pr_id> --vote <vote> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`
- `<vote>` (required): Vote to cast. one of `approve`, `approve-with-suggestions`, `reject`, `reset`, `wait-for-author`

---
