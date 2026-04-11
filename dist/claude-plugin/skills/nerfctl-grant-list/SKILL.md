---
name: nerfctl-grant-list
description: List nerf tool permissions across all scopes
argument-hint: [--scope user|local]
disable-model-invocation: true
allowed-tools: Bash
---

List all nerf tool permissions. Shows all scopes unless a specific scope is requested.

Run this command:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/nerfctl-grant-list $ARGUMENTS
```

Report the output to the user.
