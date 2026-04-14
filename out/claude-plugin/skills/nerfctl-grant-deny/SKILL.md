---
name: nerfctl-grant-deny
description: Deny nerf tools entirely (supports glob patterns like nerf-git-*)
argument-hint: <pattern> [--scope user|local]
disable-model-invocation: true
allowed-tools: Bash
---

Deny nerf tools matching the given pattern entirely. Supports glob patterns
(e.g. `nerf-git-*` to deny all git tools). Default scope is user.

Quote all arguments so they are passed to the script unprocessed by the shell.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/nerfctl-grant-deny $ARGUMENTS
```

Report the output to the user.
