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
    import shutil

    from nerftools import install_nerfctl
    from nerftools.builder import build_script_text

    written: list[Path] = []

    # Always start clean
    output_dir.mkdir(parents=True, exist_ok=True)
    for item in output_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        elif item.is_file():
            item.unlink()

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
            hint_hook = hooks_dir / "nerf-bash-hint"
            hint_hook.write_text(_build_bash_hint_hook_script(manifests, prefix=prefix))
            hint_hook.chmod(0o755)
            written.append(hint_hook)
            hook_events["PreToolUse"] = [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/nerf-bash-hint",
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

    # Overview skill (named after the plugin, so the user-facing invocation is /<plugin>:<plugin>)
    if manifests:
        overview_text = _build_claude_plugin_overview_text(manifests, plugin_meta, prefix=prefix)
        overview_dir = skills_dir / plugin_meta.name
        overview_dir.mkdir(exist_ok=True)
        out = overview_dir / "SKILL.md"
        out.write_text(overview_text)
        written.append(out)

    return written


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
    import shutil

    from nerftools.builder import build_script_text

    written: list[Path] = []

    # Always start clean
    output_dir.mkdir(parents=True, exist_ok=True)
    for item in output_dir.iterdir():
        if item.is_symlink():
            raise ValueError(
                f"refusing to clean symlink in output directory: {item}. "
                "Please remove the symlink manually before proceeding."
            )
        if item.is_dir():
            shutil.rmtree(item)
        elif item.is_file():
            item.unlink()

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

    return "\n".join(parts).rstrip() + "\n"


# -- PreToolUse hint hook (claude-plugin) --------------------------------------


_HINT_HOOK_TEMPLATE = '''\
#!/usr/bin/env bash
# Auto-generated by nerftools: PreToolUse Bash hint dispatcher.
#
# When the agent invokes a Bash command, this hook checks the command against
# package-declared regex patterns. If any match, the hook emits a `deny`
# permission decision listing the relevant skill(s), redirecting the agent to
# the safety-constrained wrappers. The deny is silent to the user.
#
# Sentinel `# __BRAND__:bypass <reason>` (non-empty reason) anywhere in the
# command allows the call through without matching. Empty reason still denies,
# with an explanation.
#
# Fail-open behavior: if bash < 4 or jq is missing, the hook exits 0 silently.
# A SessionStart hook surfaces a warning so the user knows the redirect is
# disabled.

# Fail open if bash is too old; the SessionStart companion warns the user.
if [[ "${BASH_VERSINFO[0]:-0}" -lt 4 ]]; then
  exit 0
fi

set -uo pipefail

_WRAPPER_PREFIX="__PREFIX__"
_BRAND="__BRAND__"
# Brand pre-escaped for regex use so a future prefix containing meta-chars
# (e.g. ".", "+") doesn't break the bypass sentinel match.
_BRAND_RE="__BRAND_RE__"

# Tab-separated <regex>\\t<skill> rows, declaration order. \\b boundaries in
# manifest patterns are translated to portable POSIX ERE at generation time
# so the hook works on macOS BSD regex (where \\b is not supported).
_PATTERNS=(
__PATTERNS__
)

# Fail open if jq is unavailable.
command -v jq >/dev/null 2>&1 || exit 0

_input=$(cat)
_tool=$(printf '%s' "$_input" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
[[ "$_tool" == "Bash" ]] || exit 0

_cmd=$(printf '%s' "$_input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[[ -n "$_cmd" ]] || exit 0

# Skip the redirect when the command is invoking a wrapper itself.
# We split on common shell separators (&&, ||, ;, |, &) into segments,
# skip any leading "VAR=val" env-var assignments in each segment, and
# check whether the first remaining token's basename starts with the
# wrapper prefix. This handles "cd /repo && nerf-git status", bash
# env-var prefixes ("FOO=bar nerf-git pull"), and absolute-path
# invocations like "/abs/path/nerf-git-add ." without skipping
# unrelated tokens that happen to contain the prefix at arg position
# (e.g. "git log --grep nerf-X"). Commands fronted by the POSIX `env`
# binary (or `nice`, `time`, `sudo`, etc.) are not specially recognized
# -- the runner is the executable; agents can use the bypass sentinel
# for that case.
if [[ -n "$_WRAPPER_PREFIX" ]]; then
  _norm="${_cmd//&&/$'\\n'}"
  _norm="${_norm//||/$'\\n'}"
  _norm="${_norm//[|;&]/$'\\n'}"
  while IFS= read -r _seg; do
    _seg="${_seg#"${_seg%%[![:space:]]*}"}"
    [[ -z "$_seg" ]] && continue
    read -ra _toks <<< "$_seg"
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
      exit 0
    fi
  done <<< "$_norm"
fi

emit_deny() {
  jq -nc --arg r "$1" \\
    '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $r}}'
}

# Bypass sentinel: "# <brand>:bypass <reason>" anywhere in the command.
_bypass_re="# ${_BRAND_RE}:bypass([^"$'\\n'"]*)"
if [[ "$_cmd" =~ $_bypass_re ]]; then
  _reason="${BASH_REMATCH[1]}"
  # Trim surrounding whitespace.
  _reason="${_reason#"${_reason%%[![:space:]]*}"}"
  _reason="${_reason%"${_reason##*[![:space:]]}"}"
  if [[ -n "$_reason" ]]; then
    exit 0
  fi
  emit_deny "The \\`# ${_BRAND}:bypass\\` marker requires a reason. Retry with \\`# ${_BRAND}:bypass <one-line explanation>\\`."
  exit 0
fi

# Collect matching skills in declaration order, deduped.
_matched=()
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

[[ ${#_matched[@]} -eq 0 ]] && exit 0

# Format skill list.
_list=""
for _s in "${_matched[@]}"; do
  if [[ -z "$_list" ]]; then
    _list="\\`${_s}\\`"
  else
    _list="${_list}, \\`${_s}\\`"
  fi
done

_msg="The following ${_BRAND} skill(s) may wrap this command: ${_list}.

Use one if it covers what you need. To run the command directly anyway, retry with a brief reason appended as \\`# ${_BRAND}:bypass <one-line explanation>\\`."

emit_deny "$_msg"
'''


def _derive_brand(prefix: str) -> str:
    """Derive the sentinel/annotation brand from the wrapper prefix.

    ``"nerf-"`` -> ``"nerf"``, ``"mytool-"`` -> ``"mytool"``. Falls back to
    ``"nerf"`` when the prefix is empty or contains only separators.
    """
    return prefix.rstrip("-_") or "nerf"


def _build_bash_hint_hook_script(manifests: list[NerfManifest], *, prefix: str) -> str:
    """Render the PreToolUse hint dispatcher with patterns baked in."""
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
    )


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
# and what it covers. Appends a warning if the runtime bash is too old
# for the PreToolUse redirect hook to work.

