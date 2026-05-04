---
name: nerf-az-devops
description: "Azure DevOps organization-level configuration tools"
targets: ["*"]
---

# nerf-az-devops

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

Tools for configuring Azure DevOps defaults that apply across the
az-boards, az-pipelines, and az-repos packages. Use
az-devops-set-default-project when the git-remote-detected project
is not the one you want to operate on by default.

## nerf-az-devops-set-default-project

Set the default Azure DevOps project for subsequent az boards, az pipelines, and az repos commands. Persists to the user's az config (~/.azure). Useful when the git remote's project is not the project you want to operate on by default..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-devops/scripts/nerf-az-devops-set-default-project <project>`
**Maps to:** `az devops configure --defaults project=<project>`

**Arguments:**

- `<project>` (required): Project name or ID to set as the default

---
