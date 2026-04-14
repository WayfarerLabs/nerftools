# Nerf Tools

Define and generate nerf tools: limited-scope wrappers for common CLI utilities that allow for
fine-grained control over agent execution.

Nerf tools wrap CLI commands so that the resulting tool has a limited, predictable scope. This then
allows for broad permissioning in agentic tooling, knowing that the tools can't be used to perform
operations outside of the declared scope.

This mechanism was designed specifically for Claude Code, where the permission system (as of
2026-04) is not really capable of fine-grained control over broad tools like `git`, `aws`, etc. That
said, it should work in any environment where a permission layer can allow calling a tool like
`nerf-git-add` but block calling `git` directly.

## Core Concepts

### Packages and Tools

A **tool** is a single executable script that wraps one or more underlying CLI utilities in a
limited-scope interface. Tools can support parameters (options as well as positional arguments) as
needed to satisfy their purpose.

To help keep things tidy, tools are grouped into **packages**. This organization is completely
arbitrary but is generally done around a specific underlying CLI utility (all or part). For example,
all nerf tools that wrap `git` might be grouped into a `git` package, while tools that wrap `aws`
commands might be grouped into several `aws-<subservice>` packages, such as `aws-s3`, `aws-ec2`,
etc.

### Manifests

**Manifests** are the way that nerf tools are defined. The mechanism is designed to make it very
easy and fast to define new tools. The nerf tool system supports several different types of tool
that have different semantics, capabilities, and relationships to the underlying CLI utilities they
wrap. A `generate` process then takes the manifests and generates the corresponding executable nerf
tools.

An individual manifest can contain any number of tool definitions for a single package. Any number
of manifest files can be used to generate tools and multiple manifests can contribute to the same
package, with tools merged using last-wins semantics.

For more detail on the manifest format and tool types/capabilities, see the
[manifest reference](docs/nerf-manifest.md).

This repo includes a set of [default manifests](nerftools/default_manifests/) that define a baseline
set of nerf tools for common CLI utilities. Users are free to build upon these with their own custom
manifests or exclude them entirely by passing the `--no-default` flag to the CLI when generating
tools.

### Targets

A **target** is the output format that the nerf CLI should generate from the manifests. Different
targets produce different artifacts from the same set of manifests. For example, the `bin` target
generates executable scripts in a single directory that can then be placed on the PATH for easy
access. Other targets (such as `claude-plugin`) are designed and packaged for use with specific
tooling.

Many targets include a notion of "skills", which are conventional agent skills, designed to convey
how to use the generated tools. Skills are generally created one per package, listing all the tools
within that package along with the package-level information.

## How to Use Nerf Tools

This repo offers several ways to use the nerf tools. Choose the best one for your specific needs:

- The repo exposes a fully-generated Claude Code plugin with the default tools that can be installed
  into a Claude Code environment directly from this repository. This is super easy but does not
  allow for customization of the tools or other changes to the plugin.
- Alternatively, users can install the Python package and generate their own targets locally using
  the CLI.