set -uo pipefail

_PLUGIN_NAME="__PLUGIN_NAME__"
_PREFIX="__PREFIX__"

_intro="The \\`${_PLUGIN_NAME}\\` plugin is installed. It provides safety-constrained wrappers for __EXAMPLE_CLI_LIST__. Prefer these wrappers over raw bash for commands they cover. Load the \\`${_PLUGIN_NAME}\\` skill for the full overview, or any \\`${_PREFIX}<group>\\` skill__EXAMPLE_SKILL_HINT__ for specific tools. A pre-bash redirect hook will prompt you to use a wrapper when one is available."

_msg="$_intro"
if [[ "${BASH_VERSINFO[0]:-0}" -lt 4 ]]; then
  _msg="${_msg}"$'\\n\\n'"Warning: the pre-bash redirect hook is disabled because this system's bash is too old (found ${BASH_VERSION:-unknown}; bash 4+ required). Tell the user to install a newer bash (\\`brew install bash\\` on macOS, or via the system package manager on Linux) to enable it. Generated wrapper scripts may also fail until bash is upgraded."
fi

# Emit JSON via jq when available; otherwise fall back to a static notice
# that at least tells someone how to fix things.
if command -v jq >/dev/null 2>&1; then
  jq -nc --arg m "$_msg" \\
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $m}}'
else
  printf '%s\\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"nerftools: jq is required for the redirect and SessionStart hooks but is not installed. Tell the user to install jq."}}'
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
    return (
        _SESSION_START_TEMPLATE
        .replace("__PLUGIN_NAME__", _bash_double_quote_escape(plugin_meta.name))
        .replace("__PREFIX__", _bash_double_quote_escape(prefix))
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
