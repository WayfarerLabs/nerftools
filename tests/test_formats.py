"""Tests for output format builders (v1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nerftools.config import Author, MarketplaceMetadata, PluginMetadata
from nerftools.formats import build_claude_plugin, build_codex_plugin
from nerftools.manifest import (
    ArgSpec,
    NerfManifest,
    OptionSpec,
    PackageMeta,
    PassthroughSpec,
    TemplateSpec,
    ThreatLevel,
    ThreatSpec,
    ToolSpec,
)

_THREAT_NONE = ThreatSpec(read=ThreatLevel.NONE, write=ThreatLevel.NONE)


def _manifest(
    name: str = "test-pkg",
    skill_group: str = "test-pkg",
    tools: dict[str, ToolSpec] | None = None,
) -> NerfManifest:
    return NerfManifest(
        version=1,
        package=PackageMeta(
            name=name,
            description="Test package",
            skill_group=skill_group,
            skill_intro="",
        ),
        tools=tools or {},
    )


def _template_tool(command: list[str], **kwargs: object) -> ToolSpec:
    return ToolSpec(
        description="A test tool.",
        threat=_THREAT_NONE,
        template=TemplateSpec(command=tuple(command)),
        **kwargs,
    )


def _plugin_meta(name: str = "test-plugin") -> PluginMetadata:
    return PluginMetadata(
        name=name,
        version="0.0.1",
        description="Test plugin",
    )


def _build(manifests: list[NerfManifest], out: Path, **kwargs: object) -> None:
    build_claude_plugin(manifests, out, kwargs.pop("plugin_meta", _plugin_meta()), **kwargs)  # type: ignore[arg-type]


# -- claude-plugin format ------------------------------------------------------


def test_claude_plugin_creates_plugin_json(tmp_path: Path) -> None:
    _build([_manifest()], tmp_path)
    plugin_json = tmp_path / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists()
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "test-plugin"
    assert data["version"] == "0.0.1"
    assert data["description"] == "Test plugin"
    assert data["skills"] == "./skills/"


def test_claude_plugin_plugin_json_includes_optional_fields(tmp_path: Path) -> None:
    plugin_meta = PluginMetadata(
        name="custom",
        version="1.2.3",
        description="Custom",
        author=Author(name="Someone", email="a@b.com"),
        homepage="https://example.com",
        repository="https://github.com/x/y",
        license="MIT",
        keywords=["foo", "bar"],
    )
    _build([_manifest()], tmp_path, plugin_meta=plugin_meta)
    data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
    assert data["author"] == {"name": "Someone", "email": "a@b.com"}
    assert data["homepage"] == "https://example.com"
    assert data["repository"] == "https://github.com/x/y"
    assert data["license"] == "MIT"
    assert data["keywords"] == ["foo", "bar"]


def test_claude_plugin_does_not_create_marketplace_json_by_default(tmp_path: Path) -> None:
    # marketplace.json is a marketplace-level file, not a plugin-level file
    _build([_manifest()], tmp_path)
    assert not (tmp_path / ".claude-plugin" / "marketplace.json").exists()


def test_claude_plugin_embeds_marketplace_when_meta_provided(tmp_path: Path) -> None:
    marketplace_meta = MarketplaceMetadata(
        name="standalone",
        description="Standalone marketplace",
        owner=Author(name="Org"),
    )
    _build([_manifest()], tmp_path, marketplace_meta=marketplace_meta)
    mp = tmp_path / ".claude-plugin" / "marketplace.json"
    assert mp.exists()
    data = json.loads(mp.read_text())
    assert data["name"] == "standalone"
    assert data["owner"]["name"] == "Org"
    assert data["plugins"][0]["name"] == "test-plugin"  # from plugin_meta
    assert data["plugins"][0]["source"] == "./"


def test_claude_plugin_creates_skills_with_scripts(tmp_path: Path) -> None:
    tools = {"git-add": _template_tool(
        ["git", "add", "{{arguments.files}}"],
        arguments={"files": ArgSpec(description="files", variadic=True)},
    )}
    _build([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")

    skill_md = tmp_path / "skills" / "nerf-git" / "SKILL.md"
    assert skill_md.exists()

    script = tmp_path / "skills" / "nerf-git" / "scripts" / "nerf-git-add"
    assert script.exists()
    assert script.stat().st_mode & 0o111  # executable


def test_claude_plugin_skill_uses_plugin_root(tmp_path: Path) -> None:
    tools = {"git-log": _template_tool(["git", "log"])}
    _build([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")

    content = (tmp_path / "skills" / "nerf-git" / "SKILL.md").read_text()
    assert "${CLAUDE_PLUGIN_ROOT}" in content
    assert "nerf-git/scripts/nerf-git-log" in content


def test_claude_plugin_overview_skill_named_after_plugin(tmp_path: Path) -> None:
    tools = {"git-log": _template_tool(["git", "log"])}
    _build(
        [_manifest(skill_group="git", tools=tools)],
        tmp_path,
        prefix="nerf-",
        plugin_meta=_plugin_meta("my-plugin"),
    )

    overview = tmp_path / "skills" / "my-plugin" / "SKILL.md"
    assert overview.exists()
    content = overview.read_text()
    assert "# my-plugin" in content
    assert "nerf-git" in content


def test_claude_plugin_nerfctl_scripts(tmp_path: Path) -> None:
    _build([_manifest()], tmp_path)

    scripts_dir = tmp_path / "scripts"
    assert scripts_dir.exists()
    assert (scripts_dir / "nerfctl-grant-allow").exists()
    assert (scripts_dir / "nerfctl-grant-deny").exists()
    assert (scripts_dir / "nerfctl-grant-reset").exists()
    assert (scripts_dir / "nerfctl-grant-by-threat").exists()
    assert (scripts_dir / "nerfctl-grant-list").exists()
    assert not (scripts_dir / "nerfctl-install-plugin").exists()


def test_claude_plugin_nerfctl_skills(tmp_path: Path) -> None:
    _build([_manifest()], tmp_path)

    for name in (
        "nerfctl-grant-allow", "nerfctl-grant-deny", "nerfctl-grant-reset",
        "nerfctl-grant-by-threat", "nerfctl-grant-list",
    ):
        skill_md = tmp_path / "skills" / name / "SKILL.md"
        assert skill_md.exists(), f"missing {name}/SKILL.md"
        content = skill_md.read_text()
        assert "disable-model-invocation: true" in content
        assert "${CLAUDE_PLUGIN_ROOT}" in content


def test_claude_plugin_cleans_output_by_default(tmp_path: Path) -> None:
    stale = tmp_path / "old-stuff"
    stale.mkdir()
    (stale / "file.txt").write_text("stale")
    _build([_manifest()], tmp_path)
    assert not stale.exists()


def test_claude_plugin_maps_to_line(tmp_path: Path) -> None:
    tools = {"git-push": _template_tool(["git", "push", "{{arguments.remote}}", "HEAD"])}
    _build([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")

    content = (tmp_path / "skills" / "nerf-git" / "SKILL.md").read_text()
    assert "**Maps to:** `git push <remote> HEAD`" in content


def test_claude_plugin_threat_metadata_in_script(tmp_path: Path) -> None:
    tool = ToolSpec(
        description="Git log",
        threat=ThreatSpec(read=ThreatLevel.WORKSPACE, write=ThreatLevel.NONE),
        template=TemplateSpec(command=("git", "log")),
    )
    _build([_manifest(skill_group="git", tools={"git-log": tool})], tmp_path, prefix="nerf-")

    script_content = (tmp_path / "skills" / "nerf-git" / "scripts" / "nerf-git-log").read_text()
    assert "# nerf:threat:read=workspace" in script_content
    assert "# nerf:threat:write=none" in script_content


def test_claude_plugin_skill_renders_option_default(tmp_path: Path) -> None:
    """Defaults declared on options must surface in the shipped Claude plugin SKILL.md."""
    options = {"remote": OptionSpec(flag="--remote", description="Remote.", default="origin")}
    tools = {"git-x": _template_tool(["echo", "{{options.remote}}"], options=options)}
    _build([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")

    content = (tmp_path / "skills" / "nerf-git" / "SKILL.md").read_text()
    assert "default `origin`" in content


def test_claude_plugin_passthrough_skill(tmp_path: Path) -> None:
    tool = ToolSpec(
        description="Safe find",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="find", deny=("-exec",), prefix=(".",)),
    )
    _build([_manifest(skill_group="find", tools={"safe-find": tool})], tmp_path, prefix="nerf-")

    content = (tmp_path / "skills" / "nerf-find" / "SKILL.md").read_text()
    assert "**Denied patterns:**" in content
    assert '**Maps to:** `find . "$@"`' in content
    assert "[tokens...]" in content


# -- claude-plugin hint hook ---------------------------------------------------


def _manifest_with_hints(
    *,
    skill_group: str = "git",
    hints: tuple[str, ...] = ("^git( |$)",),
) -> NerfManifest:
    return NerfManifest(
        version=1,
        package=PackageMeta(
            name=skill_group,
            description="Test package",
            skill_group=skill_group,
            bash_hints=hints,
        ),
        tools={"x": _template_tool(["echo", "x"])},
    )


def _run_hook(script: Path, payload: dict) -> tuple[str, int]:
    import subprocess

    result = subprocess.run(
        [str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout, result.returncode


def test_claude_plugin_no_pretool_hook_when_no_bash_hints(tmp_path: Path) -> None:
    _build([_manifest(skill_group="git")], tmp_path, prefix="nerf-")
    cfg = json.loads((tmp_path / "hooks" / "hooks.json").read_text())
    assert "PreToolUse" not in cfg["hooks"]
    assert not (tmp_path / "hooks" / "nerf-bash-hint").exists()


def test_claude_plugin_session_start_opt_out(tmp_path: Path) -> None:
    _build(
        [_manifest_with_hints()],
        tmp_path,
        prefix="nerf-",
        emit_session_start_hook=False,
    )
    cfg = json.loads((tmp_path / "hooks" / "hooks.json").read_text())
    assert "SessionStart" not in cfg["hooks"]
    assert "PreToolUse" in cfg["hooks"]
    assert not (tmp_path / "hooks" / "nerf-session-start").exists()
    assert (tmp_path / "hooks" / "nerf-bash-hint").exists()


def test_claude_plugin_pretool_opt_out(tmp_path: Path) -> None:
    _build(
        [_manifest_with_hints()],
        tmp_path,
        prefix="nerf-",
        emit_pretool_bash_hint_hook=False,
    )
    cfg = json.loads((tmp_path / "hooks" / "hooks.json").read_text())
    assert "SessionStart" in cfg["hooks"]
    assert "PreToolUse" not in cfg["hooks"]
    assert not (tmp_path / "hooks" / "nerf-bash-hint").exists()
    assert (tmp_path / "hooks" / "nerf-session-start").exists()


def test_claude_plugin_both_hooks_off_no_hooks_dir(tmp_path: Path) -> None:
    _build(
        [_manifest_with_hints()],
        tmp_path,
        prefix="nerf-",
        emit_session_start_hook=False,
        emit_pretool_bash_hint_hook=False,
    )
    assert not (tmp_path / "hooks").exists()


def test_claude_plugin_session_start_always_emitted(tmp_path: Path) -> None:
    _build([_manifest(skill_group="git")], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-session-start"
    assert script.exists() and script.stat().st_mode & 0o111
    cfg = json.loads((tmp_path / "hooks" / "hooks.json").read_text())
    ss = cfg["hooks"]["SessionStart"][0]
    assert ss["matcher"] == "startup|resume|clear|compact"
    assert ss["hooks"][0]["command"].endswith("/hooks/nerf-session-start")


def test_session_start_emits_intro(tmp_path: Path) -> None:
    _build(
        [
            _manifest(skill_group="git"),
            _manifest(name="gh-pkg", skill_group="gh"),
            _manifest(name="tf-pkg", skill_group="tf"),
        ],
        tmp_path,
        prefix="nerf-",
    )
    script = tmp_path / "hooks" / "nerf-session-start"
    import subprocess

    result = subprocess.run([str(script)], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "SessionStart"
    ctx = out["additionalContext"]
    assert "`test-plugin`" in ctx
    assert "`nerf-<group>`" in ctx
    # CLI examples are derived from the actual bundled manifests.
    assert "wrappers for git, gh, tf" in ctx


def test_session_start_dedupes_cli_families(tmp_path: Path) -> None:
    _build(
        [
            _manifest(name="az-aks", skill_group="az-aks"),
            _manifest(name="az-account", skill_group="az-account"),
            _manifest(name="az-boards", skill_group="az-boards"),
        ],
        tmp_path,
        prefix="nerf-",
    )
    import subprocess

    result = subprocess.run(
        [str(tmp_path / "hooks" / "nerf-session-start")],
        capture_output=True,
        text=True,
        check=True,
    )
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    # Three az-* packages collapse to a single "az" family in the example list.
    assert "wrappers for az." in ctx or "wrappers for az," in ctx


def test_session_start_truncates_long_family_list(tmp_path: Path) -> None:
    _build(
        [_manifest(name=f"p{i}", skill_group=f"cli{i}") for i in range(8)],
        tmp_path,
        prefix="nerf-",
    )
    import subprocess

    result = subprocess.run(
        [str(tmp_path / "hooks" / "nerf-session-start")],
        capture_output=True,
        text=True,
        check=True,
    )
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "and more" in ctx


def test_session_start_uses_plugin_name_and_prefix(tmp_path: Path) -> None:
    _build(
        [_manifest(skill_group="git")],
        tmp_path,
        plugin_meta=PluginMetadata(name="mytools", version="0.0.1", description="x"),
        prefix="mytool-",
    )
    script = tmp_path / "hooks" / "nerf-session-start"
    import subprocess

    result = subprocess.run([str(script)], capture_output=True, text=True, check=True)
    ctx = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "`mytools`" in ctx
    assert "`mytool-<group>`" in ctx
    assert "`mytool-git`" in ctx


def test_claude_plugin_hook_config_emitted(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    cfg = tmp_path / "hooks" / "hooks.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    pre = data["hooks"]["PreToolUse"][0]
    assert pre["matcher"] == "Bash"
    cmd = pre["hooks"][0]["command"]
    assert cmd.endswith("/hooks/nerf-bash-hint")
    assert "${CLAUDE_PLUGIN_ROOT}" in cmd


def test_claude_plugin_hook_script_executable(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    assert script.exists()
    assert script.stat().st_mode & 0o111  # executable


def test_hook_denies_matching_command(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, rc = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    )
    assert rc == 0
    payload = json.loads(stdout)
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    assert "`nerf-git`" in out["permissionDecisionReason"]
    assert "# nerf:bypass <one-line explanation>" in out["permissionDecisionReason"]


def test_hook_lists_all_matching_skills(tmp_path: Path) -> None:
    m1 = _manifest_with_hints(skill_group="git", hints=("\\bgit\\b",))
    m2 = _manifest_with_hints(skill_group="tf", hints=("\\bterraform\\b",))
    _build([m1, m2], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, rc = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status && terraform plan"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-git`" in reason
    assert "`nerf-tf`" in reason


def test_hook_dedupes_skills_with_multiple_patterns(tmp_path: Path) -> None:
    m = _manifest_with_hints(skill_group="git", hints=("^git( |$)", "^gh( |$)"))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert reason.count("`nerf-git`") == 1


def test_hook_allows_unmatched_command(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, rc = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
    )
    assert rc == 0
    assert stdout == ""


def test_hook_skips_nerf_wrapper_calls(tmp_path: Path) -> None:
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, rc = _run_hook(
        script,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": "/plugin/skills/nerf-git/scripts/nerf-git-add ."
            },
        },
    )
    assert rc == 0
    assert stdout == ""


def test_hook_skips_wrapper_calls_after_shell_prefix(tmp_path: Path) -> None:
    """Wrapper invocations preceded by `cd` or env-var assignments are still skipped."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"

    # cd && wrapper
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "cd /repo && nerf-git status"}},
    )
    assert stdout == ""

    # env-var assignment + wrapper
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "env FOO=bar nerf-git pull"}},
    )
    assert stdout == ""


