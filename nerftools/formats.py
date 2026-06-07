"""Plugin builders for nerf tools (v1).

Generates self-contained plugins from nerf manifests for Claude Code and
Codex, including skills, scripts, plugin manifests, and marketplace metadata.
"""

from __future__ import annotations

import re as re_module
from typing import TYPE_CHECKING

from nerftools.rendering import arg_line, maps_to_text, option_line, switch_line, usage_tokens

if TYPE_CHECKING:
    from pathlib import Path

    from nerftools.config import MarketplaceMetadata, PluginMetadata
    from nerftools.manifest import NerfManifest, ToolSpec

_NERFCTL_SKILLS = [
    {
        "dir_name": "nerfctl-grant-allow",
        "content": """\
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
""",
    },
    {
        "dir_name": "nerfctl-grant-deny",
        "content": """\
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
""",
    },
    {
        "dir_name": "nerfctl-grant-reset",
        "content": """\
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
""",
    },
    {
        "dir_name": "nerfctl-grant-by-threat",
        "content": """\
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
""",
    },
    {
        "dir_name": "nerfctl-grant-list",
        "content": """\
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
""",
    },
]


def build_claude_plugin(
    manifests: list[NerfManifest],
    output_dir: Path,
    plugin_meta: PluginMetadata,
    *,
    prefix: str = "nerf-",
    marketplace_meta: MarketplaceMetadata | None = None,
    emit_session_start_hook: bool = True,
    emit_pretool_bash_hint_hook: bool = True,
    keep_existing: bool = False,
    force: bool = False,
) -> list[Path]:
    """Build a self-contained Claude Code plugin.

    Layout:
        output_dir/
        ├── .claude-plugin/
        │   ├── plugin.json
        │   └── marketplace.json    (only if marketplace_meta is provided)
        └── skills/
            ├── <plugin-name>/SKILL.md       (overview)
            ├── <prefix><group>/
            │   ├── SKILL.md
            │   └── scripts/<prefix><tool>   (executable scripts)
            └── ...

    Pass marketplace_meta when the output is intended to be added directly
    as a standalone marketplace (e.g. deployed to a VM and registered via
    `claude plugin marketplace add <dir>`). Leave it None when distributing
    via a repo-level marketplace that points at the plugin directory as a
    source.
    """
    import json

    from nerftools import install_nerf_report, install_nerfctl
    from nerftools.builder import build_script_text
    from nerftools.outdir import prepare_output_dir

    written: list[Path] = []

    safe_to_mark = prepare_output_dir(
        output_dir,
        target="claude-plugin",
        keep_existing=keep_existing,
        force=force,
        clean="all",
    )

    # Plugin manifest
    plugin_dir = output_dir / ".claude-plugin"
    plugin_dir.mkdir(exist_ok=True)

    p = plugin_dir / "plugin.json"
    p.write_text(json.dumps(plugin_meta.to_json(), indent=2) + "\n")
    written.append(p)

    if marketplace_meta is not None:
        p = plugin_dir / "marketplace.json"
        p.write_text(json.dumps(marketplace_meta.to_json(plugin_meta), indent=2) + "\n")
        written.append(p)

    skills_dir = output_dir / "skills"
    skills_dir.mkdir(exist_ok=True)

    # Per-package: skill + scripts
    for manifest in manifests:
        group = prefix + manifest.package.skill_group
        skill_dir = skills_dir / group
        skill_dir.mkdir(exist_ok=True)
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        # Generate scripts into the skill's scripts/ dir
        for tool_name, tool_spec in manifest.tools.items():
            full_name = prefix + tool_name
            script_text = build_script_text(full_name, manifest.package.name, tool_spec)
            out = scripts_dir / full_name
            out.write_bytes(script_text.encode("utf-8"))
            out.chmod(0o755)
            written.append(out)

        # Generate skill with claude-plugin path references
        skill_text = _build_claude_plugin_skill_text(manifest, prefix=prefix)
        out = skill_dir / "SKILL.md"
        out.write_text(skill_text)
        written.append(out)

    # nerfctl scripts go in the plugin-level scripts/ dir
    scripts_root = output_dir / "scripts"
    scripts_root.mkdir(exist_ok=True)
    nerfctl_written = install_nerfctl(scripts_root)
    written.extend(nerfctl_written)

    # Hooks: SessionStart intro (+ bash-version warning) plus, when any
    # package declares bash_hints, a PreToolUse redirect dispatcher. Either
    # may be opted out of via the plugin config.
    emit_hint_hook = emit_pretool_bash_hint_hook and any(m.package.bash_hints for m in manifests)
    hook_events: dict[str, list[dict[str, object]]] = {}

    if emit_session_start_hook or emit_hint_hook:
        hooks_dir = output_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        if emit_session_start_hook:
            session_hook = hooks_dir / "nerf-session-start"
            session_hook.write_text(
                _build_session_start_hook_script(plugin_meta, manifests, prefix=prefix)
            )
            session_hook.chmod(0o755)
            written.append(session_hook)
            hook_events["SessionStart"] = [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/nerf-session-start",
                        }
                    ],
                }
            ]

        if emit_hint_hook:
            hint_hook = hooks_dir / _HOOK_FILENAME
            hint_hook.write_text(
                _build_pre_tool_use_hook_script(
                    manifests, prefix=prefix, plugin_name=plugin_meta.name
                )
            )
            hint_hook.chmod(0o755)
            written.append(hint_hook)
            hook_events["PreToolUse"] = [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"${{CLAUDE_PLUGIN_ROOT}}/hooks/{_HOOK_FILENAME}",
                        }
                    ],
                }
            ]

        cfg = hooks_dir / "hooks.json"
        cfg.write_text(json.dumps({"hooks": hook_events}, indent=2) + "\n")
        written.append(cfg)

    # nerfctl user-invokable skills (grant, deny, reset, list)
    for nerfctl_skill in _NERFCTL_SKILLS:
        skill_dir = skills_dir / nerfctl_skill["dir_name"]
        skill_dir.mkdir(exist_ok=True)
        out = skill_dir / "SKILL.md"
        out.write_text(nerfctl_skill["content"])
        written.append(out)

    # nerf-report skill: bundled script + SKILL.md
    nerf_report_dir = skills_dir / "nerf-report"
    nerf_report_scripts = nerf_report_dir / "scripts"
    nerf_report_script = install_nerf_report(nerf_report_scripts, version=plugin_meta.version)
    written.append(nerf_report_script)
    nerf_report_skill = nerf_report_dir / "SKILL.md"
    nerf_report_skill.write_text(
        _build_nerf_report_skill_text(
            script_path="${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report"
        )
    )
    written.append(nerf_report_skill)

    # Overview skill (named after the plugin, so the user-facing invocation is /<plugin>:<plugin>)
    if manifests:
        overview_text = _build_claude_plugin_overview_text(manifests, plugin_meta, prefix=prefix)
        overview_dir = skills_dir / plugin_meta.name
        overview_dir.mkdir(exist_ok=True)
        out = overview_dir / "SKILL.md"
        out.write_text(overview_text)
        written.append(out)

    if safe_to_mark:
        from nerftools.outdir import write_build_marker

        write_build_marker(output_dir, target="claude-plugin")
    return written


