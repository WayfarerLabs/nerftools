---
name: nerf-az-boards
description: "Azure Boards work item tools for querying, viewing, creating, and updating work items"
targets: ["*"]
---

# nerf-az-boards

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools interact with Azure Boards work items. The organization and
project are auto-detected from the git remote. The az-boards-wi-*
tools operate on any work item. The az-boards-mywi-* tools are
scoped to work items assigned to you.

## nerf-az-boards-wi-list

Query work items using WIQL (Work Item Query Language). Returns matching work items as JSON. The organization and project are auto-detected from the git remote..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-wi-list <wiql>`
**Maps to:** `az boards query --wiql <wiql> --output json`

**Arguments:**

- `<wiql>` (required): WIQL query string (e.g. "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] <> 'Closed' ORDER BY [System.ChangedDate] DESC")

---

## nerf-az-boards-wi-show

Show details and comments for any work item.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-wi-show <wi_id>`
**Maps to:** `az boards work-item show --id <wi_id> --output json`

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric). must match `^[0-9]+$`

---

## nerf-az-boards-wi-comment

Add a comment to any work item.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-wi-comment <wi_id> <comment>`
**Maps to:** `az boards work-item update --id <wi_id> --discussion <comment> --output none`

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric). must match `^[0-9]+$`
- `<comment>` (required): Comment text to add to the work item

---

## nerf-az-boards-wi-update

Update fields on a work item. Supports state, title, assigned-to, area, iteration, and adding a discussion comment. Returns the updated work item as JSON..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-wi-update [--state <state>] [--title <title>] [--assigned-to <assigned_to>] [--area <area>] [--iteration <iteration>] [--discussion <discussion>] [--fields|-f <fields>] <wi_id>`
**Maps to:** `az boards work-item update --id <wi_id> <state> <title> <assigned_to> <area> <iteration> <discussion> <fields> --output json`

**Options:**

- `--state` (optional): New state (e.g. Active, Resolved, Closed)
- `--title` (optional): New title
- `--assigned-to` (optional): Person to assign to (e.g. user@example.com)
- `--area` (optional): Area path (e.g. MyProject\MyArea)
- `--iteration` (optional): Iteration path (e.g. MyProject\Sprint 1)
- `--discussion` (optional): Comment to add to the work item discussion
- `--fields|-f` (optional): Custom field assignment (e.g. "System.Tags=Rock")

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric). must match `^[0-9]+$`

---

## nerf-az-boards-wi-create

Create a new work item. Requires a type and title. Optionally set assigned-to, area, iteration, description, and a discussion comment. Returns the created work item as JSON..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-wi-create [--assigned-to <assigned_to>] [--area <area>] [--iteration <iteration>] [--description|-d <description>] [--discussion <discussion>] [--fields|-f <fields>] <type> <title>`
**Maps to:** `az boards work-item create --type <type> --title <title> <assigned_to> <area> <iteration> <description> <discussion> <fields> --output json`

**Options:**

- `--assigned-to` (optional): Person to assign to (e.g. user@example.com)
- `--area` (optional): Area path (e.g. MyProject\MyArea)
- `--iteration` (optional): Iteration path (e.g. MyProject\Sprint 1)
- `--description|-d` (optional): Description of the work item
- `--discussion` (optional): Comment to add to the work item discussion
- `--fields|-f` (optional): Custom field assignment (e.g. "System.Tags=Rock")

**Arguments:**

- `<type>` (required): Work item type (e.g. Bug, Task, User Story, Feature)
- `<title>` (required): Title of the work item

---

## nerf-az-boards-wi-add-parent

Set the parent of a work item. Takes the child ID and parent ID as positional arguments. Idempotent if the link already exists..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-wi-add-parent <child_id> <parent_id>`
**Maps to:** `az boards work-item relation add --id <child_id> --relation-type parent --target-id <parent_id> --output json`

**Arguments:**

- `<child_id>` (required): Work item ID of the child (numeric). must match `^[0-9]+$`
- `<parent_id>` (required): Work item ID of the parent (numeric). must match `^[0-9]+$`

---

## nerf-az-boards-mywi-show

Show details and comments for a work item assigned to you.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-mywi-show <wi_id>`
**Maps to:** `az boards work-item show --id <wi_id> --output json`

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric, must be assigned to you). must match `^[0-9]+$`

---

## nerf-az-boards-mywi-comment

Add a comment to a work item assigned to you.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-az-boards/scripts/nerf-az-boards-mywi-comment <wi_id> <comment>`
**Maps to:** `az boards work-item update --id <wi_id> --discussion <comment> --output none`

**Arguments:**

- `<wi_id>` (required): Work item ID (numeric, must be assigned to you). must match `^[0-9]+$`
- `<comment>` (required): Comment text to add to the work item

---
