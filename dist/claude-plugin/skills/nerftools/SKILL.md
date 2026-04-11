---
name: nerftools
description: "Nerf tools overview and usage guidance"
targets: ["*"]
---

# Nerf Tools

This environment has nerf tools installed. These are scoped, safety-constrained wrappers for common CLI operations like git, az, and other tools. They enforce guardrails (validated parameters, restricted flags, pre-flight checks) that keep operations safe and auditable.

When a nerf tool exists that covers the operation you need, prefer it over invoking the underlying tool directly. Shape your workflow to take advantage of them. For example, stage files with the nerf git-add tool and then commit with the nerf git-commit tool, rather than using raw `git` commands.

Each tool's usage line shows the full absolute path to call it. Use that path directly in Bash commands.

## Available tool packages

- **nerf-az-boards**: Azure Boards work item tools for querying, viewing, creating, and updating work items
- **nerf-az-pipelines**: Azure Pipelines tools for viewing pipeline status and run history
- **nerf-az-repos**: Azure Repos tools for viewing and creating pull requests
- **nerf-gh**: GitHub CLI tools for pull requests, issues, and workflow runs
- **nerf-git**: Git workflow tools for safe, scoped git operations
- **nerf-nx**: Nx workspace tools for building, testing, and inspecting projects
- **nerf-pkgrun**: Package runner tools for cspell, markdownlint, and prettier at locked versions
- **nerf-stdutils**: Safe wrappers for common Unix utilities
- **nerf-tg**: Terragrunt workflow tools for infrastructure management
- **nerf-uv**: Python development tools via uv run

Use the corresponding `nerf-*` skill for full usage details on each package.
