---
name: nerftools
description: "Scoped, safety-constrained CLI wrappers for AI agents"
targets: ["*"]
---

# nerftools

This environment has nerf tools installed. These are scoped, safety-constrained wrappers for common CLI operations like git, az, and other tools. They enforce guardrails (validated parameters, restricted flags, pre-flight checks) that keep operations safe and auditable.

When a nerf tool exists that covers the operation you need, prefer it over invoking the underlying tool directly. Shape your workflow to take advantage of them. For example, stage files with the nerf git-add tool and then commit with the nerf git-commit tool, rather than using raw `git` commands.

Each tool's usage line shows the full absolute path to call it. Use that path directly in Bash commands.

## Available tool packages

- **nerf-az-account**: Azure subscription and identity context tools
- **nerf-az-aks**: Azure Kubernetes Service inspection and access tools
- **nerf-az-boards**: Azure Boards work item tools for querying, viewing, creating, and updating work items
- **nerf-az-cosmosdb**: Azure Cosmos DB account inspection tools (network access, VNet rules, databases)
- **nerf-az-devops**: Azure DevOps organization-level configuration tools
- **nerf-az-keyvault**: Azure Key Vault inspection tools (network ACLs, secret metadata)
- **nerf-az-monitor**: Azure Monitor inspection tools (activity log, metrics, diagnostic settings)
- **nerf-az-network**: Azure networking inspection tools (VNets, peerings, NSGs, private endpoints, DNS zones)
- **nerf-az-pipelines**: Azure Pipelines tools for viewing pipeline status and run history
- **nerf-az-postgres**: Azure Database for PostgreSQL Flexible Server inspection tools
- **nerf-az-repos**: Azure Repos tools for viewing and creating pull requests
- **nerf-az-resource**: Generic Azure resource and resource group inspection tools
- **nerf-az-role**: Azure RBAC inspection tools (role assignments, role definitions)
- **nerf-az-storage**: Azure Storage Account inspection tools (network rules, public access, private endpoints)
- **nerf-gh**: GitHub CLI tools for pull requests, issues, and workflow runs
- **nerf-git**: Git workflow tools for safe, scoped git operations
- **nerf-kubectl**: kubectl tools for inspecting and operating on Kubernetes clusters
- **nerf-nx**: Nx workspace tools for building, testing, and inspecting projects
- **nerf-pkgrun**: Package runner tools for cspell, markdownlint, and prettier at locked versions
- **nerf-stdutils**: Safe wrappers for common Unix utilities
- **nerf-tg**: Terragrunt workflow tools for infrastructure management
- **nerf-uv**: Python development tools via uv run

Use the corresponding `nerf-*` skill for full usage details on each package.
