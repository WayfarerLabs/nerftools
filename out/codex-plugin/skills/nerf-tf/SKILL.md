---
name: nerf-tf
description: "Terraform workflow tools for formatting and static validation"
targets: ["*"]
---

# nerf-tf

These tools are available as scripts within this skill. Call them using the paths shown in each usage line.

These tools run Terraform commands in the current directory. They cover
canonical HCL formatting via `terraform fmt` and static configuration
checks via `terraform validate`. Planning and applying for this codebase
are done through Terragrunt (see the tg-* tools).

## nerf-tf-fmt

Run terraform fmt to canonically format Terraform files. Operates on the current directory by default; pass a target directory positionally to format elsewhere under the workspace.

**Usage:** `scripts/nerf-tf-fmt [-check] [-recursive] [-diff] [<directory>]`
**Maps to:** `terraform fmt <check> <recursive> <diff> <directory>`

**Switches:**

- `-check`: Check formatting without modifying files (exits non-zero if files are unformatted)
- `-recursive`: Process files in subdirectories
- `-diff`: Display diffs of formatting changes

**Arguments:**

- `<directory>` (optional): Subdirectory of the workspace to format (default current)

---

## nerf-tf-validate

Run terraform validate to check syntactic validity and internal consistency of the configuration in the current directory. Static checks only -- does not access remote state or provider APIs. Requires an initialized working directory (run `terraform init` or the tg-init tool first).

**Usage:** `scripts/nerf-tf-validate [-json] [-no-tests]`
**Maps to:** `terraform validate <json> <no_tests>`

**Switches:**

- `-json`: Produce output in a machine-readable JSON format
- `-no-tests`: Skip validating .tftest.hcl test files

---
