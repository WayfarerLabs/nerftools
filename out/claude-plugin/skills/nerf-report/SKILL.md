---
name: nerf-report
description: Report bugs, bypass reasons, complaints, or feature requests about nerf tools
argument-hint: <kind> <tool> <body>
allowed-tools: Bash
---

Use this when you hit something worth telling the nerftools maintainer about:
a bug, a guardrail you had to bypass (and why), a UX annoyance, or a feature
you wish existed. Reports land in `~/.nerftools/reports/` as Markdown files;
the maintainer triages them.

Pick the right `<kind>`:

- `bug` -- the tool produced wrong behavior, rejected valid input, or
  crashed
- `bypass` -- you bypassed a guardrail; explain what you needed to do and
  why the guard was in the way
- `complaint` -- the tool works but the UX got in your way (cryptic error,
  surprising default, missing flag forced a workaround)
- `request` -- you'd like a new tool, option, or behavior

`<tool>` is the nerf tool you're reporting about (e.g. `nerf-az-repos-pr-edit`),
or `nerftools` for meta-issues about the package itself.

`<body>` is free-form prose. Quote it so the shell passes it through as a
single argument.

```bash
${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report <kind> <tool> "<body>"
```

Examples:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report bypass nerf-az-repos-pr-edit "guard demanded --title|--description|--draft; I wanted to update reviewers only"
${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report bug nerf-gh-pr-ready "rejected --undo on a draft PR even though gh pr ready --undo is documented"
${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report complaint nerf-git-commit "Conventional Commits regex rejects multi-scope (gh,az); had to commit twice"
${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report request nerf-az-repos-pr-comments "would like --since <timestamp> to filter recent comments"
```

The script auto-captures the timestamp, working directory, agent session
ID, and nerftools version into the report's frontmatter -- you don't need
to include those in the body.
