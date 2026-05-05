"""Tests for shell script generation (v1)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from nerftools.builder import build_script_text, build_scripts
from nerftools.manifest import (
    ArgSpec,
    GuardSpec,
    NerfManifest,
    OptionSpec,
    PackageMeta,
    PassthroughSpec,
    PathTest,
    SwitchSpec,
    TemplateSpec,
    ThreatLevel,
    ThreatSpec,
    ToolSpec,
)

_THREAT_NONE = ThreatSpec(read=ThreatLevel.NONE, write=ThreatLevel.NONE)
_THREAT_WS = ThreatSpec(read=ThreatLevel.WORKSPACE, write=ThreatLevel.WORKSPACE)


def _option(
    flag: str,
    description: str = "A param",
    *,
    required: bool = True,
    pattern: str | None = None,
    allow: tuple[str, ...] = (),
    deny: tuple[str, ...] = (),
) -> OptionSpec:
    return OptionSpec(
        flag=flag, description=description, required=required,
        pattern=pattern, allow=allow, deny=deny,
    )


def _arg(
    description: str = "A param",
    *,
    required: bool = False,
    variadic: bool = False,
    pattern: str | None = None,
    allow: tuple[str, ...] = (),
    deny: tuple[str, ...] = (),
) -> ArgSpec:
    return ArgSpec(
        description=description, required=required, variadic=variadic,
        pattern=pattern, allow=allow, deny=deny,
    )


def _template_tool(
    command: list[str],
    switches: dict[str, SwitchSpec] | None = None,
    options: dict[str, OptionSpec] | None = None,
    arguments: dict[str, ArgSpec] | None = None,
    env: dict[str, str] | None = None,
    description: str = "A test tool.",
    guards: tuple[GuardSpec, ...] = (),
    pre: str | None = None,
    npm_pkgrun: bool = False,
) -> ToolSpec:
    return ToolSpec(
        description=description,
        threat=_THREAT_NONE,
        template=TemplateSpec(command=tuple(command), npm_pkgrun=npm_pkgrun),
        switches=switches or {},
        options=options or {},
        arguments=arguments or {},
        env=env or {},
        guards=guards,
        pre=pre,
    )


# -- Script structure ----------------------------------------------------------


def test_simple_tool_has_shebang() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hello"]))
    assert script.startswith("#!/usr/bin/env bash\n")


def test_simple_tool_has_set_pipefail() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hello"]))
    assert "set -euo pipefail" in script


def test_simple_tool_exec_line() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hello"]))
    assert "exec echo hello" in script


def test_simple_tool_has_dry_run_support() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hello"]))
    assert "--nerf-dry-run)" in script
    assert "dry-run:" in script


def test_generated_header_comment() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hello"]))
    assert "# my-tool -- A test tool" in script
    assert "# Generated from my-pkg manifest." in script


def test_threat_metadata_in_header() -> None:
    tool = ToolSpec(
        description="A test tool.",
        threat=ThreatSpec(read=ThreatLevel.WORKSPACE, write=ThreatLevel.REMOTE),
        template=TemplateSpec(command=("echo",)),
    )
    script = build_script_text("t", "p", tool)
    assert "# nerf:threat:read=workspace" in script
    assert "# nerf:threat:write=remote" in script


# -- Options (formerly flags) -------------------------------------------------


def test_option_in_case_statement() -> None:
    options = {"remote": _option("--remote")}
    script = build_script_text("t", "p", _template_tool(["git", "push", "{{options.remote}}"], options=options))
    assert "--remote)" in script
    assert 'REMOTE="$2"' in script


def test_option_with_short_in_case() -> None:
    options = {"remote": OptionSpec(flag="--remote", description="Remote", short="-r", required=True)}
    script = build_script_text("t", "p", _template_tool(["git", "push", "{{options.remote}}"], options=options))
    assert "--remote|-r)" in script
    assert 'REMOTE="$2"' in script


def test_option_with_short_in_usage() -> None:
    options = {"remote": OptionSpec(flag="--remote", description="Remote", short="-r", required=True)}
    script = build_script_text("t", "p", _template_tool(["git", "push", "{{options.remote}}"], options=options))
    assert "--remote|-r <remote>" in script


def test_option_exec_substitution() -> None:
    options = {"remote": _option("--remote")}
    script = build_script_text("t", "p", _template_tool(["git", "push", "{{options.remote}}", "HEAD"], options=options))
    assert 'exec git push "${REMOTE}" HEAD' in script


def test_required_option_validation() -> None:
    options = {"remote": _option("--remote")}
    script = build_script_text("t", "p", _template_tool(["echo", "{{options.remote}}"], options=options))
    assert "missing required option --remote" in script


def test_option_default_seeds_bash_variable() -> None:
    """An option with default should initialize its bash variable to the default,
    so inline placeholders see the value even when the agent doesn't pass --flag.
    """
    options = {"remote": OptionSpec(flag="--remote", description="Remote.", default="origin")}
    tool = _template_tool(["echo", "{{options.remote}}"], options=options)
    script = build_script_text("t", "p", tool)
    assert "REMOTE='origin'" in script
    assert 'REMOTE=""' not in script


def test_option_default_does_not_trigger_dup_check_on_first_use(tmp_path: Path) -> None:
    """Regression: when an option has a default, the bash variable is initialized
    non-empty, but the duplicate-detection check must still allow the user to
    pass --flag once. Uses a separate "_<VAR>_SET" marker.
    """
    options = {"remote": OptionSpec(flag="--remote", description="Remote.", default="origin")}
    tool = _template_tool(["echo", "{{options.remote}}"], options=options)
    script_path = tmp_path / "nerf-t"
    script_path.write_text(build_script_text("nerf-t", "p", tool))
    script_path.chmod(0o755)
    # First use of the flag with a non-default value must succeed
    result = subprocess.run(
        [str(script_path), "--nerf-dry-run", "--remote", "upstream"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "upstream" in result.stdout
    # But passing the flag twice must still be rejected
    result = subprocess.run(
        [str(script_path), "--remote", "a", "--remote", "b"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "can only be specified once" in result.stderr


def test_option_default_in_inline_placeholder(tmp_path: Path) -> None:
    """The default-feature is most useful in inline placeholders like
    "{{options.x}}/{{arguments.y}}" where the substituted ${X} must be non-empty
    for the URL/path to be well-formed. Whole-token placeholders happen to also
    work, but the inline path is the load-bearing case.
    """
    options = {"remote": OptionSpec(flag="--remote", description="Remote.", default="origin")}
    arguments = {"branch": ArgSpec(description="Branch.", required=True)}
    tool = _template_tool(
        ["echo", "{{options.remote}}/{{arguments.branch}}"],
        options=options,
        arguments=arguments,
    )
    script_path = tmp_path / "nerf-t"
    script_path.write_text(build_script_text("nerf-t", "p", tool))
    script_path.chmod(0o755)

    # Default applied when --remote omitted
    result = subprocess.run([str(script_path), "feat-x"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "origin/feat-x" in result.stdout

    # User override
    result = subprocess.run(
        [str(script_path), "--remote", "upstream", "feat-x"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "upstream/feat-x" in result.stdout


def test_option_default_with_special_chars_is_quoted(tmp_path: Path) -> None:
    """Defaults with shell-special characters must be safely single-quoted."""
    options = {"x": OptionSpec(flag="--x", description="X.", default="it's tricky")}
    tool = _template_tool(["echo", "{{options.x}}"], options=options)
    script = build_script_text("t", "p", tool)
    # Single-quote escaping uses '\"'\"' to embed a literal single quote
    assert "X='it'\"'\"'s tricky'" in script
    script_path = tmp_path / "nerf-t"
    script_path.write_text(script)
    script_path.chmod(0o755)
    result = subprocess.run([str(script_path), "--nerf-dry-run"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_optional_option_no_required_check() -> None:
    options = {"remote": _option("--remote", required=False)}
    script = build_script_text("t", "p", _template_tool(["echo", "{{options.remote}}"], options=options))
    assert "missing required option --remote" not in script


def test_optional_option_uses_conditional_expansion() -> None:
    options = {"remote": _option("--remote", required=False)}
    script = build_script_text("t", "p", _template_tool(["git", "fetch", "{{options.remote}}"], options=options))
    assert '${REMOTE:+"$REMOTE"}' in script


def test_pattern_validation() -> None:
    options = {"remote": _option("--remote", pattern="^[a-z]+$")}
    script = build_script_text("t", "p", _template_tool(["echo", "{{options.remote}}"], options=options))
    assert "^[a-z]+$" in script
    assert "does not match required pattern" in script


def test_deny_validation() -> None:
    options = {"remote": _option("--remote", deny=("origin", "main"))}
    script = build_script_text("t", "p", _template_tool(["echo", "{{options.remote}}"], options=options))
    assert '"${REMOTE}" == "origin"' in script
    assert '"${REMOTE}" == "main"' in script


def test_allow_validation() -> None:
    options = {"env": _option("--env", allow=("prod", "staging"))}
    script = build_script_text("t", "p", _template_tool(["echo", "{{options.env}}"], options=options))
    assert '"${ENV}" != "prod"' in script
    assert '"${ENV}" != "staging"' in script
    assert "not an allowed value" in script


def test_option_parser_break_when_positional_args_present() -> None:
    options = {"verbose": _option("--verbose", required=False)}
    arguments = {"target": _arg(required=True)}
    tool = _template_tool(
        ["cmd", "{{options.verbose}}", "{{arguments.target}}"], options=options, arguments=arguments,
    )
    script = build_script_text("t", "p", tool)
    assert "*) break ;;" in script


def test_option_parser_error_when_no_positional_args() -> None:
    options = {"remote": _option("--remote")}
    script = build_script_text("t", "p", _template_tool(["echo", "{{options.remote}}"], options=options))
    assert "unknown argument" in script
    assert "*) break ;;" not in script


# -- Switches (formerly boolean flags) ----------------------------------------


def test_switch_shift_one() -> None:
    switches = {"draft": SwitchSpec(flag="--draft", description="Draft")}
    tool = _template_tool(["gh", "pr", "create", "{{switches.draft}}"], switches=switches)
    script = build_script_text("t", "p", tool)
    assert 'DRAFT="true"; shift 1' in script


def test_switch_no_shift_two() -> None:
    switches = {"draft": SwitchSpec(flag="--draft", description="Draft")}
    tool = _template_tool(["gh", "pr", "create", "{{switches.draft}}"], switches=switches)
    script = build_script_text("t", "p", tool)
    assert "shift 2" not in script


def test_switch_expands_to_flag_string() -> None:
    switches = {"draft": SwitchSpec(flag="--draft", description="Draft")}
    tool = _template_tool(["gh", "pr", "create", "{{switches.draft}}"], switches=switches)
    script = build_script_text("t", "p", tool)
    assert '${DRAFT:+"--draft"}' in script


def test_switch_usage_shows_bracketed_flag() -> None:
    switches = {"draft": SwitchSpec(flag="--draft", description="Draft")}
    tool = _template_tool(["gh", "pr", "create", "{{switches.draft}}"], switches=switches)
    script = build_script_text("t", "p", tool)
    assert "[--draft]" in script


def test_switch_bash_syntax() -> None:
    switches = {"draft": SwitchSpec(flag="--draft", description="Draft")}
    tool = _template_tool(["gh", "pr", "create", "{{switches.draft}}"], switches=switches)
    script = build_script_text("t", "p", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


# -- Positional args -----------------------------------------------------------


def test_positional_arg_collected() -> None:
    arguments = {"remote": _arg(required=True)}
    script = build_script_text("t", "p", _template_tool(["git", "fetch", "{{arguments.remote}}"], arguments=arguments))
    assert 'REMOTE="${1:-}"' in script


def test_positional_exec_substitution() -> None:
    arguments = {"remote": _arg(required=True)}
    script = build_script_text("t", "p", _template_tool(["git", "fetch", "{{arguments.remote}}"], arguments=arguments))
    assert 'exec git fetch "${REMOTE}"' in script


def test_required_arg_validation() -> None:
    arguments = {"target": _arg(required=True)}
    script = build_script_text("t", "p", _template_tool(["cmd", "{{arguments.target}}"], arguments=arguments))
    assert "missing required argument <target>" in script


def test_optional_arg_no_required_check() -> None:
    arguments = {"target": _arg(required=False)}
    script = build_script_text("t", "p", _template_tool(["cmd", "{{arguments.target}}"], arguments=arguments))
    assert "missing required argument <target>" not in script


def test_variadic_arg_collected() -> None:
    arguments = {"files": _arg(variadic=True)}
    script = build_script_text("t", "p", _template_tool(["git", "add", "{{arguments.files}}"], arguments=arguments))
    assert 'FILES=("$@")' in script


def test_extra_positional_rejected_when_no_variadic(tmp_path: Path) -> None:
    """Trailing tokens past the declared positionals must error, not be silently dropped.

    Without this check, "tool <pos> --unknown-flag" silently drops --unknown-flag because
    the flag parser breaks at the first non-flag and the positional parser only takes $1.
    """
    arguments = {"target": _arg(required=True)}
    tool = _template_tool(["echo", "{{arguments.target}}"], arguments=arguments)
    script = build_script_text("nerf-test", "test", tool)
    script_path = tmp_path / "nerf-test"
    script_path.write_text(script)
    script_path.chmod(0o755)
    result = subprocess.run(
        [str(script_path), "value", "--unknown"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "unexpected extra arguments" in result.stderr
    assert "--unknown" in result.stderr


def test_no_extra_check_when_variadic(tmp_path: Path) -> None:
    """Tools with a variadic positional should accept any trailing tokens (variadic eats them)."""
    arguments = {"files": _arg(required=True, variadic=True)}
    tool = _template_tool(["echo", "{{arguments.files}}"], arguments=arguments)
    script = build_script_text("nerf-test", "test", tool)
    # The extra-args check must NOT be emitted for variadic tools.
    assert "unexpected extra arguments" not in script


def test_dry_run_preserves_quoting_for_values_with_spaces(tmp_path: Path) -> None:
    """Dry-run must shell-quote values so multi-word args don't look like multiple args."""
    arguments = {"target": _arg(required=True)}
    tool = _template_tool(["echo", "{{arguments.target}}"], arguments=arguments)
    script_path = tmp_path / "nerf-test"
    script_path.write_text(build_script_text("nerf-test", "test", tool))
    script_path.chmod(0o755)
    result = subprocess.run(
        [str(script_path), "--nerf-dry-run", "a b c"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # printf %q escapes spaces with backslash; the value is presented as one shell-quoted token.
    assert "a\\ b\\ c" in result.stdout
    # The naive "echo dry-run: ..." form would have shown plain "a b c".
    assert "a b c" not in result.stdout


def test_variadic_allow_flags_rejects_nerf_dry_run_inside_command(tmp_path: Path) -> None:
    """--nerf-dry-run inside a variadic+allow_flags arg must be rejected explicitly.

    The flag parser breaks at the first non-flag token, so wrapper flags placed AFTER
    positional args end up captured into the variadic and silently passed to the wrapped
    command. For --nerf-dry-run this means the dry-run gate is bypassed -- the real call
    runs without the agent realizing.
    """
    arguments = {"command": _arg(required=True, variadic=True)}
    # Build a tool with allow_flags=True via direct ArgSpec
    from nerftools.manifest import ArgSpec
    arguments = {"command": ArgSpec(description="", required=True, variadic=True, allow_flags=True)}
    tool = _template_tool(["echo", "{{arguments.command}}"], arguments=arguments)
    script_path = tmp_path / "nerf-runs"
    script_path.write_text(build_script_text("nerf-runs", "test", tool))
    script_path.chmod(0o755)
    # Dry-run AFTER positionals: caught
    result = subprocess.run(
        [str(script_path), "kubectl", "get", "pods", "--nerf-dry-run"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "no-op" in result.stderr
    assert "wrapper flag" in result.stderr


def test_variadic_allow_flags_check_does_not_fire_for_unrelated_flags(tmp_path: Path) -> None:
    """The check is targeted at --nerf-dry-run only; legitimate inner flags (--help, etc.)
    must pass through without false positives.
    """
    from nerftools.manifest import ArgSpec
    arguments = {"command": ArgSpec(description="", required=True, variadic=True, allow_flags=True)}
    tool = _template_tool(["echo", "{{arguments.command}}"], arguments=arguments)
    script_path = tmp_path / "nerf-runs2"
    script_path.write_text(build_script_text("nerf-runs2", "test", tool))
    script_path.chmod(0o755)
    result = subprocess.run(
        [str(script_path), "--nerf-dry-run", "kubectl", "--help"],
        capture_output=True, text=True,
    )
    # --help here is a token in the command, not a wrapper flag -- must pass.
    assert result.returncode == 0, result.stderr
    assert "kubectl" in result.stdout
    assert "--help" in result.stdout


def test_optional_option_value_with_spaces_passes_as_one_argv_element(tmp_path: Path) -> None:
    """The ${VAR:+"--flag"} ${VAR:+"$VAR"} substitution must preserve embedded spaces.

    This is a defensive regression test for the codegen pattern. If a future builder
    edit removes the inner double quotes (e.g. emits ${VAR:+--flag $VAR}), values with
    spaces would word-split into multiple argv elements, silently changing semantics
    for every tool with an optional option. The helper prints one argv element per
    line so word splitting would manifest as extra lines.
    """
    helper = tmp_path / "argv-dump"
    helper.write_text("#!/bin/bash\nprintf '%s\\n' \"$@\"\n")
    helper.chmod(0o755)

    options = {"label": _option("--label", required=False)}
    tool = _template_tool(
        [str(helper), "{{options.label}}"],
        options=options,
    )
    script_path = tmp_path / "nerf-argv"
    script_path.write_text(build_script_text("nerf-argv", "test", tool))
    script_path.chmod(0o755)
    result = subprocess.run(
        [str(script_path), "--label", "my multi word value"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    # Expect exactly two argv elements: "--label" and "my multi word value".
    assert lines == ["--label", "my multi word value"], (
        f"Optional option value lost shell quoting; got argv lines: {lines}"
    )


def test_variadic_arg_exec_substitution() -> None:
    arguments = {"files": _arg(required=True, variadic=True)}
    script = build_script_text("t", "p", _template_tool(["git", "add", "{{arguments.files}}"], arguments=arguments))
    assert '"${FILES[@]}"' in script


def test_optional_variadic_uses_conditional_expansion() -> None:
    arguments = {"files": _arg(variadic=True)}
    script = build_script_text("t", "p", _template_tool(["git", "add", "{{arguments.files}}"], arguments=arguments))
    assert '${FILES[@]+"${FILES[@]}"}' in script


# -- Flag injection prevention -------------------------------------------------


def test_positional_arg_rejects_flag_like_value() -> None:
    arguments = {"target": _arg(required=True)}
    script = build_script_text("t", "p", _template_tool(["cmd", "{{arguments.target}}"], arguments=arguments))
    assert '"${TARGET}" == -*' in script
    assert "cannot start with '-'" in script


def test_variadic_arg_rejects_flag_like_values() -> None:
    arguments = {"files": _arg(variadic=True)}
    script = build_script_text("t", "p", _template_tool(["git", "add", "{{arguments.files}}"], arguments=arguments))
    assert '"$_v" == -*' in script
    assert "cannot start with '-'" in script


# -- Env vars ------------------------------------------------------------------


def test_env_exports_before_exec() -> None:
    script = build_script_text(
        "t", "p",
        _template_tool(["az", "account", "show"], env={"AZURE_CONFIG_DIR": "/home/user/.azure"}),
    )
    lines = script.splitlines()
    export_idx = next(i for i, line in enumerate(lines) if "AZURE_CONFIG_DIR" in line)
    exec_idx = next(i for i, line in enumerate(lines) if line.startswith("exec "))
    assert export_idx < exec_idx
    assert "export AZURE_CONFIG_DIR='/home/user/.azure'" in script


# -- Guards --------------------------------------------------------------------


def test_guard_check_before_exec() -> None:
    guards = (GuardSpec(command=("git", "remote", "get-url", "{{arguments.remote}}"), fail_message="Remote not found"),)
    arguments = {"remote": _arg(required=True)}
    tool = _template_tool(
        ["git", "push", "{{arguments.remote}}", "HEAD"], arguments=arguments, guards=guards,
    )
    script = build_script_text("t", "p", tool)
    lines = script.splitlines()
    guard_idx = next(i for i, line in enumerate(lines) if "get-url" in line)
    exec_idx = next(i for i, line in enumerate(lines) if line.startswith("exec "))
    assert guard_idx < exec_idx
    assert "Remote not found" in script


def test_script_guard_check_before_exec() -> None:
    guards = (GuardSpec(script="! git diff --cached --quiet", fail_message="Nothing staged"),)
    script = build_script_text("t", "p", _template_tool(["git", "commit", "-m", "msg"], guards=guards))
    assert "Nothing staged" in script
    assert "|| {" in script


def test_script_guard_substitutes_placeholders() -> None:
    guards = (
        GuardSpec(
            script='! git rev-parse "refs/tags/{{arguments.tag}}" > /dev/null 2>&1',
            fail_message="Tag exists",
        ),
    )
    arguments = {"tag": _arg(required=True)}
    tool = _template_tool(
        ["git", "tag", "-a", "{{arguments.tag}}", "-m", "{{arguments.tag}}"],
        arguments=arguments,
        guards=guards,
    )
    script = build_script_text("t", "p", tool)
    assert "${TAG}" in script


# -- Pre-hooks -----------------------------------------------------------------


def test_pre_hook_generates_function() -> None:
    tool = _template_tool(["echo"], pre="echo setup")
    script = build_script_text("t", "p", tool)
    assert "_nerf_pre()" in script
    assert "echo setup" in script
    assert "_nerf_pre_rc" in script
    assert "pre-hook failed" in script


def test_pre_hook_before_exec() -> None:
    tool = _template_tool(["echo"], pre="echo setup")
    script = build_script_text("t", "p", tool)
    lines = script.splitlines()
    pre_idx = next(i for i, line in enumerate(lines) if "_nerf_pre()" in line)
    exec_idx = next(i for i, line in enumerate(lines) if line.startswith("exec "))
    assert pre_idx < exec_idx


def test_pre_hook_bash_syntax() -> None:
    tool = _template_tool(
        ["echo"],
        pre='BRANCH=$(git symbolic-ref --short HEAD)\nif [ -z "$BRANCH" ]; then\n  return 1\nfi',
    )
    script = build_script_text("t", "p", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


# -- Passthrough mode ----------------------------------------------------------


def test_passthrough_exec() -> None:
    tool = ToolSpec(
        description="Safe find",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="find", prefix=(".",)),
    )
    script = build_script_text("nerf-safe-find", "find", tool)
    assert "exec find '.' \"$@\"" in script


def test_passthrough_deny_scan() -> None:
    tool = ToolSpec(
        description="Safe find",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="find", deny=("-exec", "-delete"), prefix=(".",)),
    )
    script = build_script_text("nerf-safe-find", "find", tool)
    assert "_NERF_DENY_PATTERNS" in script
    assert "'-exec'" in script
    assert "'-delete'" in script
    assert "is not allowed" in script


def test_passthrough_suffix() -> None:
    tool = ToolSpec(
        description="Kubectl",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="kubectl", suffix=("--context=prod",)),
    )
    script = build_script_text("t", "p", tool)
    assert "exec kubectl \"$@\" '--context=prod'" in script


def test_passthrough_usage_shows_tokens() -> None:
    tool = ToolSpec(
        description="Safe find",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="find", deny=("-exec",), prefix=(".",)),
    )
    script = build_script_text("t", "p", tool)
    assert "[tokens...]" in script
    assert "Denied patterns:" in script


def test_passthrough_maps_to() -> None:
    tool = ToolSpec(
        description="Safe find",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="find", prefix=(".",)),
    )
    script = build_script_text("t", "p", tool)
    assert 'Maps to: find . "$@"' in script


def test_passthrough_bash_syntax() -> None:
    tool = ToolSpec(
        description="Safe find",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="find", deny=("-exec", "-ok*", "-delete"), prefix=(".",)),
    )
    script = build_script_text("nerf-safe-find", "find", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


# -- Script mode ---------------------------------------------------------------


def test_script_mode_includes_body() -> None:
    tool = ToolSpec(
        description="Deploy check",
        threat=_THREAT_NONE,
        script='echo "checking..."\nexit 0',
        arguments={"env": _arg(required=True, allow=("staging", "production"))},
    )
    script = build_script_text("t", "p", tool)
    assert 'echo "checking..."' in script
    assert "exit 0" in script


def test_script_mode_no_exec() -> None:
    tool = ToolSpec(
        description="Deploy check",
        threat=_THREAT_NONE,
        script='echo "done"',
    )
    script = build_script_text("t", "p", tool)
    assert "exec " not in script


def test_script_mode_no_maps_to() -> None:
    tool = ToolSpec(
        description="Deploy check",
        threat=_THREAT_NONE,
        script='echo "done"',
    )
    script = build_script_text("t", "p", tool)
    assert "Maps to:" not in script


def test_script_mode_bash_syntax() -> None:
    tool = ToolSpec(
        description="Check",
        threat=_THREAT_NONE,
        script='echo "checking ${ENVIRONMENT}"\nif [ "$DRY_RUN" = "true" ]; then\n  exit 0\nfi',
        arguments={"environment": _arg(required=True)},
        switches={"dry_run": SwitchSpec(flag="--dry-run", description="Dry run")},
    )
    script = build_script_text("t", "p", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


# -- Usage / help --------------------------------------------------------------


def test_usage_contains_tool_name() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hi"]))
    assert "Usage: my-tool" in script


def test_usage_contains_description() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hi"], description="Does the thing."))
    assert "Does the thing." in script


# -- Structured error messages -------------------------------------------------


def test_structured_error_has_tool_name() -> None:
    arguments = {"target": _arg(required=True)}
    script = build_script_text("nerf-deploy", "p", _template_tool(["cmd", "{{arguments.target}}"], arguments=arguments))
    assert "error: nerf-deploy:" in script


def test_structured_error_has_hint() -> None:
    arguments = {"target": _arg(required=True)}
    script = build_script_text("t", "p", _template_tool(["cmd", "{{arguments.target}}"], arguments=arguments))
    assert "hint:" in script


# -- Bash syntax validation ----------------------------------------------------


def test_generated_script_is_valid_bash() -> None:
    options = {"remote": _option("--remote", pattern="^[a-z]+$", deny=("origin",))}
    tool = _template_tool(
        ["git", "push", "{{options.remote}}", "HEAD"], options=options,
    )
    script = build_script_text("my-tool", "my-pkg", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


def test_simple_tool_bash_syntax() -> None:
    script = build_script_text("my-tool", "my-pkg", _template_tool(["echo", "hello"]))
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


def test_tool_with_options_and_args_bash_syntax() -> None:
    options = {"verbose": _option("--verbose", required=False)}
    arguments = {"target": _arg(required=True)}
    tool = _template_tool(
        ["cmd", "{{options.verbose}}", "{{arguments.target}}"], options=options, arguments=arguments,
    )
    script = build_script_text("my-tool", "my-pkg", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


def test_variadic_tool_bash_syntax() -> None:
    arguments = {"files": _arg(required=True, variadic=True)}
    tool = _template_tool(["git", "add", "{{arguments.files}}"], arguments=arguments)
    script = build_script_text("my-tool", "my-pkg", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


# -- keep_existing / clean behavior -------------------------------------------


def _simple_manifest(name: str = "test-pkg") -> NerfManifest:
    return NerfManifest(
        version=1,
        package=PackageMeta(name=name, description="Test.", skill_group=name, skill_intro=""),
        tools={"my-tool": _template_tool(["echo", "hello"])},
    )


def test_build_scripts_clears_stale_files_by_default(tmp_path: Path) -> None:
    stale = tmp_path / "stale-tool"
    stale.write_text("old")
    build_scripts([_simple_manifest()], tmp_path, prefix="")
    assert not stale.exists()


def test_build_scripts_keep_existing_preserves_unmanaged_files(tmp_path: Path) -> None:
    extra = tmp_path / "custom-tool"
    extra.write_text("custom")
    build_scripts([_simple_manifest()], tmp_path, keep_existing=True, prefix="")
    assert extra.exists()


def test_build_scripts_always_writes_generated_files(tmp_path: Path) -> None:
    build_scripts([_simple_manifest()], tmp_path, prefix="nerf-")
    assert (tmp_path / "nerf-my-tool").exists()


@pytest.mark.parametrize("keep", [True, False])
def test_build_scripts_overwrites_existing_generated_file(tmp_path: Path, keep: bool) -> None:
    (tmp_path / "nerf-my-tool").write_text("old content")
    build_scripts([_simple_manifest()], tmp_path, keep_existing=keep, prefix="nerf-")
    assert "old content" not in (tmp_path / "nerf-my-tool").read_text()


def test_build_scripts_prefix_applied_to_filename(tmp_path: Path) -> None:
    build_scripts([_simple_manifest()], tmp_path, prefix="gwat-")
    assert (tmp_path / "gwat-my-tool").exists()


def test_build_scripts_prefix_in_script_header(tmp_path: Path) -> None:
    build_scripts([_simple_manifest()], tmp_path, prefix="nerf-")
    content = (tmp_path / "nerf-my-tool").read_text()
    assert "# nerf-my-tool" in content


# -- npm_pkgrun ----------------------------------------------------------------


def test_npm_pkgrun_includes_resolver() -> None:
    tool = _template_tool(
        ["cspell@8.19.4", "{{arguments.args}}"],
        arguments={"args": _arg(required=True, variadic=True)},
        npm_pkgrun=True,
    )
    script = build_script_text("pkgrun-cspell", "pkgrun", tool)
    assert "_PKGRUN" in script
    assert "bunx" in script
    assert 'exec "$_PKGRUN" cspell@8.19.4' in script


def test_non_pkgrun_has_no_resolver() -> None:
    tool = _template_tool(["git", "add", "{{arguments.files}}"], arguments={"files": _arg(variadic=True)})
    script = build_script_text("git-add", "test", tool)
    assert "_PKGRUN" not in script


# -- Path tests ----------------------------------------------------------------


def _path_option_tool(
    tests: tuple[PathTest, ...],
    *,
    required: bool = False,
) -> ToolSpec:
    options = {
        "dir": OptionSpec(
            flag="-C", description="Directory", required=required, path_tests=tests,
        ),
    }
    return _template_tool(["echo", "{{options.dir}}"], options=options)


def _path_arg_tool(
    tests: tuple[PathTest, ...],
    *,
    required: bool = True,
    variadic: bool = False,
) -> ToolSpec:
    arguments = {
        "target": ArgSpec(
            description="Target", required=required, variadic=variadic,
            path_tests=tests,
        ),
    }
    return _template_tool(["echo", "{{arguments.target}}"], arguments=arguments)


def test_no_path_tests_no_helper() -> None:
    script = build_script_text("t", "p", _template_tool(["echo", "hello"]))
    assert "_nerf_check_path" not in script


def test_path_tests_emit_helper() -> None:
    script = build_script_text("t", "p", _path_option_tool((PathTest.UNDER_CWD,)))
    assert "_nerf_check_path()" in script
    assert "realpath -m" in script


def test_path_tests_helper_emitted_once_per_tool() -> None:
    options = {
        "dir": OptionSpec(
            flag="-C", description="d", required=False,
            path_tests=(PathTest.UNDER_CWD, PathTest.DIR),
        ),
    }
    arguments = {
        "target": ArgSpec(
            description="t", required=True,
            path_tests=(PathTest.UNDER_CWD, PathTest.EXISTS),
        ),
    }
    tool = _template_tool(
        ["echo", "{{options.dir}}", "{{arguments.target}}"],
        options=options, arguments=arguments,
    )
    script = build_script_text("t", "p", tool)
    assert script.count("_nerf_check_path() {") == 1


def test_path_tests_option_invocation() -> None:
    script = build_script_text("t", "p", _path_option_tool((PathTest.UNDER_CWD, PathTest.DIR)))
    assert "_nerf_check_path 'option -C' \"${DIR}\" 'under_cwd,dir'" in script
    # Optional option is gated on non-empty:
    assert 'if [[ -n "${DIR}" ]]; then' in script


def test_path_tests_required_argument_invocation() -> None:
    script = build_script_text("t", "p", _path_arg_tool((PathTest.UNDER_CWD, PathTest.EXISTS)))
    assert "_nerf_check_path 'argument <target>' \"${TARGET}\" 'under_cwd,exists'" in script


def test_path_tests_variadic_argument_loops() -> None:
    script = build_script_text("t", "p", _path_arg_tool((PathTest.UNDER_CWD,), variadic=True))
    assert 'for _v in "${TARGET[@]}"; do' in script
    assert "_nerf_check_path 'argument <target>' \"$_v\" 'under_cwd'" in script


def test_path_tests_generated_bash_is_valid() -> None:
    options = {
        "dir": OptionSpec(
            flag="-C", description="d", required=False,
            path_tests=(PathTest.UNDER_CWD, PathTest.DIR),
        ),
    }
    arguments = {
        "target": ArgSpec(
            description="t", required=True,
            path_tests=(PathTest.UNDER_CWD, PathTest.EXISTS),
        ),
    }
    tool = _template_tool(
        ["echo", "{{options.dir}}", "{{arguments.target}}"],
        options=options, arguments=arguments,
    )
    script = build_script_text("t", "p", tool)
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


def _write_and_run(
    tmp_path: Path, tool: ToolSpec, args: list[str], *, cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    script_path = tmp_path / "nerf-test"
    script_path.write_text(build_script_text("nerf-test", "test", tool))
    script_path.chmod(0o755)
    return subprocess.run(
        [str(script_path), *args],
        capture_output=True, text=True,
        cwd=str(cwd or tmp_path),
    )


def test_under_cwd_rejects_outside_path(tmp_path: Path) -> None:
    tool = _path_arg_tool((PathTest.UNDER_CWD,))
    result = _write_and_run(tmp_path, tool, ["/etc/hosts"])
    assert result.returncode != 0
    assert "'under_cwd' failed" in result.stderr


def test_under_cwd_accepts_relative_inside(tmp_path: Path) -> None:
    (tmp_path / "subdir").mkdir()
    tool = _path_arg_tool((PathTest.UNDER_CWD,))
    result = _write_and_run(tmp_path, tool, ["--nerf-dry-run", "subdir"])
    assert result.returncode == 0, result.stderr


def test_under_cwd_accepts_absolute_inside(tmp_path: Path) -> None:
    (tmp_path / "subdir").mkdir()
    tool = _path_arg_tool((PathTest.UNDER_CWD,))
    result = _write_and_run(tmp_path, tool, ["--nerf-dry-run", str(tmp_path / "subdir")])
    assert result.returncode == 0, result.stderr


def test_under_cwd_root_cwd_accepts_any_absolute_path(tmp_path: Path) -> None:
    """Regression: when cwd is "/", the naive prefix check would build "//" and
    reject every valid absolute path. The codegen short-circuits the prefix check
    in that case because every absolute path is trivially under root.
    """
    tool = _path_arg_tool((PathTest.UNDER_CWD,))
    # Run from "/" instead of tmp_path. Use --nerf-dry-run so no actual exec is needed.
    result = _write_and_run(tmp_path, tool, ["--nerf-dry-run", "/etc"], cwd=Path("/"))
    assert result.returncode == 0, result.stderr


def test_exists_rejects_missing(tmp_path: Path) -> None:
    tool = _path_arg_tool((PathTest.EXISTS,))
    result = _write_and_run(tmp_path, tool, ["does-not-exist"])
    assert result.returncode != 0
    assert "'exists' failed" in result.stderr


def test_not_exists_rejects_present(tmp_path: Path) -> None:
    (tmp_path / "already-here").touch()
    tool = _path_arg_tool((PathTest.NOT_EXISTS,))
    result = _write_and_run(tmp_path, tool, ["already-here"])
    assert result.returncode != 0
    assert "'not_exists' failed" in result.stderr


def test_file_rejects_dir(tmp_path: Path) -> None:
    (tmp_path / "subdir").mkdir()
    tool = _path_arg_tool((PathTest.FILE,))
    result = _write_and_run(tmp_path, tool, ["subdir"])
    assert result.returncode != 0
    assert "'file' failed" in result.stderr


def test_dir_rejects_file(tmp_path: Path) -> None:
    (tmp_path / "afile").touch()
    tool = _path_arg_tool((PathTest.DIR,))
    result = _write_and_run(tmp_path, tool, ["afile"])
    assert result.returncode != 0
    assert "'dir' failed" in result.stderr


def test_symlink_resolves_outside_cwd_rejected(tmp_path: Path) -> None:
    """A symlink whose target is outside cwd should fail under_cwd."""
    link = tmp_path / "outlink"
    link.symlink_to("/etc")
    tool = _path_arg_tool((PathTest.UNDER_CWD,))
    result = _write_and_run(tmp_path, tool, ["outlink"])
    assert result.returncode != 0
    assert "'under_cwd' failed" in result.stderr


def test_control_character_rejected(tmp_path: Path) -> None:
    tool = _path_arg_tool((PathTest.UNDER_CWD,))
    result = _write_and_run(tmp_path, tool, ["bad\nname"])
    assert result.returncode != 0
    assert "illegal control character" in result.stderr


def test_optional_option_path_test_skipped_when_unset(tmp_path: Path) -> None:
    tool = _path_option_tool((PathTest.UNDER_CWD, PathTest.DIR), required=False)
    # No -C provided -- option is unset, helper should not run, dry-run succeeds.
    # Tool also has no required positionals so this should reach the dry-run.
    result = _write_and_run(tmp_path, tool, ["--nerf-dry-run"])
    assert result.returncode == 0, result.stderr
