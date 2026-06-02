# Nerf Manifest Reference

A nerf manifest is a YAML file that declares tools within a package. Multiple manifests can
contribute to the same package. When they share a `package.name`, tools are merged with last-wins
semantics. The manifest is the source of truth for tool definitions, parameter specs, safety
guardrails, threat metadata, and AI skill documentation.

Each tool defines exactly **one execution mode** (`template`, `passthrough`, or `script`) plus
optional lifecycle hooks and shared configuration. The `nerf` CLI reads manifests and generates
self-contained bash scripts, rulesync skills, and agent plugins (e.g. for Claude Code). Run
`nerf generate --help` for the current list of output targets.

Generated scripts target **bash** (not POSIX sh).

## Quick start

A minimal manifest with one tool:

```yaml
version: 1

package:
  name: git
  description: Git workflow tools
  skill_group: git

tools:
  git-log:
    description: Show recent commits
    threat:
      read: workspace
      write: none
    template:
      command: [git, log, --oneline, -20]
```

Validate and generate:

```bash
nerf validate manifest.yaml
nerf generate --target bin --outdir ./bin manifest.yaml
```

## Versioning

Every manifest declares its spec version as a top-level integer:

```yaml
version: 1
```

- The `version` field is required.
- The value is a single integer (major version only).
- The current version is **1**.
- The CLI validates against the declared version's schema.
- Backwards-incompatible changes require a version bump. Additive changes (new optional fields) do
  not.

## Terminology

These terms are used consistently throughout manifests, generated scripts, and generated
documentation.

### Token

A **token** is a single raw element of `$@`, one shell argument as received by the script. Before
parsing, every `$1`, `$2`, etc. is just a token.

Passthrough mode operates **exclusively at the token level**. It never classifies tokens; it scans
them against deny rules and forwards them as-is.

### Parameter types (template and script modes)

| Term         | What it is                                                             | Tokens consumed | Syntax           | Example           |
| ------------ | ---------------------------------------------------------------------- | --------------- | ---------------- | ----------------- |
| **switch**   | Boolean flag. Present or absent, no value.                             | 1               | `--flag` or `-f` | `--verbose`       |
| **option**   | Named flag + value (two tokens: **option flag** and **option value**). | 2               | `--flag <value>` | `--remote origin` |
| **argument** | Positional value identified by position, not by a flag.                | 1               | `<value>`        | `origin`          |

### Prefix and suffix tokens (passthrough mode)

**Prefix tokens** are static tokens inserted before the user's tokens. **Suffix tokens** are
inserted after. Both are hardcoded in the manifest.

```text
exec <command> <prefix...> "$@" <suffix...>
```

### Pre-flight hooks

Pre-flight hooks are inline bash snippets that run before the main execution of the tool. They can
be used to perform checks, set up environment variables, or otherwise prepare the execution context
before the main command runs.

### Guards

Guards are boolean checks that run before the main execution of the tool. Each guard is a bash
expression that must evaluate to true for the tool to proceed. If any guard fails, the tool aborts
execution. Guards are useful for enforcing preconditions, such as verifying that required files
exist or that the environment is correctly configured.

### Invocation order

Switches and options must come before arguments. The generated parser stops consuming flags at the
first non-flag token (or `--`).

```text
nerf-tool [switches] [options] [--] <arguments...>
```

### Variadic argument (templates)

A **variadic argument** collects all remaining positional values into a bash array. At most one
variadic argument is allowed per tool, and it must be the last argument, both to the nerf tool and
to the underlying wrapped CLI utility.

## Package

Top-level metadata about the tool package.

```yaml
package:
  name: <string> # Unique package identifier (e.g. "git", "nx")
  description: <string> # Human-readable description of the package
  skill_group: <string> # Skill directory name (usually matches name)
  skill_intro: <string> # Optional multi-line intro for AI skill docs
  bash_hints: # Optional list of regex patterns; see "Bash hint hook" below
    - <regex>
```

All fields except `skill_intro` and `bash_hints` are required.

### Bash hint hook

Plugin targets that support a pre-bash hook (Claude Code today; others as
their APIs land) use `bash_hints` to generate a redirect: when the agent
calls raw bash with a command that matches any pattern, the hook denies
the call (silently, without prompting the user) and points the agent at
the corresponding nerf skill. Multiple matching skills are listed
together. Targets without a pre-bash hook simply ignore the field.