_NERF_REPORT_FOOTER = (
    "_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? "
    "Use the `nerf-report` skill._"
)


def _build_nerf_report_skill_text(*, script_path: str) -> str:
    """SKILL.md for the nerf-report tool. *script_path* is the path the agent
    should invoke -- absolute (`${CLAUDE_PLUGIN_ROOT}/...`) for Claude, or
    relative-to-skill (`scripts/nerf-report`) for Codex.
    """
    return f"""\
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
- `bypass` -- you ran a command directly instead of via the nerf wrapper
  that would normally cover it (any reason: wrapper too restrictive,
  missing a flag, has a bug, doesn't fit this case, etc.). When the
  PreToolUse Bash hint hook would have redirected your raw call, run
  `nerf-report bypass` *first*, then append the resulting report
  filename to the command as `# nerf:bypass <report-filename>` (replace
  `nerf` with your configured brand if different).
- `complaint` -- the tool works but the UX got in your way (cryptic error,
  surprising default, missing flag forced a workaround)
- `request` -- you'd like a new tool, option, or behavior

`<tool>` is the nerf tool you're reporting about (e.g. `nerf-az-repos-pr-edit`),
or `nerftools` for meta-issues about the package itself.

`<body>` is free-form prose. Quote it so the shell passes it through as a
single argument.

```bash
{script_path} <kind> <tool> "<body>"
```

Examples:

```bash
{script_path} bypass nerf-az-repos-pr-edit "guard demanded --title|--description|--draft; I wanted to update reviewers only"
{script_path} bug nerf-gh-pr-ready "rejected --undo on a draft PR even though gh pr ready --undo is documented"
{script_path} complaint nerf-git-commit "Conventional Commits regex rejects multi-scope (gh,az); had to commit twice"
{script_path} request nerf-az-repos-pr-comments "would like --since <timestamp> to filter recent comments"
```

The script auto-captures the timestamp, working directory, agent session
ID, and nerftools version into the report's frontmatter -- you don't need
to include those in the body.
"""


def _build_claude_plugin_skill_text(manifest: NerfManifest, prefix: str = "") -> str:
    """Generate a SKILL.md for the claude-plugin format.

    Uses ${CLAUDE_PLUGIN_ROOT} for script paths so Claude Code resolves them
    to absolute paths before the agent sees them.
    """
    parts: list[str] = []
    skill_group = prefix + manifest.package.skill_group

    parts.append("---")
    parts.append(f"name: {skill_group}")
    parts.append(f'description: "{manifest.package.description}"')
    parts.append('targets: ["*"]')
    parts.append("---")
    parts.append("")
    parts.append(f"# {skill_group}")
    parts.append("")
    parts.append(
        "These tools are available as scripts within this plugin. "
        "Call them using the absolute paths shown in each usage line."
    )
    parts.append("")

    if manifest.package.skill_intro:
        parts.append(manifest.package.skill_intro.strip())
        parts.append("")

    for tool_name, tool_spec in manifest.tools.items():
        full_name = prefix + tool_name
        parts.append(_claude_plugin_tool_section(full_name, skill_group, tool_spec))

    parts.append(_NERF_REPORT_FOOTER)

    return "\n".join(parts).rstrip() + "\n"