def test_hook_portable_word_boundary_translation(tmp_path: Path) -> None:
    """Manifest patterns may use \\b; the generated hook ships portable ERE."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script_text = (tmp_path / "hooks" / "nerf-bash-hint").read_text()
    # The GNU \b extension must not appear in the rendered script.
    assert "\\bgit\\b" not in script_text
    # The portable alternation must.
    assert "(^|$|[^[:alnum:]_])git(^|$|[^[:alnum:]_])" in script_text


def test_hook_brand_regex_meta_safe(tmp_path: Path) -> None:
    """A prefix with regex metacharacters doesn't break the sentinel match."""
    _build(
        [_manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))],
        tmp_path,
        prefix="my.tool-",
    )
    script = tmp_path / "hooks" / "nerf-bash-hint"
    # Sentinel uses the literal brand 'my.tool', so 'myXtool:bypass' must NOT match.
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # myXtool:bypass reason"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`my.tool-git`" in reason
    # The literal brand sentinel DOES bypass.
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # my.tool:bypass reason"}},
    )
    assert stdout == ""


def test_hook_allows_non_bash_tool(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, rc = _run_hook(
        script, {"tool_name": "Edit", "tool_input": {"file_path": "/x"}}
    )
    assert rc == 0
    assert stdout == ""


def test_hook_bypass_with_reason_allows(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, rc = _run_hook(
        script,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git log -p  # nerf:bypass need raw diff output"},
        },
    )
    assert rc == 0
    assert stdout == ""


def test_hook_bypass_empty_reason_denies(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # nerf:bypass"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "requires a reason" in reason


def test_hook_brand_follows_prefix(tmp_path: Path) -> None:
    _build(
        [_manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))],
        tmp_path,
        prefix="mytool-",
    )
    script = tmp_path / "hooks" / "nerf-bash-hint"
    # Bypass with the brand-derived sentinel allows
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # mytool:bypass yes"}},
    )
    assert stdout == ""
    # Bypass with the old "nerf:" brand does NOT match -> still denies
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # nerf:bypass yes"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`mytool-git`" in reason
    assert "# mytool:bypass" in reason