Patterns are evaluated as POSIX ERE matches that may appear anywhere in
the command — prefer word-boundary anchors (`\bgit\b`) over start-anchored
ones (`^git`) so compound commands like `foo && git status` match. The
generated hook evaluates patterns via bash's `[[ =~ ]]`, which on most
platforms uses POSIX ERE. Manifest loading compiles each pattern as a
Python regex (catching uncompilable patterns and control characters) but
does not enforce ERE compatibility — Python-only constructs (lookaheads,
named groups, etc.) will pass load-time validation but won't match at
runtime. Stick to ERE. As a convenience, `\b` boundaries are translated to
portable POSIX ERE at generation time so manifests can keep using them.

The hook automatically skips when it detects an actual wrapper invocation:
it splits the command on shell separators (`&&`, `||`, `;`, `|`, `&`),
finds the first non-env-var token of each segment, and checks whether that
token's basename starts with the wrapper prefix. Compound forms like
`cd /repo && nerf-git status` and absolute-path invocations like
`/abs/path/nerf-git-add .` skip cleanly; tokens that contain the prefix at
arg position (e.g. `git log --grep nerf-X`) do not trigger the skip.

When the same `package.name` is split across multiple manifests (extension
pattern), `bash_hints` are unioned across them (order-preserved, deduped).
An extension can add new patterns without restating the base set.

An agent that genuinely needs to run the underlying command directly can
include `# <brand>:bypass <reason>` anywhere in the command (reason
required). The `<brand>` follows the wrapper prefix (default `nerf-` →
`nerf`, `mytool-` → `mytool`). The hook lets the call through; the user's
normal permission flow still applies.

The conventional `<reason>` is the filename of a `nerf-report bypass` entry
filed beforehand -- that keeps the bypass annotation grep-able from the
agent's transcript while putting the full justification, tool context, and
session metadata in a structured report under `~/.nerftools/reports/` for
the maintainer to triage. Any non-whitespace string is accepted, so this is
a convention rather than a hard requirement.

## Tool definition

```yaml
tools:
  <tool-name>:
    description: <string> # Required. What the tool does.
    threat: # Required. Risk classification.
      read: <scope> #   none|workspace|machine|remote|admin
      write: <scope> #   none|workspace|machine|remote|admin

    # Execution mode (exactly one required):
    template: { ... } # Build a command from a template
    passthrough: { ... } # Forward tokens with a deny-list
    script: <string> # Inline bash script

    # Parameters (optional, template and script only):
    switches: { ... }
    options: { ... }
    arguments: { ... }

    # Lifecycle (optional, all modes):
    pre: <string> # Inline bash run before main execution
    guards: # Pre-flight boolean checks
      - { ... }

    # Environment (optional):
    env: { ... } # Key-value pairs exported before execution
```

- Exactly one of `template`, `passthrough`, or `script` must be set.
- `switches`, `options`, and `arguments` are **not allowed** with `passthrough`.

## Threat model

Every tool declares a two-dimensional threat profile: what it **reads** and what it **writes**. This
metadata enables operators to grant permissions by risk scope rather than enumerating individual
tools.

```yaml
threat:
  read: <scope>
  write: <scope>
```

The threat profile is metadata only and does not change what the tool does. Enforcement is at the
permission layer (nerfctl grant commands, settings.json).

### Scopes (ordered, narrow to broad)

| Scope       | Meaning                                                 |
| ----------- | ------------------------------------------------------- |
| `none`      | No access in this dimension.                            |
| `workspace` | Confined to the current workspace directory tree.       |
| `machine`   | Anywhere on the local filesystem.                       |
| `remote`    | Network operations: APIs, remote repos, cloud services. |
| `admin`     | Destructive, irreversible, or elevated operations.      |

### Examples

| Tool               | Read      | Write     | Rationale                                   |
| ------------------ | --------- | --------- | ------------------------------------------- |
| `git log`          | workspace | none      | Reads repo history, writes nothing          |
| `git add`          | workspace | workspace | Reads and modifies the staging area         |
| `git fetch`        | remote    | workspace | Downloads from remote, writes to local refs |
| `git push`         | workspace | remote    | Reads local refs, writes to remote          |
| `find .`           | workspace | none      | Reads directory tree under workspace root   |
| `cspell`           | workspace | none      | Reads files, reports issues                 |
| `prettier --write` | workspace | workspace | Reads and reformats files                   |

### Scope comparison

Scopes are ordered: `none < workspace < machine < remote < admin`. A tool is within a grant ceiling
when `tool.read <= ceiling.read AND tool.write <= ceiling.write`.

### Embedded metadata

Generated scripts include the threat profile as structured comments:

```bash
#!/usr/bin/env bash
# nerf-git-push-branch -- Push the current branch to a remote
# Generated from git manifest. Do not edit directly.
# nerf:threat:read=workspace
# nerf:threat:write=remote
```

This enables runtime tool discovery and threat classification without the manifest.

## Execution modes

### template

Build a command from an explicit template with `{{kind.name}}` placeholders. Best for wrapping a
single tool call where you want full control over exposed parameters.