def _tool_section(tool_name: str, tool_spec: ToolSpec, *, script_path: str) -> str:
    """Generate a tool section for a plugin skill.

    Shared by all plugin targets — the caller passes the resolved *script_path*
    (absolute for Claude, relative for Codex).
    """
    parts: list[str] = []
    parts.append(f"## {tool_name}")
    parts.append("")
    parts.append(tool_spec.description)
    parts.append("")

    usage = " ".join([script_path, *usage_tokens(tool_spec)])
    parts.append(f"**Usage:** `{usage}`")

    maps_to = maps_to_text(tool_spec)
    if maps_to:
        parts.append(f"**Maps to:** `{maps_to}`")
    parts.append("")

    if tool_spec.passthrough is not None and tool_spec.passthrough.deny:
        denied = ", ".join(f"`{d}`" for d in tool_spec.passthrough.deny)
        parts.append(f"**Denied patterns:** {denied}")
        parts.append("")

    has_params = bool(tool_spec.switches) or bool(tool_spec.options) or bool(tool_spec.arguments)
    if has_params:
        if tool_spec.switches:
            parts.append("**Switches:**")
            parts.append("")
            for _name, sw in tool_spec.switches.items():
                parts.append(switch_line(sw))
            parts.append("")

        if tool_spec.options:
            parts.append("**Options:**")
            parts.append("")
            for name, opt in tool_spec.options.items():
                parts.append(option_line(name, opt))
            parts.append("")

        if tool_spec.arguments:
            parts.append("**Arguments:**")
            parts.append("")
            for name, spec in tool_spec.arguments.items():
                parts.append(arg_line(name, spec))
            parts.append("")
    else:
        if tool_spec.passthrough is None:
            parts.append("No arguments.")
            parts.append("")

    parts.append("---")
    parts.append("")
    return "\n".join(parts)


def _claude_plugin_tool_section(tool_name: str, skill_group: str, tool_spec: ToolSpec) -> str:
    """Generate a tool section using ``${CLAUDE_PLUGIN_ROOT}`` paths."""
    script_path = f"${{CLAUDE_PLUGIN_ROOT}}/skills/{skill_group}/scripts/{tool_name}"
    return _tool_section(tool_name, tool_spec, script_path=script_path)


def _overview_text(
    manifests: list[NerfManifest],
    plugin_meta: PluginMetadata,
    prefix: str = "",
    *,
    path_instruction: str,
) -> str:
    """Generate the overview SKILL.md shared by all plugin targets."""
    parts: list[str] = []

    parts.append("---")
    parts.append(f"name: {plugin_meta.name}")
    parts.append(f'description: "{plugin_meta.description}"')
    parts.append('targets: ["*"]')
    parts.append("---")
    parts.append("")
    parts.append(f"# {plugin_meta.name}")
    parts.append("")
    parts.append(
        "This environment has nerf tools installed. These are scoped, safety-constrained wrappers for "
        "common CLI operations like git, az, and other tools. They enforce guardrails (validated "
        "parameters, restricted flags, pre-flight checks) that keep operations safe and auditable."
    )
    parts.append("")
    parts.append(
        "When a nerf tool exists that covers the operation you need, prefer it over invoking the "
        "underlying tool directly. Shape your workflow to take advantage of them. For example, "
        "stage files with the nerf git-add tool and then commit with the nerf git-commit tool, "
        "rather than using raw `git` commands."
    )
    parts.append("")
    parts.append(path_instruction)
    parts.append("")
    parts.append("## Available tool packages")
    parts.append("")

    for manifest in manifests:
        group = prefix + manifest.package.skill_group
        parts.append(f"- **{group}**: {manifest.package.description}")

    parts.append("")
    parts.append("Use the corresponding `nerf-*` skill for full usage details on each package.")
    parts.append("")
    parts.append("## Feedback")
    parts.append("")
    parts.append(
        "Found a problem or want a change? Use the `nerf-report` skill to file a structured "
        "report (`bug`, `bypass`, `complaint`, or `request`). The maintainer triages them."
    )

    return "\n".join(parts).rstrip() + "\n"


def _build_claude_plugin_overview_text(
    manifests: list[NerfManifest],
    plugin_meta: PluginMetadata,
    prefix: str = "",
) -> str:
    """Generate the overview SKILL.md for the claude-plugin format."""
    return _overview_text(
        manifests,
        plugin_meta,
        prefix,
        path_instruction=(
            "Each tool's usage line shows the full absolute path to call it. "
            "Use that path directly in Bash commands."
        ),
    )


# -- Codex plugin format -------------------------------------------------------


