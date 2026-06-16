---
name: nerfctl-grant-allow
description: Allow nerf tools without prompting (supports glob patterns like nerf-git-*)
argument-hint: <scope> <pattern> [--reset-other-scopes]
disable-model-invocation: true
allowed-tools: Bash
---

Allow nerf tools matching the given pattern without prompting. Supports glob patterns
(e.g. `nerf-git-*` to allow all git tools).

Scope is required and must be one of `user` (~/.claude/settings.json), `project`
(.claude/settings.json, committed), or `local` (.claude/settings.local.json, gitignored).
Pass `--reset-other-scopes` to clear matching entries from the two scopes you didn't
target, making the chosen scope the sole source of truth for these tools (otherwise
conflicting entries elsewhere are warned about).

Quote all arguments so they are passed to the script unprocessed by the shell.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/nerfctl-grant-allow $ARGUMENTS
```

Report the output to the user.
