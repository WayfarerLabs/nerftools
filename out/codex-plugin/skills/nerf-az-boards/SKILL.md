---
name: nerf-az-boards
description: "Azure Boards work item tools for querying, viewing, creating, and updating work items"
targets: ["*"]
---

# nerf-az-boards

These tools are available as scripts within this skill. Call them using the paths shown in each usage line.

These tools interact with Azure Boards work items. The organization and
project are auto-detected from the git remote in the current directory.
Pass --project to target a different project, or -C <directory> to
resolve the project from the git remote of a sub-directory (useful
when multiple repos live under one workspace root and you don't want
to cd around). The az-boards-wi-* tools operate on any work item. The
az-boards-mywi-* tools are scoped to work items assigned to you.
az-boards-area-list lists area paths in a project, useful for setting
--area on create/update.

## nerf-az-boards-wi-list

Query work items using WIQL (Work Item Query Language). Returns matching work items as JSON. The organization and project are auto-detected from the git remote; pass --project to override.

**Usage:** `scripts/nerf-az-boards-wi-list [--project|-p <project>] [-C <directory>] <wiql>`
**Maps to:** `az boards query --wiql <wiql> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<wiql>` (required): WIQL query string (e.g. "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] <> 'Closed' ORDER BY [System.ChangedDate] DESC")

---

## nerf-az-boards-wi-show

Show details and comments for any work item.

**Usage:** `scripts/nerf-az-boards-wi-show [--project|-p <project>] [-C <directory>] <wi_id>`
**Maps to:** `az boards work-item show --id <wi_id> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric). must match `^[0-9]+$`

---

## nerf-az-boards-wi-comment

Add a comment to any work item.

**Usage:** `scripts/nerf-az-boards-wi-comment [--project|-p <project>] [-C <directory>] <wi_id> <comment>`
**Maps to:** `az boards work-item update --id <wi_id> --discussion <comment> <project> --output none`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric). must match `^[0-9]+$`
- `<comment>` (required): Comment text. Stored as HTML on the work item, so HTML markup renders (e.g. "<p>See <a href='...'>this</a></p>"). Plain text is stored verbatim and renders as-is.

---

## nerf-az-boards-wi-update

Update fields on a work item. Supports state, title, assigned-to, area, iteration, and adding a discussion comment. Returns the updated work item as JSON.

**Usage:** `scripts/nerf-az-boards-wi-update [--state <state>] [--title <title>] [--assigned-to <assigned_to>] [--area <area>] [--iteration <iteration>] [--discussion <discussion>] [--fields|-f <fields>] [--project|-p <project>] [-C <directory>] <wi_id>`
**Maps to:** `az boards work-item update --id <wi_id> <state> <title> <assigned_to> <area> <iteration> <discussion> <fields> <project> --output json`

**Options:**

- `--state` (optional): New state (e.g. Active, Resolved, Closed)
- `--title` (optional): New title
- `--assigned-to` (optional): Person to assign to (e.g. user@example.com)
- `--area` (optional): Area path (e.g. MyProject\MyArea)
- `--iteration` (optional): Iteration path (e.g. MyProject\Sprint 1)
- `--discussion` (optional): Comment to add to the work item discussion. Stored as HTML, so HTML markup renders; plain text renders as-is.
- `--fields|-f` (optional): Custom field assignment (e.g. "System.Tags=Rock")
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric). must match `^[0-9]+$`

---

## nerf-az-boards-wi-create

Create a new work item. Requires a type and title. Optionally set assigned-to, area, iteration, description, and a discussion comment. Returns the created work item as JSON.

**Usage:** `scripts/nerf-az-boards-wi-create [--assigned-to <assigned_to>] [--area <area>] [--iteration <iteration>] [--description|-d <description>] [--discussion <discussion>] [--fields|-f <fields>] [--project|-p <project>] [-C <directory>] <type> <title>`
**Maps to:** `az boards work-item create --type <type> --title <title> <assigned_to> <area> <iteration> <description> <discussion> <fields> <project> --output json`

**Options:**

- `--assigned-to` (optional): Person to assign to (e.g. user@example.com)
- `--area` (optional): Area path (e.g. MyProject\MyArea)
- `--iteration` (optional): Iteration path (e.g. MyProject\Sprint 1)
- `--description|-d` (optional): Description of the work item. Stored as HTML, so HTML markup renders (e.g. "<p>Steps:</p><ol><li>...</li></ol>"). Plain text is stored verbatim and renders as-is.
- `--discussion` (optional): Comment to add to the work item discussion. Stored as HTML, so HTML markup renders; plain text renders as-is.
- `--fields|-f` (optional): Custom field assignment (e.g. "System.Tags=Rock")
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<type>` (required): Work item type (e.g. Bug, Task, User Story, Feature)
- `<title>` (required): Title of the work item