def build_codex_plugin(
    manifests: list[NerfManifest],
    output_dir: Path,
    plugin_meta: PluginMetadata,
    *,
    prefix: str = "nerf-",
    keep_existing: bool = False,
    force: bool = False,
) -> list[Path]:
    """Build a self-contained Codex plugin.

    Layout::

        output_dir/
        ├── .codex-plugin/
        │   └── plugin.json
        └── skills/
            ├── <plugin-name>/SKILL.md       (overview)
            ├── <prefix><group>/
            │   ├── SKILL.md
            │   └── scripts/<prefix><tool>   (executable scripts)
            └── ...

    Script paths in SKILL.md are relative to the skill directory — Codex
    resolves them from the absolute path it injects into the system prompt.

    Note: `bash_hints` (the PreToolUse redirect hook used by the Claude
    plugin) is not yet emitted for Codex; once Codex's hook API is
    verified end-to-end, a parallel dispatcher can be wired up here.
    """
    import json

    from nerftools import install_nerf_report
    from nerftools.builder import build_script_text
    from nerftools.outdir import prepare_output_dir

    written: list[Path] = []

    safe_to_mark = prepare_output_dir(
        output_dir,
        target="codex-plugin",
        keep_existing=keep_existing,
        force=force,
        clean="all",
    )

    # Plugin manifest
    plugin_dir = output_dir / ".codex-plugin"
    plugin_dir.mkdir(exist_ok=True)

    p = plugin_dir / "plugin.json"
    p.write_text(json.dumps(plugin_meta.to_json(), indent=2) + "\n")
    written.append(p)

    skills_dir = output_dir / "skills"
    skills_dir.mkdir(exist_ok=True)

    # Per-package: skill + scripts
    for manifest in manifests:
        group = prefix + manifest.package.skill_group
        skill_dir = skills_dir / group
        skill_dir.mkdir(exist_ok=True)
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        # Generate scripts into the skill's scripts/ dir
        for tool_name, tool_spec in manifest.tools.items():
            full_name = prefix + tool_name
            script_text = build_script_text(full_name, manifest.package.name, tool_spec)
            out = scripts_dir / full_name
            out.write_bytes(script_text.encode("utf-8"))
            out.chmod(0o755)
            written.append(out)

        # Generate skill with relative path references
        skill_text = _build_codex_plugin_skill_text(manifest, prefix=prefix)
        out = skill_dir / "SKILL.md"
        out.write_text(skill_text)
        written.append(out)

    # nerf-report skill: bundled script + SKILL.md (paths relative to the
    # skill dir, matching the codex per-package skill convention).
    nerf_report_dir = skills_dir / "nerf-report"
    nerf_report_scripts = nerf_report_dir / "scripts"
    nerf_report_script = install_nerf_report(nerf_report_scripts, version=plugin_meta.version)
    written.append(nerf_report_script)
    nerf_report_skill = nerf_report_dir / "SKILL.md"
    nerf_report_skill.write_text(
        _build_nerf_report_skill_text(script_path="scripts/nerf-report")
    )
    written.append(nerf_report_skill)

    # Overview skill
    if manifests:
        overview_text = _overview_text(
            manifests,
            plugin_meta,
            prefix,
            path_instruction=(
                "Each tool's usage line shows the path to call it relative to "
                "this skill's directory."
            ),
        )
        overview_dir = skills_dir / plugin_meta.name
        overview_dir.mkdir(exist_ok=True)
        out = overview_dir / "SKILL.md"
        out.write_text(overview_text)
        written.append(out)

    if safe_to_mark:
        from nerftools.outdir import write_build_marker

        write_build_marker(output_dir, target="codex-plugin")
    return written


def _build_codex_plugin_skill_text(manifest: NerfManifest, prefix: str = "") -> str:
    """Generate a SKILL.md for the codex-plugin format.

    Uses relative script paths — Codex resolves them from the skill's
    listed file path in the system prompt.
    """
    parts: list[str] = []
    skill_group = prefix + manifest.package.skill_group

    parts.append("---")
    parts.append(f"name: {skill_group}")
    parts.append(f'description: "{manifest.package.description}"')
    parts.append('targets: ["*"]')
    parts.append("---")
    parts.append("")
    parts.append(f"# {skill_group}")
    parts.append("")
    parts.append(
        "These tools are available as scripts within this skill. "
        "Call them using the paths shown in each usage line."
    )
    parts.append("")

    if manifest.package.skill_intro:
        parts.append(manifest.package.skill_intro.strip())
        parts.append("")

    for tool_name, tool_spec in manifest.tools.items():
        full_name = prefix + tool_name
        script_path = f"scripts/{full_name}"
        parts.append(_tool_section(full_name, tool_spec, script_path=script_path))

    parts.append(_NERF_REPORT_FOOTER)

    return "\n".join(parts).rstrip() + "\n"


# -- PreToolUse hint hook (claude-plugin) --------------------------------------