- Additionally, platforms like [Agentworks](https://github.com/WayfarerLabs/agentworks) integrate
  with nerf tools to allow for automated generation and consumption of targets from manifests as
  part of broader agentic tooling platforms.

## Security Model

Nerf tools are specifically designed to work in environments where the agent technically has access
to the underlying CLI utilities (e.g., `git`, `aws`, etc. are installed, configured, and available)
but where a permission layer can restrict direct access to those tools. This is generally true for
agentic co-development frameworks such as Claude Code, OpenCode, etc.

It's important to note that the security here is only as good as the permission layer. If that can
be circumvented such that the agent can invoke the underlying CLI utilities directly, then the nerf
tools no longer provide any meaningful restriction on what the agent can do.

**IMPORTANT: Nerf tools should not be considered universally safe.** Different tools have different
threat profiles. Rather, the goal is that each nerf tool should limit usage of the underlying CLI
tool to a set of operations with a roughly-equivalent threat profile (as expressed in its declared
threat model) so that permissions can be broadly granted (e.g. in tools like Claude Code) with
confidence that the agent can't perform operations outside the declared threat profile.

## Quick start

```bash
# Validate manifests
uv run nerf validate

# Generate executable scripts (drop on PATH)
uv run nerf generate --target bin --outdir ./bin

# Generate rulesync skills
uv run nerf generate --target skills --outdir ./skills

# Generate a Claude Code plugin (requires a plugin metadata config)
uv run nerf generate --target claude-plugin \
  --plugin-config nerf-plugin.yaml \
  --outdir ./claude-plugin
```

Plugin metadata is sourced from an external file to make it easy for teams to personalize the output
plugin for their needs. See [nerf-plugin.yaml](nerf-plugin.yaml) for the plugin metadata format.

## Default Manifests/Packages

| Package      | Tools | Description                                                      |
| ------------ | ----- | ---------------------------------------------------------------- |
| git          | 11    | Git workflow with commit, push, fetch, tag, amend, revert, reset |
| az-repos     | 3     | Azure Repos PR management                                        |
| az-pipelines | 3     | Azure Pipelines monitoring                                       |
| az-boards    | 7     | Azure Boards work items (query, view, create, update)            |
| nx           | 6     | Nx monorepo workspace operations                                 |
| tg           | 10    | Terragrunt infrastructure management                             |
| pkgrun       | 3     | npm package runners (cspell, markdownlint, prettier)             |
| stdutils     | 4     | Unix utilities (find, grep) with safety guardrails               |
| gh           | 10    | GitHub CLI (PRs, issues, workflow runs)                          |
| uv           | 4     | Python dev tools via uv run (pytest, ruff, mypy)                 |

## Nerf Control Tools

This package includes tools for managing nerf permissions and grants, allowing operators to control
which tools an agent can invoke based on the declared threat profile of each tool. These are
specific to the target tooling (e.g. Claude Code).

These allow two major ways of managing nerf tool permissions as listed below. Note that these can
generally be used together with last-wins semantics, where later grants or denials override earlier
ones in the execution order.

### Grant by Tool Name/Pattern

Nerf tools can be granted/denied individually by specifying the tool name or a pattern that matches
multiple tools. This allows operators to explicitly allow or block access to specific CLI utilities
regardless of their declared threat profile.

### Grant by Threat Model

Every nerf tool declares a 2D threat profile (`read` and `write` scopes) as part of its manifest --
see the [manifest reference](docs/nerf-manifest.md#threat-model) for how these are defined. Grants
can then be expressed as threat ceilings rather than enumerations of individual tools, letting
operators permission broadly while still bounding what an agent can do:

```bash
# Allow all tools that read/write within the workspace
nerfctl-grant-by-threat --read workspace --write workspace

# Also allow remote-read tools (e.g. git fetch, az boards)
nerfctl-grant-by-threat --read remote --write workspace
```

Any tool whose declared profile falls within the ceiling is allowed; tools with broader profiles
are denied (or reset, depending on flags).

## Development

```bash
# Install dependencies and run tests
uv run pytest tests/ -v

# Lint
uv run ruff check nerftools/ tests/
uv run mypy nerftools/

# Validate all default manifests
uv run nerf validate
```

Requires Python 3.12+ (pinned via `.python-version`).

## Project structure

```text
nerftools/             Python package
  manifest.py          Data model, loading, validation
  builder.py           Bash script generation (3 execution modes)
  rendering.py         Shared display helpers (maps-to, usage tokens)
  skill.py             Rulesync skill generation
  formats.py           Claude Code plugin builder
  cli.py               CLI (validate + generate)
  nerfctl/claude/      Grant management shell scripts
  default_manifests/   Default tool package manifests (YAML)
tests/                 Test suite
out/claude-plugin/     Pre-built Claude Code plugin (auto-generated)
docs/                  Manifest spec and other (future) docs
```