```yaml
template:
  command: [<string>, ...] # Command parts with {{kind.name}} placeholders
  npm_pkgrun: <bool> # Use bunx/pnpx/npx resolver (default: false)
```

Rules:

- Every `{{kind.name}}` in `command` must be defined in `switches`, `options`, or `arguments`.
- Every parameter must be referenced by a `{{kind.name}}` somewhere observable at execution time:
  `command`, `pre`, or a `guard` (script or command). The reference can live in any one of those --
  e.g. a `-C directory` whose only effect is to populate a value consumed by `pre` is a legitimate
  pre-only parameter and is accepted without appearing in `command`.
- A variadic argument's `{{kind.name}}` must be the last element of `command`.
- The generated script ends with `exec`, replacing the process.

**Literal command tokens are passed unquoted to bash.** Placeholder substitutions (`{{switches.x}}`,
`{{options.x}}`, `{{arguments.x}}`) emit shell-quoted variable references and are always safe -- a
value like `*.md` passed via `{{arguments.target}}` reaches the wrapped tool verbatim, with no glob
expansion. The unquoted-token concern applies _only_ to the static literal strings you put in
`template.command`. The codegen lays each literal token down unquoted in the generated `exec` line,
so bash sees them raw. This works for simple words, flags, and comma-separated lists (e.g.
`--json title,body,state`), which covers the vast majority of cases. It does _not_ work for literal
tokens containing shell-special characters -- braces, parens, brackets, glob characters (`*`, `?`),
tilde, redirects, pipes, dollar signs, backticks, quotes, whitespace, etc. If you need a literal
token like that (a `jq` expression, etc.), or if you need any pipe / redirection / transformation
logic, use `script` mode instead.

Example:

```yaml
git-commit:
  description: Create a git commit with a Conventional Commits message
  threat:
    read: workspace
    write: workspace
  template:
    command: [git, commit, -m, "{{arguments.message}}"]
  arguments:
    message:
      description: "Commit message: type[(scope)][!]: description"
      required: true
      pattern:
        "^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\\([a-zA-Z0-9._-]+\\))?!?:
        .+"
  guards:
    - script: "! git diff --cached --quiet"
      fail_message: No staged changes. Use git-add to stage changes first.
```

### passthrough

Forward all tokens to an underlying command, rejecting any that match a deny list. Best for exposing
a tool mostly as-is while removing dangerous capabilities.

Passthrough mode operates **exclusively at the token level**. There is no parsing, no classification
into switches/options/arguments. Every element of `$@` is scanned against deny rules and forwarded
as-is.

```yaml
passthrough:
  command: <string> # Underlying command name
  deny: [<string>, ...] # Glob patterns to reject (optional)
  prefix: [<string>, ...] # Static tokens before user tokens (optional)
  suffix: [<string>, ...] # Static tokens after user tokens (optional)
```

**Deny list matching:** each entry is a glob pattern matched against every token. Glob
metacharacters are `*`, `?`, `[`, `]`. A pattern without metacharacters is an exact match.

| Pattern    | Matches         | Does not match |
| ---------- | --------------- | -------------- |
| `--delete` | `--delete`      | `--delete-all` |
| `-ok*`     | `-ok`, `-okdir` | `--ok`         |

To match a literal metacharacter, escape with `\`. In YAML, use single quotes (`'\*'`) or double the
backslash (`"\\*"`).

Example:

```yaml
safe-find:
  description: Run find without exec capabilities
  threat:
    read: workspace
    write: none
  passthrough:
    command: find
    deny: [-exec, -execdir, -ok, -okdir, -delete]
    prefix: [.]
```

#### Known security limitations

Passthrough deny operates on whole tokens, so it cannot enforce restrictions when the wrapped tool
accepts alternative flag syntax:

- **Short-flag stacking.** Tools that use POSIX-style or `pflag` short flags (notably `kubectl`,
  many `getopt`-based utilities) allow combining boolean short flags into one token: `-Aw` is parsed
  as `-A -w`. A deny entry of `-w` matches only the exact token `-w`, not `-Aw`, `-wA`, `-Aow`, or
  any other stack containing `w`.
- **Inline value forms.** For a flag that takes a value, the deny patterns `--watch` and `-w` do not
  catch `--watch=true`, `-w=true`, or `-wtrue` (BSD-style short flag with concatenated value). The
  first two can be partially mitigated with glob denies like `--watch=*` and `-w=*`. The
  concatenated form `-wtrue` is syntactically indistinguishable from a short-flag stack and cannot
  be reliably denied at the token level.

**When this matters.** Use `template` mode when the wrapped tool is an agent-escape vector and
supports either of the above syntaxes. Templates declare the entire surface up front, so any flag
not declared in the manifest cannot reach the underlying command. Use passthrough only when the
wrapped tool's flag surface is well-understood, or when an undeclared flag slipping through is
purely an ergonomic issue rather than a safety one.

**Future direction.** A future opt-in deny extension may recognize tokens matching `^-[a-zA-Z]{2,}$`
and decompose them for deny matching, closing the short-flag-stacking gap. The concatenated-value
form is likely to remain a passthrough limitation because it cannot be distinguished from a stack
without per-tool flag knowledge. When in doubt, prefer template mode.

### script

Run an inline bash script. Best for tools that need custom logic beyond wrapping a single command.

```yaml
script: |
  <bash script body>