_HINT_HOOK_TEMPLATE = '''\
#!/usr/bin/env bash
# Auto-generated by nerftools: PreToolUse multi-check dispatcher.
#
# Runs the following opt-in checks against the Bash command the agent is
# about to run. Checks run in declaration order; the first denial short-
# circuits the rest. Each check is independently env-var gated and
# brand-namespaced so multiple plugins with different brands can coexist.
#
# 1. Current-version check  (env: __BRAND_VERSION_ENV__)
#    Refuses to run a tool invocation whose path points at an OLD or NEW
#    version of THIS plugin (catches stale tool paths that an agent may
#    have cached from a prior session after a plugin upgrade). Matches
#    on plugin owner, plugin name (including brand), and tool-name brand
#    prefix to avoid false positives on other plugins. NO bypass
#    sentinel -- this check is intentionally strict.
#
# 2. Bash-hint check        (env: __BRAND_HINT_ENV__)
#    Refuses raw bash commands matching a wrapper's bash_hints pattern;
#    redirects the agent to the wrapper. Bypassable via the sentinel
#    `# __BRAND__:bypass-bash-hint <reason>` (non-empty reason required).
#
# Fail-open: if bash < 4 or jq is missing, this hook exits 0 silently.
# A SessionStart hook surfaces a warning so the user knows the redirect
# is disabled.

if [[ "${BASH_VERSINFO[0]:-0}" -lt 4 ]]; then
  exit 0
fi

set -uo pipefail

_WRAPPER_PREFIX="__PREFIX__"
_BRAND="__BRAND__"
_BRAND_RE="__BRAND_RE__"
_PLUGIN_NAME="__PLUGIN_NAME__"

# Tab-separated <regex>\\t<skill> rows, declaration order. \\b boundaries in
# manifest patterns are translated to portable POSIX ERE at generation time
# so the hook works on macOS BSD regex (where \\b is not supported).
_PATTERNS=(
__PATTERNS__
)

command -v jq >/dev/null 2>&1 || exit 0

_input=$(cat)
_tool=$(printf '%s' "$_input" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
[[ "$_tool" == "Bash" ]] || exit 0

_cmd=$(printf '%s' "$_input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[[ -n "$_cmd" ]] || exit 0

emit_deny() {
  jq -nc --arg r "$1" \\
    '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $r}}'
}

# Find a version-aware sort (GNU `sort -V` or `gsort -V`). Returns "" on
# stdout if neither works.
_pick_version_sorter() {
  local probe_in=$'1.10.0\\n1.9.0\\n'
  local probe_out=$'1.9.0\\n1.10.0'
  local cmd
  for cmd in sort gsort; do
    command -v "$cmd" >/dev/null 2>&1 || continue
    if [[ "$(printf '%s' "$probe_in" | "$cmd" -V 2>/dev/null)" == "$probe_out" ]]; then
      echo "$cmd"
      return 0
    fi
  done
  return 1
}

# POSIX-ERE escape a literal string so it can be safely interpolated into
# a regex. Escapes: . ^ $ * + ? | [ ] { } ( ) \\
_ere_escape() {
  local s="$1"
  s="${s//\\\\/\\\\\\\\}"
  s="${s//./\\\\.}"
  s="${s//^/\\\\^}"
  s="${s//\\$/\\\\$}"
  s="${s//\\*/\\\\*}"
  s="${s//+/\\\\+}"
  s="${s//\\?/\\\\?}"
  s="${s//|/\\\\|}"
  s="${s//[/\\\\[}"
  s="${s//]/\\\\]}"
  s="${s//\\{/\\\\\\{}"
  s="${s//\\}/\\\\\\}}"
  s="${s//(/\\\\(}"
  s="${s//)/\\\\)}"
  printf '%s' "$s"
}

# -- Check: current version --------------------------------------------------
#
# Self-derive this plugin's prefix + current version, then verify the
# command isn't invoking a tool path under a different version of OUR
# plugin. Method 1 (preferred): walk up from this hook's own path.
# Method 2 (fallback): scan ~/.claude/plugins/cache/*/<plugin>/ for the
# max version directory. Method 3: skip with warning.
_check_current_version() {
  case "${__BRAND_VERSION_ENV__:-}" in
    1 | [tT][rR][uU][eE] | [yY][eE][sS] | [oO][nN]) ;;
    *) return 0 ;;
  esac

  local self_path version_dir plugin_dir current_version=""
  self_path=$(realpath "$0" 2>/dev/null) || {
    echo "warning: __HOOK_NAME__: cannot resolve own path; skipping current-version check" >&2
    return 0
  }
  version_dir=$(dirname "$(dirname "$self_path")")
  if [[ -d "$version_dir/skills" && -d "$version_dir/.claude-plugin" ]]; then
    plugin_dir=$(dirname "$version_dir")
    current_version=$(basename "$version_dir")
  else
    # Fallback: scan cache for any owner with our plugin name.
    local vsort
    vsort=$(_pick_version_sorter) || {
      echo "warning: __HOOK_NAME__: cannot self-derive plugin location and no version-aware sort available; skipping current-version check" >&2
      return 0
    }
    plugin_dir=""
    local versions="" _p _vd
    for _p in "$HOME/.claude/plugins/cache"/*/"$_PLUGIN_NAME"; do
      [[ -d "$_p" ]] || continue
      plugin_dir="$_p"
      while IFS= read -r _vd; do
        [[ -d "$_vd" ]] && versions+="$(basename "$_vd")"$'\\n'
      done < <(find "$_p" -maxdepth 1 -mindepth 1 -type d 2>/dev/null)
    done
    if [[ -z "$plugin_dir" || -z "$versions" ]]; then
      echo "warning: __HOOK_NAME__: cannot determine plugin location; skipping current-version check" >&2
      return 0
    fi
    current_version=$(printf '%s' "$versions" | "$vsort" -V | tail -1)
  fi

  # Extract called versions from absolute paths in the command that match
  # OUR plugin tree and a brand-prefixed tool script.
  local escaped_prefix escaped_brand path_re called=""
  escaped_prefix=$(_ere_escape "$plugin_dir/")
  escaped_brand=$(_ere_escape "$_BRAND")
  path_re="${escaped_prefix}[^/[:space:]]+/skills/[^/[:space:]]+/scripts/${escaped_brand}-[^[:space:]]+"
  if command -v grep >/dev/null 2>&1; then
    called=$(printf '%s' "$_cmd" | grep -oE "$path_re" 2>/dev/null \\
      | sed -E "s|^${escaped_prefix}([^/]+)/.*|\\\\1|" | sort -u)
  fi
  [[ -z "$called" ]] && return 0

  local v mismatch=""
  while IFS= read -r v; do
    [[ -z "$v" ]] && continue
    if [[ "$v" != "$current_version" ]]; then mismatch="$v"; break; fi
  done <<< "$called"
  [[ -z "$mismatch" ]] && return 0

  # Direction: older vs newer. Use sort -V if available; otherwise treat
  # as "older" conservatively (still a deny, just with the safer message).
  local direction="older" vsort
  vsort=$(_pick_version_sorter) || vsort=""
  if [[ -n "$vsort" ]] && [[ "$(printf '%s\\n%s\\n' "$mismatch" "$current_version" | "$vsort" -V | tail -1)" == "$mismatch" ]]; then
    direction="newer"
  fi

  local msg
  if [[ "$direction" == "older" ]]; then
    msg="You invoked an older version of this plugin's tools (called: ${mismatch}, current: ${current_version}). You must use the current version ${current_version}.

If you suspect a configuration or plugin-install problem, stop and report this to the user immediately and await instructions.

Otherwise, if the latest version's tools appear broken or are missing functionality you need, consider filing a nerf-report (if the skill is available), or stop and report directly to the user and await instructions.

Do not attempt to work around this. Work within the provided tools and escalate to the user if things seem off."
  else
    msg="You invoked a NEWER version of this plugin's tools than is currently installed (called: ${mismatch}, installed: ${current_version}). This indicates a serious configuration inconsistency.

Stop immediately. Report this condition to the user and await instructions.

Do not attempt to work around this."
  fi

  emit_deny "$msg"
  exit 0
}

# -- Check: bash hint --------------------------------------------------------

_check_bash_hint() {
  case "${__BRAND_HINT_ENV__:-}" in
    1 | [tT][rR][uU][eE] | [yY][eE][sS] | [oO][nN]) ;;
    *) return 0 ;;
  esac

  # Skip the redirect when the command is invoking a wrapper itself. We
  # split on common shell separators (&&, ||, ;, |, &) into segments,
  # skip any leading "VAR=val" env-var assignments in each segment, and
  # check whether the first remaining token's basename starts with the
  # wrapper prefix.
  if [[ -n "$_WRAPPER_PREFIX" ]]; then
    local _norm="${_cmd//&&/$'\\n'}"
    _norm="${_norm//||/$'\\n'}"
    _norm="${_norm//[|;&]/$'\\n'}"
    local _seg _toks _exec _t _base
    while IFS= read -r _seg; do
      _seg="${_seg#"${_seg%%[![:space:]]*}"}"
      [[ -z "$_seg" ]] && continue
      read -r -a _toks <<< "$_seg"
      _exec=""
      for _t in "${_toks[@]:-}"; do
        if [[ "$_t" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
          continue
        fi
        _exec="$_t"
        break
      done
      [[ -z "$_exec" ]] && continue
      _base="${_exec##*/}"
      if [[ "$_base" == "$_WRAPPER_PREFIX"* ]]; then
        return 0
      fi
    done <<< "$_norm"
  fi

  # Bypass sentinel for THIS check only. Other checks (e.g. current-version)
  # are not bypassable via this sentinel.
  local _bypass_re="# ${_BRAND_RE}:bypass-bash-hint[[:space:]]+[^[:space:]]"
  if [[ "$_cmd" =~ $_bypass_re ]]; then
    return 0
  fi

  local _matched=() _row _pat _skill _already _m
  for _row in "${_PATTERNS[@]:-}"; do
    _pat="${_row%%$'\\t'*}"
    _skill="${_row##*$'\\t'}"
    _already=0
    for _m in "${_matched[@]:-}"; do
      if [[ "$_m" == "$_skill" ]]; then _already=1; break; fi
    done
    [[ $_already -eq 1 ]] && continue
    if [[ "$_cmd" =~ $_pat ]]; then
      _matched+=("$_skill")
    fi
  done

  [[ ${#_matched[@]} -eq 0 ]] && return 0

  local _list="" _s
  for _s in "${_matched[@]}"; do
    if [[ -z "$_list" ]]; then _list="\\`${_s}\\`"; else _list="${_list}, \\`${_s}\\`"; fi
  done

  local _msg="The following ${_BRAND} skill(s) may wrap this command: ${_list}.

Use one if it covers what you need. To run the command directly anyway:
1. File a 'bypass' report via the \\`nerf-report\\` skill explaining what you needed and why the listed wrapper(s) didn't fit.
2. Retry the command with the resulting report filename appended as \\`# ${_BRAND}:bypass-bash-hint <report-filename>\\`."

  emit_deny "$_msg"
  exit 0
}

# Run in declaration order; each denies-and-exits on its own.
_check_current_version
_check_bash_hint
'''


