---
name: nerf-nx
description: "Nx workspace tools for building, testing, and inspecting projects"
targets: ["*"]
---

# nerf-nx

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools run Nx commands via npx. All tools require an nx.json file in
the current directory (Nx workspace root). Use nx-show-projects to
list all projects, nx-run to execute a target, and nx-affected to
find projects affected by current changes.

## nerf-nx-show-projects

List all projects in the Nx workspace (one per line).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-nx/scripts/nerf-nx-show-projects`
**Maps to:** `npx nx show projects`

No arguments.

---

## nerf-nx-show-project

Show configuration details for a specific Nx project (targets, source root, metadata).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-nx/scripts/nerf-nx-show-project <project>`
**Maps to:** `npx nx show project <project>`

**Arguments:**

- `<project>` (required): Nx project name (from nx-show-projects). must match `^[a-zA-Z0-9_-]+$`

---

## nerf-nx-run

Run an Nx target on a project in project:target format (e.g. myapp:build).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-nx/scripts/nerf-nx-run <target>`
**Maps to:** `npx nx run <target>`

**Arguments:**

- `<target>` (required): Target in project:target format (e.g. myapp:build, myapp:test, myapp:lint). must match `^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$`

---

## nerf-nx-affected

List Nx projects affected by current changes compared to main.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-nx/scripts/nerf-nx-affected`
**Maps to:** `npx nx show projects --affected`

No arguments.

---

## nerf-nx-graph

Print the Nx project dependency graph as JSON.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-nx/scripts/nerf-nx-graph`
**Maps to:** `npx nx graph --print-affected`

No arguments.

---

## nerf-nx-reset

Clear the Nx cache and reset the Nx daemon.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-nx/scripts/nerf-nx-reset`
**Maps to:** `npx nx reset`

No arguments.

---
