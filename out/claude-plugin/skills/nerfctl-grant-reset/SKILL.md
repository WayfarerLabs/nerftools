---
name: nerfctl-grant-reset
description: Reset nerf tools to ask-every-time (supports glob patterns like nerf-git-*)
argument-hint: <pattern> [--scope user|local]
disable-model-invocation: true
allowed-tools: Bash
---

Reset permissions for nerf tools matching the given pattern back to the default
ask-every-time behavior. Supports glob patterns. Default scope is user.

Quote all arguments so they are passed to the script unprocessed by the shell.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/nerfctl-grant-reset $ARGUMENTS
```

Report the output to the user.