```

- Parameters are parsed and available as shell variables before the script runs.
- The script runs in the main shell (not a subshell). Its exit code becomes the tool's exit code.
- There is no `exec`. The script controls its own flow.

Example:

```yaml
deploy-check:
  description: Validate deployment readiness
  threat:
    read: remote
    write: remote
  script: |
    echo "Checking ${ENVIRONMENT}..."
    if [ "$DRY_RUN" = "true" ]; then
      echo "(dry run)" >&2
      exit 0
    fi
    terraform plan -detailed-exitcode
    rc=$?
    if [ $rc -eq 2 ]; then
      echo "Changes pending — review required" >&2
      exit 1
    fi
  arguments:
    environment:
      description: Target environment
      required: true
      allow: [staging, production]
  switches:
    dry_run:
      description: Skip actual checks
```

## Parameter specs

Parameters are only allowed with `template` and `script` modes. Names must not overlap across
`switches`, `options`, and `arguments` within a single tool.

All parameter values are stored as shell variables with the name uppercased and dashes replaced by
underscores (e.g. `my-param` becomes `MY_PARAM`).

### switches

A boolean flag, present or absent, with no value. Switches are always optional.

```yaml
switches:
  <name>:
    description: <string> # Required
    flag: <string> # Override flag (default: --<name> with _ replaced by -)
    short: <string> # Single-char short form (e.g. -v)
    repeatable: <bool> # Can be passed multiple times (default: false)
```

The shell variable is `"true"` when present, `""` when absent. For repeatable switches, the variable
is an integer count (0 when absent, incremented each time the switch is passed).

Rules:

- `flag` must match `-<name>` or `--<name>` pattern.
- `short` must match `-[a-zA-Z]`.

### options

A named flag that takes exactly one value.

```yaml
options:
  <name>:
    description: <string> # Required
    flag: <string> # Override flag (default: --<name> with _ replaced by -)
    short: <string> # Single-char short form
    required: <bool> # Default: false
    repeatable: <bool> # Can be passed multiple times (default: false)
    pattern: <string> # Regex the value must match (auto-anchored with ^...$)
    allow: [<string>, ...] # Exhaustive list of allowed values
    deny: [<string>, ...] # Values to reject
    path_tests: [<test>, ...] # Mark as a filesystem path; see "Path tests" below
    default: <string> # Default value seeded into the bash variable when the flag is omitted
```

Rules:

- `allow` and `deny` are mutually exclusive.
- `flag` must match `-<name>` or `--<name>` pattern.
- `short` must match `-[a-zA-Z]`.
- `pattern` is automatically anchored to a full match in the generated bash script.
- When `repeatable: true`, the option can be passed multiple times. The generated script accumulates
  flag-value pairs in an array so `"${VAR[@]}"` expands to `--flag val1 --flag val2`.
- `default` seeds the bash variable so inline placeholder substitutions like `"{{options.x}}/foo"`
  see the value even when the agent omits the flag. `default` is validated at manifest-load time: it
  must satisfy `pattern` / `allow` / `deny`, and is mutually exclusive with `required: true`,
  `repeatable: true`, and `path_tests` (path tests only evaluate against runtime cwd, so they cannot
  validate a load-time default). `default` must be a string; YAML `null`, `true`, `0`, etc. are
  rejected.

### arguments

A positional argument identified by position.

```yaml
arguments:
  <name>:
    description: <string> # Required
    required: <bool> # Default: false
    variadic: <bool> # Collect remaining args into array (default: false)
    allow_flags: <bool> # Allow flag-like tokens in variadic args (default: false)
    pattern: <string> # Regex the value must match (auto-anchored)
    allow: [<string>, ...] # Exhaustive list of allowed values
    deny: [<string>, ...] # Values to reject
    path_tests: [<test>, ...] # Mark as a filesystem path; see "Path tests" below
