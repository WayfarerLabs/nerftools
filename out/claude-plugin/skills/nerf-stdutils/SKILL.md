---
name: nerf-stdutils
description: "Safe wrappers for common Unix utilities"
targets: ["*"]
---

# nerf-stdutils

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools wrap standard Unix utilities with safety guardrails.
Use find and find-cwd for file discovery without code execution
capabilities. Use grep and grep-recursive-cwd for text search.
Use print-range to extract a numeric line range from a file or
stream. find-cwd, grep-recursive-cwd, and print-range-cwd are
pre-scoped to the current directory.

General-purpose sed and awk are intentionally NOT wrapped --
their full surface area (in-place edits, shell-out via the `e`
command, arbitrary file writes via `w`) makes them dangerous to
permission broadly. Only the line-range filtering idiom is
covered, via print-range. If you have a sed/awk need that
print-range and grep don't cover, file a `nerf-report` so a
tightly-scoped wrapper can be added.

## nerf-find

Search for files and directories. Exec-like actions are denied -- use this for discovery only, not for running commands on results.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-stdutils/scripts/nerf-find [tokens...]`
**Maps to:** `find "$@"`

**Denied patterns:** `-exec`, `-execdir`, `-ok`, `-okdir`, `-delete`

---

## nerf-find-cwd

Search for files and directories under the current directory. Exec-like actions are denied. The search root is always '.' (current directory).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-stdutils/scripts/nerf-find-cwd [tokens...]`
**Maps to:** `find . "$@"`

**Denied patterns:** `-exec`, `-execdir`, `-ok`, `-okdir`, `-delete`

---

## nerf-grep-recursive-cwd

Search for a pattern recursively in the current directory. Prints matching lines with filenames and line numbers.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-stdutils/scripts/nerf-grep-recursive-cwd [--ignore-case|-i] [--line-regexp|-x] [--word-regexp|-w] [--count|-c] [--files-with-matches|-l] [--include <include>] [--exclude <exclude>] <pattern>`
**Maps to:** `grep -r -n <ignore_case> <line_regexp> <word_regexp> <count> <files_with_matches> <include> <exclude> -- <pattern> .`

**Switches:**

- `--ignore-case, -i`: Case-insensitive matching
- `--line-regexp, -x`: Match whole lines only
- `--word-regexp, -w`: Match whole words only
- `--count, -c`: Print only a count of matching lines per file
- `--files-with-matches, -l`: Print only filenames containing matches

**Options:**

- `--include` (optional): Search only files matching this glob (e.g. '*.py')
- `--exclude` (optional): Skip files matching this glob (e.g. '*.log')

**Arguments:**

- `<pattern>` (required): Regular expression pattern to search for

---

## nerf-grep

Search for a pattern in files or directories. Supports recursive search via -r. Files and directories are specified as trailing positional arguments after the pattern.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-stdutils/scripts/nerf-grep [--recursive|-r] [--ignore-case|-i] [--line-regexp|-x] [--word-regexp|-w] [--count|-c] [--files-with-matches|-l] [--include <include>] [--exclude <exclude>] <pattern> <paths...>`
**Maps to:** `grep -n <recursive> <ignore_case> <line_regexp> <word_regexp> <count> <files_with_matches> <include> <exclude> -- <pattern> <paths>`

**Switches:**

- `--recursive, -r`: Search directories recursively
- `--ignore-case, -i`: Case-insensitive matching
- `--line-regexp, -x`: Match whole lines only
- `--word-regexp, -w`: Match whole words only
- `--count, -c`: Print only a count of matching lines per file
- `--files-with-matches, -l`: Print only filenames containing matches

**Options:**

- `--include` (optional): Search only files matching this glob (e.g. '*.py')
- `--exclude` (optional): Skip files matching this glob (e.g. '*.log')

**Arguments:**

- `<pattern>` (required): Regular expression pattern to search for
- `<paths...>` (required): Files or directories to search

---

## nerf-print-range

Print a line range from a file or stdin. <start> and <end> are 1-indexed inclusive line numbers; both are required. With no <file>, reads from stdin (so this works at the end of a pipeline). For workspace-scoped reads, use print-range-cwd instead. For "lines matching X" rather than a line range, use grep.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-stdutils/scripts/nerf-print-range <start> <end> [<file>]`
**Maps to:** `awk NR>=<start> && NR<=<end> <file>`

**Arguments:**

- `<start>` (required): First line number (1-indexed, inclusive). must match `^[1-9][0-9]*$`
- `<end>` (required): Last line number (1-indexed, inclusive). must match `^[1-9][0-9]*$`
- `<file>` (optional): File to read (omit to read from stdin)

---

## nerf-print-range-cwd

Print a line range from a workspace file. Like print-range, but <file> is required and must resolve under the current directory (workspace-scoped read). Use this when you specifically want to read a file in the repo; use print-range for machine-scope reads or for filtering a piped stream.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-stdutils/scripts/nerf-print-range-cwd <start> <end> <file>`
**Maps to:** `awk NR>=<start> && NR<=<end> <file>`

**Arguments:**

- `<start>` (required): First line number (1-indexed, inclusive). must match `^[1-9][0-9]*$`
- `<end>` (required): Last line number (1-indexed, inclusive). must match `^[1-9][0-9]*$`
- `<file>` (required): File to read (must be under the current directory)

---

_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? Use the `nerf-report` skill._
