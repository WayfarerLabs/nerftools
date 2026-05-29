---
name: nerf-az-repos
description: "Azure Repos tools for viewing and creating pull requests"
targets: ["*"]
---

# nerf-az-repos

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools interact with Azure Repos pull requests. The organization
and project are auto-detected from the git remote in the current
directory. Pass --project to target a different project, or -C
<directory> to resolve the project from the git remote of a
sub-directory under the workspace (useful when multiple repos live
under one workspace root and you don't want to cd around).
Use az-repos-pr-list to see open PRs, az-repos-pr-show to inspect a
specific PR, and az-repos-pr-create to create a new PR from the
current branch. az-repos-pr-edit updates a PR's title and/or
description. az-repos-pr-set-status changes a PR's lifecycle state
(active / abandoned / completed). az-repos-pr-vote casts or resets
a review vote on a PR.

## nerf-az-repos-pr-list

List pull requests in the project as JSON.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-list [--status <status>] [--top <top>] [--creator <creator>] [--reviewer <reviewer>] [--project|-p <project>] [-C <directory>]`
**Maps to:** `az repos pr list <status> <top> <creator> <reviewer> <project> --output json`

**Options:**

- `--status` (optional): Filter by status (default: active). one of `active`, `abandoned`, `completed`, `all`
- `--top` (optional): Maximum number of PRs to return (default 10). must match `^[0-9]+$`
- `--creator` (optional): Filter by PR creator
- `--reviewer` (optional): Filter by reviewer
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

---

## nerf-az-repos-pr-show

Show full details for a pull request as JSON.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-show [--project|-p <project>] [-C <directory>] <pr_id>`
**Maps to:** `az repos pr show --id <pr_id> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`

---

## nerf-az-repos-pr-comments

List all comment threads on a pull request as JSON. Project and repository are auto-detected from the git remote (origin) in the current directory; pass -C <directory> to read the remote from a different repo under the workspace, or --project to override just the project (the repository is always taken from the remote URL).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-comments [--project|-p <project>] [-C <directory>] <pr_id>`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (overrides auto-detection from the origin remote)
- `-C` (optional): Read the origin remote from this directory instead of cwd (must be under cwd)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`

---

## nerf-az-repos-pr-create

Create a pull request from the current branch (or from the branch in the -C directory). Source branch is auto-detected from HEAD. The target branch defaults to the repo's default branch unless --target-branch is given. Cannot be run from detached HEAD or from main. When -C is passed, the project, repository, and source branch are all resolved from the given directory's git remote and HEAD.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-create [--draft] [--target-branch|-t <target_branch>] [--project|-p <project>] [--repository|-r <repository>] [--source-branch|-s <source_branch>] [-C <directory>] <title> <description>`
**Maps to:** `az repos pr create --title <title> --description <description> <draft> <target_branch> <project> <repository> <source_branch> --output json`

**Switches:**

- `--draft`: Create the PR as a draft

**Options:**

- `--target-branch|-t` (optional): Target branch for the PR (defaults to the repo's default branch). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$`
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `--repository|-r` (optional): Azure DevOps repository name or ID (auto-detected from the git remote if omitted)
- `--source-branch|-s` (optional): Source branch of the PR (auto-detected from HEAD if omitted; required when -C is passed since az reads HEAD from cwd, not from -C). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$`
- `-C` (optional): Resolve project, repository, and source branch from the git remote/HEAD of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<title>` (required): PR title
- `<description>` (required): PR description (body text; supports markdown)

---

## nerf-az-repos-pr-set-status

Update a pull request's lifecycle status. Use "abandoned" to close a PR without merging, "active" to reactivate an abandoned PR, or "completed" to merge it (Azure DevOps will reject "completed" if required approvals or policies are not satisfied).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-set-status [--project|-p <project>] [-C <directory>] <pr_id> <status>`
**Maps to:** `az repos pr update --id <pr_id> --status <status> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`
- `<status>` (required): New status. one of `active`, `abandoned`, `completed`

---

## nerf-az-repos-pr-edit

Edit a pull request's title and/or description. At least one of --title or --description must be provided. Useful for keeping a PR's metadata in sync with its scope as the branch evolves. Does not change the PR's status, target branch, or reviewers.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-edit [--title <title>] [--description <description>] [--project|-p <project>] [-C <directory>] <pr_id>`
**Maps to:** `az repos pr update --id <pr_id> <title> <description> <project> --output json`

**Options:**

- `--title` (optional): New PR title
- `--description` (optional): New PR description (body text; supports markdown)
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`

---

## nerf-az-repos-pr-vote

Cast or reset a review vote on a pull request. The signed-in identity must be a reviewer (or able to add itself) on the PR. Use "reset" to clear an existing vote.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-repos/scripts/nerf-az-repos-pr-vote [--project|-p <project>] [-C <directory>] <pr_id> <vote>`
**Maps to:** `az repos pr set-vote --id <pr_id> --vote <vote> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<pr_id>` (required): Pull request ID (numeric). must match `^[0-9]+$`
- `<vote>` (required): Vote to cast. one of `approve`, `approve-with-suggestions`, `reject`, `reset`, `wait-for-author`

---