```

Rules:

- `allow` and `deny` are mutually exclusive.
- At most one argument may be `variadic`, and it must be the last in `arguments`.
- In `template` mode, a variadic `{{kind.name}}` must be the last element in `template.command`.
- Variadic arguments become bash arrays; all others become scalar variables.
- By default, variadic arguments reject tokens starting with `-` to prevent flag injection. Set
  `allow_flags: true` when forwarding to a tool that expects its own flags (e.g. pytest, ruff).
  **Read "Variadic flag injection" below before enabling this** -- `allow_flags: true` is
  functionally passthrough mode for the bytes in the variadic, and the only honest defense is a
  structural property of the wrapped command that makes dangerous flags unreachable.
- Inside a variadic with `allow_flags: true`, `deny:` does double duty: in addition to its usual
  arg-value role (rejecting one of an exhaustive set of values for a named argument) it becomes a
  per-token **flag firewall** -- strictly weaker than `passthrough` mode's glob-based deny, since
  the match is exact-token only. Use it for an enumerable set of exact flag tokens; reach for a
  `pre:` loop with `case`-pattern matching when a flag has both bare and `--flag=value` shapes
  (see "Variadic flag injection" for guidance).
- Arguments do not have a `default` field. Required positional arguments always receive a value;
  optional positionals are exposed to the wrapped tool only when the agent supplies one.

### Variadic flag injection

`allow_flags: true` on a variadic argument is functionally passthrough mode for the bytes that land
in the variadic. The nerf parser stops consuming nerf-declared flags at the first unrecognized token
and forwards everything from that point -- including arbitrary `-`-prefixed tokens -- raw to the
wrapped tool, which fully parses them as flags. The variadic's own `deny` / `allow` / `pattern`
validations _do_ run per element, but they are exact-token matches: they do not handle stacked
short flags (`-Aw`), inline value forms (`--flag=value`), or any other syntactic variant the wrapped
tool may accept. Use them to forbid a small enumerable set of dangerous flags (e.g. the
gitconfig-driver re-enablers `--ext-diff` / `--textconv`), not as a general flag firewall. For
broader coverage the only honest defense is a structural property of the wrapped command that
makes dangerous flags unreachable from the variadic's position.

The canonical example is the **subcommand parse boundary in multi-level CLIs** (git, kubectl,
docker, az, etc.). Dangerous flags often live at the top-level parser, not the subcommand's. A
variadic placed after the subcommand cannot smuggle a top-level flag because the subcommand's parser
does not recognize it. For example, `git`'s top-level flags (`-C`, `--git-dir`, `--work-tree`, `-c`)
must precede the subcommand. A variadic placed after `git log` cannot reach them: `-C` after `log`
is reinterpreted as `--find-copies`, and the rest error as unknown options. This makes
`allow_flags: true` _on a subcommand-level variadic_ safe for that specific subcommand, but only
after verifying the subcommand itself has no dangerous flags of its own. Document the analysis in
the tool's `description`; do not transfer it to a different wrapped command without redoing it.

Other structural protections exist (e.g. a tool that has no write-capable flags at all, or a tool
whose dangerous flags are gated by an outer wrapper). Treat each one as a per-tool argument.

#### Choosing between `deny:` and a `pre:` loop

Both can reject dangerous tokens from a variadic, but they cover different shapes:

- **`deny:` on the variadic argument** is an exact-token match against each forwarded element.
  Use it for an enumerable set of dangerous flags whose value-attached form (`--flag=value`) is
  either nonexistent or equally unsafe -- e.g. `--ext-diff` and `--textconv` on `git diff`, which
  are toggles with no `=value` shape and unsafely re-enable disabled drivers. Cheap, declarative,
  and produces the standard "denied:" error.
- **A `pre:` loop with a `case` pattern** is the right tool when a dangerous flag has both bare
  (`--flag <val>`) and inline (`--flag=val`) shapes, or any other syntactic variant exact-match
  misses (short-flag stacking like `-Aw`, BSD-style `-oval`, etc.). The canonical example is
  `--output[=]<path>` on `git diff` / `git log` (see `nerftools/default_manifests/git.yaml`),
  which writes a patch to an arbitrary file path and so would violate `write: none`. The `pre:`
  loop catches both forms with `--output|--output=*`.

The two compose naturally: `deny:` for the easy cases, `pre:` for everything exact-match misses.

When you do **not** need to forward arbitrary flags, prefer the **sentinel pattern**: declare the
flags you want to expose as nerf `switches` / `options`, place `--` after the static prefix in
`template.command`, and leave the variadic with `allow_flags: false` (the default) for positional
content only. The parser rejects `-`-prefixed tokens at the variadic, and the `--` sentinel forces
the wrapped tool to interpret anything that slips through as a positional -- usually a loud failure
rather than a silent dangerous-flag invocation. This is defense-in-depth on top of the default; it
is not a justification for `allow_flags: true` (the two intents are opposite -- the sentinel tells
the wrapped tool to ignore flags, which negates the point of forwarding them).

If you need flag forwarding and there is no structural protection, either exhaustively declare all
safe args or fall back to `passthrough` mode where token-level `deny` is available. Just make sure
you understand the fundamental difference in templates parsing args vs passthrough just analyzing
opaque tokens. It's not a simple conversion.

## Path tests

Mark an option or argument as a filesystem path by setting `path_tests` to a non-empty list of test
names. The generated script applies a baseline check (control characters rejected, canonicalization
succeeds) plus the listed tests in a deterministic order.

```yaml
options:
  directory:
    description: Directory to run in
    flag: -C
    path_tests: [under_cwd, dir]
