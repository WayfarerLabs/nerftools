---
name: nerf-tf
description: "Terraform workflow tools (currently scoped to formatting helpers)"
targets: ["*"]
---

# nerf-tf

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools run Terraform commands in the current directory. Today they
only cover canonical HCL formatting via `terraform fmt`. Planning and
applying for this codebase are done through Terragrunt (see the tg-*
tools).

## nerf-tf-fmt

Run terraform fmt to canonically format Terraform files. Operates on the current directory by default; pass a target directory positionally to format elsewhere under the workspace.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tf/scripts/nerf-tf-fmt [-check] [-recursive] [-diff] [<directory>]`
**Maps to:** `terraform fmt <check> <recursive> <diff> <directory>`

**Switches:**

- `-check`: Check formatting without modifying files (exits non-zero if files are unformatted)
- `-recursive`: Process files in subdirectories
- `-diff`: Display diffs of formatting changes

**Arguments:**

- `<directory>` (optional): Subdirectory of the workspace to format (default current)

---
