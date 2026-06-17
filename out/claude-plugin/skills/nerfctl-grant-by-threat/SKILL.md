---
name: nerfctl-grant-by-threat
description: Allow/deny nerf tools by threat profile (read/write ceiling)
argument-hint: <scope> --read <level> --write <level> [--filter <glob>] [--outside deny|reset] [--reset-other-scopes]
disable-model-invocation: true
allowed-tools: Bash
---

Allow or deny nerf tools based on their threat profile. Tools within the
threat box (read <= ceiling AND write <= ceiling) are allowed. Tools outside
are denied or reset.

Threat levels (narrow to broad): `none`, `workspace`, `machine`, `remote`, `admin`

Scope is required and must be one of `user` (~/.claude/settings.json), `project`
(.claude/settings.json, committed), or `local` (.claude/settings.local.json, gitignored).
Pass `--reset-other-scopes` to clear matching entries from the two scopes you didn't
target, making the chosen scope the sole source of truth for these tools (otherwise
conflicting entries elsewhere are warned about).

Quote all arguments so they are passed to the script unprocessed by the shell.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/nerfctl-grant-by-threat $ARGUMENTS
```

Report the output to the user.
