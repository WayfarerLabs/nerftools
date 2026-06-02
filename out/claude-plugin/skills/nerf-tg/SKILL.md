---
name: nerf-tg
description: "Terragrunt workflow tools for infrastructure management"
targets: ["*"]
---

# nerf-tg

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools run Terragrunt commands in the current directory. All tools use
--non-interactive mode. Tools with the -all suffix run across all units
under the current directory using "terragrunt run --all". Use the non-all
variant when working in a specific module directory, and the -all variant
when working at the root of a stack. Note: `tg-fmt` and `tg-hcl-validate`
already recurse through HCL files from the current directory on their own,
so they usually cover an entire stack. `tg-hcl-validate` therefore has no
-all counterpart; `tg-fmt-all` exists for symmetry but is rarely needed.

## nerf-tg-validate

Run terragrunt validate in the current module directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-validate`
**Maps to:** `terragrunt validate --non-interactive`

No arguments.

---

## nerf-tg-validate-all

Run terragrunt validate across all units under the current directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-validate-all`
**Maps to:** `terragrunt run --all -- validate --non-interactive`

No arguments.

---

## nerf-tg-init

Run terragrunt init in the current module directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-init [-upgrade]`
**Maps to:** `terragrunt init --non-interactive -input=false <upgrade>`

**Switches:**

- `-upgrade`: Upgrade modules and plugins to latest versions

---

## nerf-tg-init-all

Run terragrunt init across all units under the current directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-init-all [-upgrade]`
**Maps to:** `terragrunt run --all -- init --non-interactive -input=false <upgrade>`

**Switches:**

- `-upgrade`: Upgrade modules and plugins to latest versions

---

## nerf-tg-plan

Run terragrunt plan in the current module directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-plan`
**Maps to:** `terragrunt plan --non-interactive -input=false`

No arguments.

---

## nerf-tg-plan-all

Run terragrunt plan across all units under the current directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-plan-all`
**Maps to:** `terragrunt run --all -- plan --non-interactive -input=false`

No arguments.

---

## nerf-tg-output

Run terragrunt output in the current module directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-output`
**Maps to:** `terragrunt output --non-interactive`

No arguments.

---

## nerf-tg-output-all

Run terragrunt output across all units under the current directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-output-all`
**Maps to:** `terragrunt run --all -- output --non-interactive`

No arguments.

---

## nerf-tg-fmt

Run terragrunt hcl format to canonically format HCL files. Recurses through all HCL files (.hcl) under the current directory by default.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-fmt [--check] [--diff]`
**Maps to:** `terragrunt hcl format --non-interactive <check> <diff>`

**Switches:**

- `--check`: Check formatting without modifying files (exits non-zero if files are unformatted)
- `--diff`: Print diff between original and modified file versions. Without --check, files are still rewritten in place.

---

## nerf-tg-fmt-all

Run terragrunt hcl format across all units under the current directory via "terragrunt run --all". Note that tg-fmt already recurses through HCL files on its own; this -all variant exists for symmetry with the other tg-*-all tools and is rarely needed in practice.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-fmt-all [--check] [--diff]`
**Maps to:** `terragrunt run --all -- hcl format --non-interactive <check> <diff>`

**Switches:**

- `--check`: Check formatting without modifying files (exits non-zero if files are unformatted)
- `--diff`: Print diff between original and modified file versions. Without --check, files are still rewritten in place.

---

## nerf-tg-hcl-validate

Run terragrunt hcl validate to check the syntactic validity of Terragrunt HCL configuration files. Recurses through all HCL files under the current directory. Static checks only -- does not access remote state or provider APIs. Distinct from tg-validate, which validates the underlying Terraform configuration instead.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-hcl-validate [--json] [--inputs] [--show-config-path]`
**Maps to:** `terragrunt hcl validate --non-interactive <json> <inputs> <show_config_path>`

**Switches:**

- `--json`: Produce output in machine-readable JSON
- `--inputs`: Check that Terragrunt inputs align with Terraform-defined variables
- `--show-config-path`: After validation, print the paths of any files that failed validation

---

_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? Use the `nerf-report` skill._
