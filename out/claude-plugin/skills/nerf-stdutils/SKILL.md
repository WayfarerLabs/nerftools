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
find-cwd and grep-recursive-cwd are pre-scoped to the current directory.

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
