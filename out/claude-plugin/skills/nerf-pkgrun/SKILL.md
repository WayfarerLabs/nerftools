---
name: nerf-pkgrun
description: "Package runner tools for cspell, markdownlint, and prettier at locked versions"
targets: ["*"]
---

# nerf-pkgrun

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools run npm packages at locked versions via the best available
package runner (bunx, pnpx, or npx). Pass arguments directly -- they are
forwarded to the underlying tool unchanged. Use pkgrun-cspell for spell
checking, pkgrun-markdownlint for Markdown linting, and pkgrun-prettier
for code formatting.

## nerf-pkgrun-cspell

Run cspell v8.19.4 with the given arguments (e.g. '**/*.md').

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-pkgrun/scripts/nerf-pkgrun-cspell <args...>`
**Maps to:** `<runner> cspell@8.19.4 <args>`

**Arguments:**

- `<args...>` (required): Arguments to pass to cspell (e.g. '**/*.md' or --words-only '**/*.md')

---

## nerf-pkgrun-markdownlint

Run markdownlint-cli2 v0.21.0 with the given arguments (e.g. '**/*.md').

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-pkgrun/scripts/nerf-pkgrun-markdownlint <args...>`
**Maps to:** `<runner> markdownlint-cli2@0.21.0 <args>`

**Arguments:**

- `<args...>` (required): Arguments to pass to markdownlint-cli2 (e.g. '**/*.md')

---

## nerf-pkgrun-prettier

Run prettier v3.8.1 with the given arguments (e.g. --write '**/*.ts').

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-pkgrun/scripts/nerf-pkgrun-prettier <args...>`
**Maps to:** `<runner> prettier@3.8.1 <args>`

**Arguments:**

- `<args...>` (required): Arguments to pass to prettier (e.g. --write '**/*.ts' or --check .)

---
