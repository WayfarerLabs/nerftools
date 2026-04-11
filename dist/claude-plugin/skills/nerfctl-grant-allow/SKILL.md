---
name: nerfctl-grant-allow
description: Allow nerf tools without prompting (supports glob patterns like nerf-git-*)
argument-hint: <pattern> [--scope user|local]
disable-model-invocation: true
allowed-tools: Bash
---

Allow nerf tools matching the given pattern without prompting. Supports glob patterns
(e.g. `nerf-git-*` to allow all git tools). Default scope is user.

Quote all arguments so they are passed to the script unprocessed by the shell.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/nerfctl-grant-allow $ARGUMENTS
```

Report the output to the user.
