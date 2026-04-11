---
name: nerfctl-grant-by-threat
description: Allow/deny nerf tools by threat profile (read/write ceiling)
argument-hint: --read <level> --write <level> [--filter <glob>] [--outside deny|reset] [--scope user|local]
disable-model-invocation: true
allowed-tools: Bash
---

Allow or deny nerf tools based on their threat profile. Tools within the
threat box (read <= ceiling AND write <= ceiling) are allowed. Tools outside
are denied or reset.

Threat levels (narrow to broad): `none`, `workspace`, `machine`, `remote`, `admin`

Quote all arguments so they are passed to the script unprocessed by the shell.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/nerfctl-grant-by-threat $ARGUMENTS
```

Report the output to the user.
