---
name: nerf-az-repos
description: "Azure Repos tools for viewing and creating pull requests"
targets: ["*"]
---

# nerf-az-repos

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools interact with Azure Repos pull requests. The organization and
project are auto-detected from the git remote. Use az-repos-pr-list to
see open PRs, az-repos-pr-show to inspect a specific PR, and
az-repos-pr-create to create a new PR from the current branch.

## nerf-az-repos-pr-list

List pull requests in the project as JSON.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-list [--status <status>] [--top <top>] [--creator <creator>] [--reviewer <reviewer>]`
**Maps to:** `az repos pr list <status> <top> <creator> <reviewer> --output json`

**Options:**

- `--status` (optional): Filter by status (default: active). one of `active`, `abandoned`, `completed`, `all`
- `--top` (optional): Maximum number of PRs to return (default 10). must match `^[0-9]+$`
- `--creator` (optional): Filter by PR creator
- `--reviewer` (optional): Filter by reviewer

---

## nerf-az-repos-pr-show

Show full details for a pull request as JSON.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-show <pr_id>`
**Maps to:** `az repos pr show --id <pr_id> --output json`

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`

---

## nerf-az-repos-pr-comments

List all comment threads on a pull request as JSON. Extracts the repository name from the git remote automatically..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-comments <pr_id>`

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`

---

## nerf-az-repos-pr-create

Create a pull request from the current branch to the default target branch. Source branch is auto-detected from HEAD. Cannot be run from detached HEAD or from main..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-create [--draft] <title> <description>`
**Maps to:** `az repos pr create --title <title> --description <description> <draft> --output json`

**Switches:**

- `--draft`: Create the PR as a draft

**Arguments:**

- `<title>` (required): PR title
- `<description>` (required): PR description (body text)

---