arguments:
  target:
    description: File to format
    required: true
    path_tests: [under_cwd, file]
```

### Test catalog

| Test          | Meaning                                                         | Bash primitive |
| ------------- | --------------------------------------------------------------- | -------------- |
| `under_cwd`   | Canonicalized path is `$PWD` itself or under it (symlink-aware) | `realpath -m`  |
| `exists`      | Path exists                                                     | `[[ -e ]]`     |
| `not_exists`  | Path does not exist (e.g. for new-file targets)                 | `[[ ! -e ]]`   |
| `file`        | Exists and is a regular file (implies `exists`)                 | `[[ -f ]]`     |
| `dir`         | Exists and is a directory (implies `exists`)                    | `[[ -d ]]`     |
| `readable`    | Readable by the current user (implies `exists`)                 | `[[ -r ]]`     |
| `writable`    | Writable by the current user (implies `exists`)                 | `[[ -w ]]`     |
| `executable`  | Executable by the current user (implies `exists`)               | `[[ -x ]]`     |
| `symlink`     | Path is a symlink                                               | `[[ -L ]]`     |
| `not_symlink` | Path is not a symlink                                           | `! [[ -L ]]`   |

**Symlinks behave differently across tests.** `under_cwd` follows symlinks via `realpath -m`, so a
symlink whose target is outside the workspace fails the boundary check even if the link itself is
inside. The `exists`/`file`/`dir`/`readable`/`writable`/`executable` tests also follow symlinks
(they check the target, not the link). Only `symlink` and `not_symlink` test the path itself without
following the link. Combine them deliberately if you mean both, e.g. `[under_cwd, file]` requires
the resolved target to be a regular file inside the workspace, while
`[under_cwd, not_symlink, file]` additionally rejects symlinks even when their targets would
qualify.

### Evaluation order

For each path-typed parameter, the helper runs:

1. **Baseline** -- reject `\n` / `\r` / `\t` in the input, canonicalize `$PWD` and the input.
2. **Boundary** -- `under_cwd`.
3. **Existence** -- `exists`, `not_exists`.
4. **Type** -- `file`, `dir`, `symlink`, `not_symlink`.
5. **Access** -- `readable`, `writable`, `executable`.

The helper short-circuits on the first failure and reports the failed test name.

### Rules

- `path_tests` only applies to `options` and `arguments`, not `switches`.
- An empty list is rejected at validation time. Omit the field entirely if you do not want path
  validation.
- Mutually exclusive: `exists` and `not_exists`; `file` and `dir`; `symlink` and `not_symlink`.
- `not_exists` cannot be combined with `file`, `dir`, `readable`, `writable`, `executable`, or
  `symlink` -- those tests require the path to exist.
- Unknown test names are rejected at validation time.
- For variadic arguments the helper runs once per element.
- Optional parameters are skipped when unset; required parameters are checked after the
  required-value check.

### Threat-scope implication

A parameter with `path_tests: [under_cwd, ...]` is constrained to the workspace, so the tool can
credibly claim `read: workspace` or `write: workspace` rather than `read: machine` or
`write: machine` for that filesystem-touching surface.

### Don't duplicate the wrapped tool's own checks

`path_tests` exists to enforce _boundaries_ (workspace containment, control characters, basic
canonicalization). It is not a place to recreate validation that the wrapped tool already does. For
most cases, `[under_cwd]` alone is the right answer: it locks the path to the workspace and
delegates type, existence, and content checks to the tool you're calling.

For example, `git -C <dir>` already produces a clear
`fatal: cannot change to '...': Not a directory` if the path is wrong. Adding `dir` to `path_tests`
would only duplicate that check and produce a less informative error than git's. Reach for the
longer test lists only when the wrapped tool's behavior on the failure mode is genuinely worse than
failing at the boundary (e.g. silently no-oping, hanging, or modifying state).

### Caveats

- Symlink resolution uses `realpath -m`, which follows symlinks. A symlink inside `$PWD` whose
  target is outside `$PWD` fails `under_cwd`. This is intentional.
- The check is not a security boundary against an adversarial filesystem actor (TOCTOU between
  validation and use is possible).
- `realpath` is required and is part of GNU coreutils on Linux and modern macOS coreutils. Pure BSD
  environments are not supported.

## Lifecycle

### Execution order

```text
guards → pre → main (template exec | passthrough exec | script run)
```

### guards

Pre-flight boolean checks that run before the main execution.

```yaml
guards:
  - fail_message: <string> # Required. Shown on failure.
    command: [<string>, ...] # Run as subprocess, output suppressed
    # OR
    script: <string> # Inline bash snippet
