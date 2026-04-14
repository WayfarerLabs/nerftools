---
name: nerf-uv
description: "Python development tools via uv run"
targets: ["*"]
---

# nerf-uv

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools run Python development tools via uv run, using the project's
virtual environment. Use uv-pytest for testing, uv-ruff-check and
uv-ruff-fix for linting, and uv-mypy for type checking. All tools
forward arguments directly to the underlying command.

## nerf-uv-pytest

Run pytest with the given arguments.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-uv/scripts/nerf-uv-pytest [<args...>]`
**Maps to:** `uv run pytest <args>`

**Arguments:**

- `<args...>` (optional): Arguments to pass to pytest (e.g. tests/ -v or -x -q)

---

## nerf-uv-ruff-check

Run ruff check (lint without modifying files).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-uv/scripts/nerf-uv-ruff-check [<args...>]`
**Maps to:** `uv run ruff check <args>`

**Arguments:**

- `<args...>` (optional): Arguments to pass to ruff check (e.g. src/)

---

## nerf-uv-ruff-fix

Run ruff check with --fix to auto-fix lint issues.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-uv/scripts/nerf-uv-ruff-fix [<args...>]`
**Maps to:** `uv run ruff check --fix <args>`

**Arguments:**

- `<args...>` (optional): Arguments to pass to ruff check --fix (e.g. src/)

---

## nerf-uv-mypy

Run mypy type checker with the given arguments.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-uv/scripts/nerf-uv-mypy [<args...>]`
**Maps to:** `uv run mypy <args>`

**Arguments:**

- `<args...>` (optional): Arguments to pass to mypy (e.g. src/ or --strict)

---