def test_hook_bypass_whitespace_only_reason_denies(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-bash-hint"
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # nerf:bypass   "}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "requires a reason" in reason


# -- codex-plugin format -------------------------------------------------------


def _build_codex(manifests: list[NerfManifest], out: Path, **kwargs: object) -> None:
    build_codex_plugin(manifests, out, kwargs.pop("plugin_meta", _plugin_meta()), **kwargs)  # type: ignore[arg-type]


def test_codex_plugin_creates_plugin_json(tmp_path: Path) -> None:
    _build_codex([_manifest()], tmp_path)
    plugin_json = tmp_path / ".codex-plugin" / "plugin.json"
    assert plugin_json.exists()
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "test-plugin"
    assert data["version"] == "0.0.1"
    assert data["description"] == "Test plugin"
    assert data["skills"] == "./skills/"


def test_codex_plugin_creates_skills_with_scripts(tmp_path: Path) -> None:
    tools = {"git-add": _template_tool(
        ["git", "add", "{{arguments.files}}"],
        arguments={"files": ArgSpec(description="files", variadic=True)},
    )}
    _build_codex([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")

    skill_md = tmp_path / "skills" / "nerf-git" / "SKILL.md"
    assert skill_md.exists()

    script = tmp_path / "skills" / "nerf-git" / "scripts" / "nerf-git-add"
    assert script.exists()
    assert script.stat().st_mode & 0o111  # executable


def test_codex_plugin_skill_uses_relative_paths(tmp_path: Path) -> None:
    tools = {"git-log": _template_tool(["git", "log"])}
    _build_codex([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")

    content = (tmp_path / "skills" / "nerf-git" / "SKILL.md").read_text()
    assert "${CLAUDE_PLUGIN_ROOT}" not in content
    assert "scripts/nerf-git-log" in content


def test_codex_plugin_overview_skill(tmp_path: Path) -> None:
    tools = {"git-log": _template_tool(["git", "log"])}
    _build_codex(
        [_manifest(skill_group="git", tools=tools)],
        tmp_path,
        prefix="nerf-",
        plugin_meta=_plugin_meta("my-plugin"),
    )

    overview = tmp_path / "skills" / "my-plugin" / "SKILL.md"
    assert overview.exists()
    content = overview.read_text()
    assert "# my-plugin" in content
    assert "nerf-git" in content


def test_codex_plugin_no_nerfctl(tmp_path: Path) -> None:
    _build_codex([_manifest()], tmp_path)

    # No top-level scripts/ dir
    assert not (tmp_path / "scripts").exists()
    # No nerfctl skill directories
    for name in (
        "nerfctl-grant-allow", "nerfctl-grant-deny", "nerfctl-grant-reset",
        "nerfctl-grant-by-threat", "nerfctl-grant-list",
    ):
        assert not (tmp_path / "skills" / name).exists()


def test_codex_plugin_no_marketplace_json(tmp_path: Path) -> None:
    _build_codex([_manifest()], tmp_path)
    assert not (tmp_path / ".codex-plugin" / "marketplace.json").exists()


def test_codex_plugin_cleans_output(tmp_path: Path) -> None:
    stale = tmp_path / "old-stuff"
    stale.mkdir()
    (stale / "file.txt").write_text("stale")
    _build_codex([_manifest()], tmp_path)
    assert not stale.exists()


def test_codex_plugin_rejects_symlink_in_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "do-not-delete.txt"
    marker.write_text("keep")

    (output_dir / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        _build_codex([_manifest()], output_dir)

    assert marker.exists()


def test_codex_plugin_maps_to_line(tmp_path: Path) -> None:
    tools = {"git-push": _template_tool(["git", "push", "{{arguments.remote}}", "HEAD"])}
    _build_codex([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")

    content = (tmp_path / "skills" / "nerf-git" / "SKILL.md").read_text()
    assert "**Maps to:** `git push <remote> HEAD`" in content


def test_codex_plugin_threat_metadata_in_script(tmp_path: Path) -> None:
    tool = ToolSpec(
        description="Git log",
        threat=ThreatSpec(read=ThreatLevel.WORKSPACE, write=ThreatLevel.NONE),
        template=TemplateSpec(command=("git", "log")),
    )
    _build_codex([_manifest(skill_group="git", tools={"git-log": tool})], tmp_path, prefix="nerf-")

    script_content = (tmp_path / "skills" / "nerf-git" / "scripts" / "nerf-git-log").read_text()
    assert "# nerf:threat:read=workspace" in script_content
    assert "# nerf:threat:write=none" in script_content