```

Exactly one of `command` or `script`. The check passes on exit code 0. `{{kind.name}}` placeholders
are substituted with parameter values.

### pre

An inline bash script that runs before the main execution mode. Use it for setup, variable
computation, and conditional abort.

```yaml
pre: |
  <bash script body>
```

The pre script is wrapped in a shell function (`_nerf_pre`). Key points:

- **Use `return` to abort, not `exit`.** `return 1` lets the wrapper report the failure. `exit`
  kills the entire script immediately, bypassing error reporting.
- **Print your own error messages.** The fallback message is generic. Write `echo "error: ..." >&2`
  before `return 1`.
- **Shell variables set in pre are visible to main.** Functions execute in the caller's scope. Do
  **not** use `local` -- a `local` declaration limits scope to the function body and the variable
  will be empty when main runs.
- **`{{kind.name}}` placeholders work.** Parameters are parsed before pre runs.
- **`set -e` does NOT abort pre on bare command failure.** Bash suppresses errexit inside any
  function whose return code is being tested by the caller, and the wrapper invokes pre via
  `_nerf_pre || _nerf_pre_rc=$?`. Even adding `set -e` inside the function body has no effect per
  POSIX/bash semantics. **Always check command results explicitly with `if`/`||` and `return 1`.**
- **Populating an option's value from pre.** Optional-scalar options emit conditionally based on a
  parser-set sentinel `_<NAME>_SET`, not on the value variable itself. To make the template emit
  `--flag $VAR` when pre computes a value that the CLI parser never saw, assign **both** the value
  and the sentinel, and **gate on the sentinel, not the value**, so an explicit `--flag ""` from the
  agent is respected as-set rather than silently overwritten:

  ```bash
  if [[ -z "${_PROJECT_SET}" ]]; then
    PROJECT="detected-value"
    _PROJECT_SET=true
  fi
  ```

  This is the documented contract for pre-only / `-C`-style options whose effect is to derive a
  value the wrapped tool needs as an explicit flag (used pervasively by the `az-*` tools to
  resolve project from `-C`). The variable name pattern is always `_<UPPERCASE_OPTION>_SET`.
  The same principle applies whenever you read or forward an option's value from `pre` or a
  script-mode body: gate on the `_<NAME>_SET` sentinel, **never** on the value string.
  - For pre-only inputs: `if [[ -n "${_DIRECTORY_SET}" ]]; then ...` distinguishes `-C ""` from
    `-C` being omitted.
  - For conditional argv forwarding from `script:` mode: write
    `[[ -n "${_PROJECT_SET}" ]] && ARGS+=(--project "${PROJECT}")`, not
    `[[ -n "${PROJECT}" ]] && ...`, so the agent's explicit empty value is preserved through to
    the wrapped tool rather than silently dropped.

Example:

```yaml
git-push-branch:
  description: Push the current branch to a remote
  threat:
    read: workspace
    write: remote
  template:
    command: [git, push, --follow-tags, "{{arguments.remote}}", HEAD]
  arguments:
    remote:
      description: Remote name
      required: true
      pattern: "^[a-z0-9_-]+$"
  pre: |
    BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)
    if [ -z "$BRANCH" ]; then
      echo "error: cannot push from detached HEAD state" >&2
      return 1
    fi
    if [ "$BRANCH" = "main" ]; then
      echo "error: use git-push-main for the main branch" >&2
      return 1
    fi
```

## Environment

```yaml
env:
  VAR_NAME: "value"
