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
when working at the root of a stack.

## nerf-tg-validate

Run terragrunt validate in the current module directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-validate`
**Maps to:** `terragrunt validate --non-interactive`

No arguments.

---

## nerf-tg-validate-all

Run terragrunt validate across all units under the current directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-validate-all`
**Maps to:** `terragrunt run --all validate --non-interactive`

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
**Maps to:** `terragrunt run --all init --non-interactive -input=false <upgrade>`

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
**Maps to:** `terragrunt run --all plan --non-interactive -input=false`

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
**Maps to:** `terragrunt run --all output --non-interactive`

No arguments.

---

## nerf-tg-fmt

Run terragrunt HCL format in the current module directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-fmt [--check]`
**Maps to:** `terragrunt hcl format --non-interactive <check>`

**Switches:**

- `--check`: Check formatting without modifying files (exits non-zero if files are unformatted)

---

## nerf-tg-fmt-all

Run terragrunt HCL format across all units under the current directory.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-tg/scripts/nerf-tg-fmt-all [--check]`
**Maps to:** `terragrunt run --all hcl format --non-interactive <check>`

**Switches:**

- `--check`: Check formatting without modifying files (exits non-zero if files are unformatted)

---