def _derive_brand(prefix: str) -> str:
    """Derive the sentinel/annotation brand from the wrapper prefix.

    ``"nerf-"`` -> ``"nerf"``, ``"mytool-"`` -> ``"mytool"``. Falls back to
    ``"nerf"`` when the prefix is empty or contains only separators.
    """
    return prefix.rstrip("-_") or "nerf"


def _derive_brand_env_var(brand: str, check_suffix: str = "BASH_HINT_HOOK") -> str:
    """Derive a brand-namespaced env var that opts a check in.

    Two plugins with different brands installed side-by-side need
    independent kill switches; namespacing the env var by brand makes
    them non-interfering. Each PreToolUse check has its own env var
    suffix so checks can be enabled/disabled independently.

    Examples:
      ``("nerf")`` -> ``"NERF_ENABLE_BASH_HINT_HOOK"`` (legacy default)
      ``("nerf", "CURRENT_VERSION_HOOK")`` -> ``"NERF_ENABLE_CURRENT_VERSION_HOOK"``
      ``("my-tool", "BASH_HINT_HOOK")`` -> ``"MY_TOOL_ENABLE_BASH_HINT_HOOK"``
    """
    sanitized = re_module.sub(r"[^A-Z0-9]", "_", brand.upper())
    # Env var names can't start with a digit.
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return f"{sanitized}_ENABLE_{check_suffix}"