```

Key-value pairs exported as environment variables before guards, pre, and main execution. Values are
static strings (no `{{kind.name}}` substitution). Keys must match `[A-Z_][A-Z0-9_]*`.

## Placeholder substitution

Placeholders use the form `{{kind.name}}` where `kind` is one of `switches`, `options`, or
`arguments`. They appear in `template.command`, `guard.command`, `guard.script`, and `pre` and are
replaced with shell variable references.

| Context          | Required scalar | Optional scalar             | Required variadic | Optional variadic       | Switch             | Repeatable option                |
| ---------------- | --------------- | --------------------------- | ----------------- | ----------------------- | ------------------ | -------------------------------- |
| template command | `"$VAR"`        | `--flag $VAR` (conditional) | `"${VAR[@]}"`     | `${VAR[@]+"${VAR[@]}"}` | `${VAR:+"--flag"}` | `"${VAR[@]}"` (flag-value pairs) |
| guard/pre script | `${VAR}`        | `${VAR}`                    | `${VAR}`          | `${VAR}`                | `${VAR}`           | `${VAR}`                         |

In script contexts (guards, pre, inline script body), the author is responsible for quoting.

## Error messages

Generated scripts produce structured errors for both humans and AI agents:

```text
error: <tool-name>: <what went wrong>
  <detail lines>
  hint: <what to do instead>
```

The first line always starts with `error: <tool-name>:` so the caller can identify which tool
failed. Examples:

```text
error: nerf-git-commit: missing required argument <message>
  hint: provide a value for <message>

error: nerf-git-commit: argument <message> does not match required pattern
  value:   "updated readme"
  pattern: ^(feat|fix|docs|...)...
  hint: value must match ^(feat|fix|docs|...)...

error: nerf-safe-find: token '-exec' is not allowed (matched deny pattern '-exec')
  denied patterns: -exec, -execdir, -ok*, --delete
  hint: remove '-exec' and retry
```

## Dry-run mode

Every generated tool supports `--nerf-dry-run`. When passed in the flag region (before any
positional argument), the tool runs all validation, guards, pre-hooks, and deny scans as normal, but
instead of executing the final command it prints what would be run and exits.

```bash
$ nerf-git-fetch --nerf-dry-run origin
dry-run: git fetch origin --tags

$ nerf-find-cwd --nerf-dry-run -name '*.py'
dry-run: find '.' -name *.py

$ nerf-deploy-check --nerf-dry-run staging
dry-run: nerf-deploy-check would run inline script
```

If a guard or deny rule would reject the invocation, the error is reported as usual:

```bash
$ nerf-find-cwd --nerf-dry-run -exec echo {} \;
error: nerf-find-cwd: token '-exec' is not allowed (matched deny pattern '-exec')
```

`--nerf-dry-run` may appear anywhere in the flag region (before the first positional argument); like
other declared flags it is recognized in any order. The parser stops consuming flags at the first
non-flag token, so `--nerf-dry-run` placed after a positional argument is captured into that
argument (or rejected as an extra) and does not enable dry-run. For tools with variadic+allow_flags
arguments, the codegen rejects `--nerf-dry-run` tokens inside the variadic explicitly to prevent
silent dry-run bypass.

## Generated documentation

### Maps-to line

Every template and passthrough tool shows a **Maps to** line revealing the underlying command:

- **Template:** `Maps to: git commit -m <message>`
- **Passthrough:** `Maps to: find . "$@"`
- **Script:** no Maps-to line.

### Help text (--help)

Generated scripts include a `usage()` function with separate Switches, Options, and Arguments
sections, constraints shown inline, and the Maps-to line.

### AI skill files (SKILL.md)

Generated skill files follow the same structure formatted as markdown for AI assistants.

## Validation summary

| Rule                                                                     | Scope                 |
| ------------------------------------------------------------------------ | --------------------- |
| `version` is required and must be an integer                             | manifest              |
| `threat.read` and `threat.write` required                                | tool                  |
| Exactly one of `template`, `passthrough`, `script`                       | tool                  |
| `switches`/`options`/`arguments` not allowed with `passthrough`          | tool                  |
| `{{kind.name}}` refs must exist in switches/options/arguments            | template, guards, pre |
| All switches/options/arguments must be referenced in `{{kind.name}}`     | template, pre, guards |
| Variadic argument must be last in `arguments`                            | arguments             |
| Variadic `{{kind.name}}` must be last element in `template.command`      | template              |
| `allow` and `deny` are mutually exclusive                                | options, arguments    |
| Switch/option/argument names must not overlap                            | tool                  |
| `flag` matches `-<name>` or `--<name>` pattern                           | switches, options     |
| `short` matches `-[a-zA-Z]`                                              | switches, options     |
| `pattern` is a valid regex                                               | options, arguments    |
| `env` keys match `[A-Z_][A-Z0-9_]*`                                      | env                   |
| Guard has exactly one of `command` or `script`                           | guards                |
| `path_tests` is non-empty if present                                     | options, arguments    |
| `path_tests` entries are known names                                     | options, arguments    |
| `path_tests` mutual exclusions enforced                                  | options, arguments    |
| `default` must be a string                                               | options               |
| `default` mutually exclusive with `required`, `repeatable`, `path_tests` | options               |
| `default` must satisfy `pattern` / `allow` / `deny` if present           | options               |