---

## nerf-az-boards-wi-add-parent

Set the parent of a work item. Takes the child ID and parent ID as positional arguments. Idempotent if the link already exists.

**Usage:** `scripts/nerf-az-boards-wi-add-parent [--project|-p <project>] [-C <directory>] <child_id> <parent_id>`
**Maps to:** `az boards work-item relation add --id <child_id> --relation-type parent --target-id <parent_id> <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<child_id>` (required): Work item ID of the child (numeric). must match `^[0-9]+$`
- `<parent_id>` (required): Work item ID of the parent (numeric). must match `^[0-9]+$`

---

## nerf-az-boards-mywi-list

List work items assigned to you that are not Closed or Removed, ordered by most recently changed. Returns matching work items as JSON.

**Usage:** `scripts/nerf-az-boards-mywi-list [--project|-p <project>] [-C <directory>]`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

---

## nerf-az-boards-mywi-show

Show details and comments for a work item assigned to you. Verifies that System.AssignedTo matches the current user; refuses items assigned to anyone else (use az-boards-wi-show for those).

**Usage:** `scripts/nerf-az-boards-mywi-show [--project|-p <project>] [-C <directory>] <wi_id>`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric, must be assigned to you). must match `^[0-9]+$`

---

## nerf-az-boards-mywi-comment

Add a comment to a work item assigned to you. Verifies that System.AssignedTo matches the current user; refuses items assigned to anyone else (use az-boards-wi-comment for those).

**Usage:** `scripts/nerf-az-boards-mywi-comment [--project|-p <project>] [-C <directory>] <wi_id> <comment>`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric, must be assigned to you). must match `^[0-9]+$`
- `<comment>` (required): Comment text. Stored as HTML on the work item, so HTML markup renders (e.g. "<p>See <a href='...'>this</a></p>"). Plain text is stored verbatim and renders as-is.

---

## nerf-az-boards-mywi-update

Update state or title on a work item assigned to you. Verifies that System.AssignedTo matches the current user; refuses items assigned to anyone else (use az-boards-wi-update for those). To reassign, use az-boards-wi-update.

**Usage:** `scripts/nerf-az-boards-mywi-update [--state <state>] [--title <title>] [--project|-p <project>] [-C <directory>] <wi_id>`

**Options:**

- `--state` (optional): New work item state (e.g. Active, Resolved, Closed)
- `--title` (optional): New work item title
- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric, must be assigned to you). must match `^[0-9]+$`

---

## nerf-az-boards-area-list

List area paths configured in a project. Returns the hierarchical area tree as JSON. Useful for setting --area on az-boards-wi-create or az-boards-wi-update.

**Usage:** `scripts/nerf-az-boards-area-list [--project|-p <project>] [-C <directory>]`
**Maps to:** `az boards area project list <project> --output json`

**Options:**

- `--project|-p` (optional): Azure DevOps project name or ID (auto-detected from the git remote if omitted)
- `-C` (optional): Resolve the Azure DevOps project from the git remote of this directory instead of cwd (must be under cwd)

---

_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? Use the `nerf-report` skill._