def _build_pre_tool_use_hook_script(
    manifests: list[NerfManifest], *, prefix: str, plugin_name: str
) -> str:
    """Render the PreToolUse multi-check dispatcher with patterns baked in."""
    brand = _derive_brand(prefix)
    rows: list[str] = []
    for manifest in manifests:
        skill_name = prefix + manifest.package.skill_group
        for pattern in manifest.package.bash_hints:
            portable = _to_portable_ere(pattern)
            row = f"{portable}\t{skill_name}"
            rows.append(f"  $'{_bash_dollar_escape(row)}'")
    return (
        _HINT_HOOK_TEMPLATE
        .replace("__PATTERNS__", "\n".join(rows))
        .replace("__PREFIX__", _bash_double_quote_escape(prefix))
        .replace("__BRAND__", _bash_double_quote_escape(brand))
        .replace("__BRAND_RE__", _bash_double_quote_escape(_ere_escape(brand)))
        .replace("__BRAND_HINT_ENV__", _derive_brand_env_var(brand, "BASH_HINT_HOOK"))
        .replace(
            "__BRAND_VERSION_ENV__",
            _derive_brand_env_var(brand, "CURRENT_VERSION_HOOK"),
        )
        .replace("__PLUGIN_NAME__", _bash_double_quote_escape(plugin_name))
        .replace("__HOOK_NAME__", _HOOK_FILENAME)
    )


# Filename for the generated PreToolUse hook. Named after the event type
# (PreToolUse) rather than any specific check, since the script runs multiple
# checks and may grow more over time.
_HOOK_FILENAME = "nerf-pre-tool-use"


# Word-boundary translation: bash's =~ uses the host POSIX ERE engine, which
# does not portably recognize \b (GNU extension; absent on macOS BSD libc).
# Translate \b in manifest-author patterns to a portable alternation that
# matches start-of-string, end-of-string, or a non-word char at that
# position. Equivalent for matching purposes; the surrounding non-word char,
# when present, is consumed (the hook only cares about a match, not a span).
_BACKSLASH_B_RE = re_module.compile(r"\\b")

# POSIX ERE metacharacters that must be backslash-escaped when a literal
# string is interpolated into a regex.
_ERE_META = set(r".[]{}()\^$|?*+")


def _to_portable_ere(pattern: str) -> str:
    """Translate ``\\b`` word boundaries in *pattern* to portable POSIX ERE."""
    return _BACKSLASH_B_RE.sub(r"(^|$|[^[:alnum:]_])", pattern)


def _ere_escape(s: str) -> str:
    """Backslash-escape POSIX ERE metacharacters in *s* for literal matching."""
    return "".join("\\" + c if c in _ERE_META else c for c in s)


def _bash_dollar_escape(s: str) -> str:
    """Escape a string for use inside bash ``$'...'`` ANSI-C quoting.

    Escapes backslashes and single quotes; tabs and newlines remain literal
    in the caller-provided value (the manifest writer is responsible for
    those).
    """
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _bash_double_quote_escape(s: str) -> str:
    """Escape a string for use inside bash ``"..."`` double-quoted strings."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")


_SESSION_START_TEMPLATE = '''\
#!/usr/bin/env bash
# Auto-generated by nerftools: SessionStart hook.
#
# Greets the agent with a one-time reminder that the plugin is installed
# and what it covers. Appends additional, env-gated reminders for each
# PreToolUse check that's currently enabled. Appends a warning if the
# runtime bash is too old for the PreToolUse redirect hook to work.

set -uo pipefail

_PLUGIN_NAME="__PLUGIN_NAME__"
_PREFIX="__PREFIX__"

_intro="The \\`${_PLUGIN_NAME}\\` plugin is installed. It provides safety-constrained wrappers for __EXAMPLE_CLI_LIST__. Prefer these wrappers over raw bash for commands they cover. Load the \\`${_PLUGIN_NAME}\\` skill for the full overview, or any \\`${_PREFIX}<group>\\` skill__EXAMPLE_SKILL_HINT__ for specific tools. A pre-bash redirect hook may prompt you to use a wrapper when one is available."

_msg="$_intro"

# Reminder for the current-version check, when enabled. The agent gets a
# heads-up that mismatched-version invocations will be rejected, plus the
# specific version they should always use (self-derived from this hook's
# own location).
case "${__BRAND_VERSION_ENV__:-}" in
  1 | [tT][rR][uU][eE] | [yY][eE][sS] | [oO][nN])
    _self=$(realpath "$0" 2>/dev/null || echo "")
    _ver_dir=""
    if [[ -n "$_self" ]]; then
      _ver_dir=$(dirname "$(dirname "$_self")")
    fi
    _version=""
    if [[ -n "$_ver_dir" && -d "$_ver_dir/skills" && -d "$_ver_dir/.claude-plugin" ]]; then
      _version=$(basename "$_ver_dir")
    fi
    if [[ -n "$_version" ]]; then
      _msg="${_msg}"$'\\n\\n'"Current-version enforcement is enabled for \\`${_PLUGIN_NAME}\\`. Always invoke its tools from this session's plugin path (version ${_version}); the PreToolUse hook will reject calls that point at a different version. If you see paths in your context that reference an older version, ignore them and use the current paths."
    fi
    ;;
esac

if [[ "${BASH_VERSINFO[0]:-0}" -lt 4 ]]; then
  _msg="${_msg}"$'\\n\\n'"Warning: the pre-bash redirect hook is disabled because this system's bash is too old (found ${BASH_VERSION:-unknown}; bash 4+ required). Tell the user to install a newer bash (\\`brew install bash\\` on macOS, or via the system package manager on Linux) to enable it. Generated wrapper scripts may also fail until bash is upgraded."
fi

# Emit JSON via jq when available; otherwise fall back to a static notice
# that at least tells someone how to fix things.
if command -v jq >/dev/null 2>&1; then
  jq -nc --arg m "$_msg" \\
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $m}}'
else
  printf '%s\\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"nerftools: jq is required for nerftools hooks but is not installed. Tell the user to install jq."}}'
fi
'''


def _build_session_start_hook_script(
    plugin_meta: PluginMetadata,
    manifests: list[NerfManifest],
    *,
    prefix: str,
) -> str:
    """Render the SessionStart hook script with plugin identity baked in.

    The example CLI list and the example skill name are derived from the
    actual manifests bundled in this build, so a plugin generated with a
    different package set advertises an accurate scope.
    """
    brand = _derive_brand(prefix)
    return (
        _SESSION_START_TEMPLATE
        .replace("__PLUGIN_NAME__", _bash_double_quote_escape(plugin_meta.name))
        .replace("__PREFIX__", _bash_double_quote_escape(prefix))
        .replace(
            "__BRAND_VERSION_ENV__",
            _derive_brand_env_var(brand, "CURRENT_VERSION_HOOK"),
        )
        .replace(
            "__EXAMPLE_CLI_LIST__",
            _bash_double_quote_escape(_example_cli_list(manifests)),
        )
        .replace(
            "__EXAMPLE_SKILL_HINT__",
            _bash_double_quote_escape(_example_skill_hint(manifests, prefix=prefix)),
        )
    )


def _example_cli_list(manifests: list[NerfManifest]) -> str:
    """Build a short, human-readable list of CLI families from manifest names.

    Dedupe by first ``-``-separated component so packages like ``az-account``,
    ``az-aks`` collapse to a single ``az``. Caps at the first 5 distinct
    families with an "and more" tail for longer plugins; falls back to a
    generic phrase for the empty case.
    """
    families: list[str] = []
    for m in manifests:
        first = m.package.skill_group.split("-", 1)[0]
        if first and first not in families:
            families.append(first)
    if not families:
        return "various CLIs"
    if len(families) > 5:
        return ", ".join(families[:5]) + ", and more"
    return ", ".join(families)


def _example_skill_hint(manifests: list[NerfManifest], *, prefix: str) -> str:
    """Return ``" (e.g. <prefix><group>)"`` for the first real manifest, else ``""``."""
    for m in manifests:
        return f" (e.g. `{prefix}{m.package.skill_group}`)"
    return ""
