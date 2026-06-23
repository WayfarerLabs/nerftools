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
    PathTest,
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
    # Overview reminds the agent about the feedback channel.
    assert "nerf-report" in content


def test_claude_plugin_per_package_skill_has_nerf_report_footer(tmp_path: Path) -> None:
    tools = {"git-log": _template_tool(["git", "log"])}
    _build([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")
    skill = tmp_path / "skills" / "nerf-git" / "SKILL.md"
    assert "nerf-report" in skill.read_text()


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
    (tmp_path / ".nerf-build-manifest").write_text("claude-plugin\n")
    stale = tmp_path / "old-stuff"
    stale.mkdir()
    (stale / "file.txt").write_text("stale")
    _build([_manifest()], tmp_path)
    assert not stale.exists()


def test_claude_plugin_keep_existing_preserves_unmanaged_content(tmp_path: Path) -> None:
    keep_me = tmp_path / "unrelated"
    keep_me.mkdir()
    (keep_me / "file.txt").write_text("important")
    _build([_manifest()], tmp_path, keep_existing=True)
    assert (keep_me / "file.txt").read_text() == "important"
    # Unmanaged dir + keep_existing -> no marker written.
    assert not (tmp_path / ".nerf-build-manifest").exists()


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


# -- requires preflight --------------------------------------------------------


def test_requires_empty_emits_no_check(tmp_path: Path) -> None:
    tools = {"t": _template_tool(["echo", "hi"])}
    _build([_manifest(skill_group="t", tools=tools)], tmp_path, prefix="nerf-")
    script_text = (tmp_path / "skills" / "nerf-t" / "scripts" / "nerf-t").read_text()
    assert "for _bin in" not in script_text
    assert "command -v" not in script_text


def test_requires_template_emits_check(tmp_path: Path) -> None:
    tools = {
        "t": _template_tool(
            ["kubectl", "version"], requires=("kubectl",)
        )
    }
    _build([_manifest(skill_group="t", tools=tools)], tmp_path, prefix="nerf-")
    script_text = (tmp_path / "skills" / "nerf-t" / "scripts" / "nerf-t").read_text()
    assert "for _bin in kubectl; do" in script_text
    assert 'if ! command -v -- "$_bin" >/dev/null 2>&1; then' in script_text
    assert (
        "error: nerf-t: required command '$_bin' is not installed or not on PATH"
        in script_text
    )
    assert "exit 127" in script_text


def test_requires_multi_binary_emits_loop(tmp_path: Path) -> None:
    tools = {
        "t": _template_tool(
            ["kubectl", "version"], requires=("kubectl", "jq")
        )
    }
    _build([_manifest(skill_group="t", tools=tools)], tmp_path, prefix="nerf-")
    script_text = (tmp_path / "skills" / "nerf-t" / "scripts" / "nerf-t").read_text()
    assert "for _bin in kubectl jq; do" in script_text


def test_requires_passthrough_emits_check(tmp_path: Path) -> None:
    tool = ToolSpec(
        description="Safe find.",
        threat=_THREAT_NONE,
        passthrough=PassthroughSpec(command="find", prefix=(".",)),
        requires=("find",),
    )
    _build([_manifest(skill_group="find", tools={"safe-find": tool})], tmp_path, prefix="nerf-")
    script_text = (
        tmp_path / "skills" / "nerf-find" / "scripts" / "nerf-safe-find"
    ).read_text()
    assert "for _bin in find; do" in script_text


def test_requires_script_emits_check(tmp_path: Path) -> None:
    tool = ToolSpec(
        description="A script-mode tool.",
        threat=_THREAT_NONE,
        script="exec terraform plan",
        requires=("terraform",),
    )
    _build([_manifest(skill_group="tf", tools={"tf-plan": tool})], tmp_path, prefix="nerf-")
    script_text = (
        tmp_path / "skills" / "nerf-tf" / "scripts" / "nerf-tf-plan"
    ).read_text()
    assert "for _bin in terraform; do" in script_text


def test_requires_missing_binary_exits_127(tmp_path: Path) -> None:
    """End-to-end: a wrapper whose required binary isn't on PATH should
    exit 127 with a helpful stderr message before doing any real work."""
    import subprocess

    tools = {
        "t": _template_tool(
            ["definitely-not-a-real-binary-xyz123"],
            requires=("definitely-not-a-real-binary-xyz123",),
        )
    }
    _build([_manifest(skill_group="t", tools=tools)], tmp_path, prefix="nerf-")
    script = tmp_path / "skills" / "nerf-t" / "scripts" / "nerf-t"
    # PATH must include /usr/bin and /bin so the script's `#!/usr/bin/env bash`
    # shebang resolves; the absent binary is the wrapper's `requires` target.
    result = subprocess.run(
        [str(script)],
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 127
    assert "required command" in result.stderr
    assert "definitely-not-a-real-binary-xyz123" in result.stderr


def test_requires_check_passes_when_binary_present(tmp_path: Path) -> None:
    """When the required binary IS on PATH, the wrapper runs through."""
    import subprocess

    tools = {"t": _template_tool(["true"], requires=("true",))}
    _build([_manifest(skill_group="t", tools=tools)], tmp_path, prefix="nerf-")
    script = tmp_path / "skills" / "nerf-t" / "scripts" / "nerf-t"
    result = subprocess.run([str(script)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_requires_check_runs_even_under_dry_run(tmp_path: Path) -> None:
    """Dry-run is a preview of what WOULD happen. If the binary isn't there
    the real run would fail at exec, so the preview should fail the same
    way -- requires check fires regardless of --nerf-dry-run."""
    import subprocess

    tools = {
        "t": _template_tool(
            ["definitely-not-a-real-binary-xyz123"],
            requires=("definitely-not-a-real-binary-xyz123",),
        )
    }
    _build([_manifest(skill_group="t", tools=tools)], tmp_path, prefix="nerf-")
    script = tmp_path / "skills" / "nerf-t" / "scripts" / "nerf-t"
    result = subprocess.run(
        [str(script), "--nerf-dry-run"],
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 127
    assert "required command" in result.stderr


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


def _run_hook(
    script: Path,
    payload: dict,
    *,
    env: dict[str, str] | None = None,
    brand: str = "nerf",
) -> tuple[str, int]:
    import os
    import subprocess

    from nerftools.formats import _derive_brand_env_var

    # The hook is opt-in via <BRAND>_ENABLE_BASH_HINT_HOOK -- default the
    # brand to "nerf" (matches all existing tests' prefix="nerf-") and
    # default the gate to truthy so the tests exercise the hook's logic.
    # Tests of the gate itself pass an explicit env that overrides.
    # Use the production helper directly so test/hook env-var derivation
    # can't drift (e.g., on digit-leading brands).
    enable_var = _derive_brand_env_var(brand)
    merged_env = {**os.environ, enable_var: "true"}
    if env is not None:
        merged_env.update(env)
    result = subprocess.run(
        [str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=merged_env,
        check=False,
    )
    return result.stdout, result.returncode


def test_claude_plugin_no_pretool_hook_when_no_bash_hints(tmp_path: Path) -> None:
    _build([_manifest(skill_group="git")], tmp_path, prefix="nerf-")
    cfg = json.loads((tmp_path / "hooks" / "hooks.json").read_text())
    assert "PreToolUse" not in cfg["hooks"]
    assert not (tmp_path / "hooks" / "nerf-pre-tool-use").exists()


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
    assert (tmp_path / "hooks" / "nerf-pre-tool-use").exists()


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
    assert not (tmp_path / "hooks" / "nerf-pre-tool-use").exists()
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
    assert cmd.endswith("/hooks/nerf-pre-tool-use")
    assert "${CLAUDE_PLUGIN_ROOT}" in cmd


def test_claude_plugin_hook_script_executable(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    assert script.exists()
    assert script.stat().st_mode & 0o111  # executable


@pytest.mark.parametrize("enable_value", ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"])
def test_hook_runs_when_enable_env_is_truthy(tmp_path: Path, enable_value: str) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, rc = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status"}},
        env={"NERF_ENABLE_BASH_HINT_HOOK": enable_value},
    )
    assert rc == 0
    assert json.loads(stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "enable_value", ["", "false", "0", "no", "off", "FaLsE", "anything-else"]
)
def test_hook_silent_noop_when_enable_env_is_not_truthy(tmp_path: Path, enable_value: str) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, rc = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status"}},
        env={"NERF_ENABLE_BASH_HINT_HOOK": enable_value},
    )
    assert rc == 0
    assert stdout == ""  # nothing printed -> Claude Code lets the command through


def test_hook_silent_noop_when_enable_env_is_unset(tmp_path: Path) -> None:
    """Explicit guard against accidentally clobbering os.environ: pass an env
    dict that omits NERF_ENABLE_BASH_HINT_HOOK to confirm the unset case."""
    import os
    import subprocess

    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    env = {k: v for k, v in os.environ.items() if k != "NERF_ENABLE_BASH_HINT_HOOK"}
    result = subprocess.run(
        [str(script)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}}),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_env_var_is_brand_namespaced(tmp_path: Path) -> None:
    """A non-default brand gets its own env var so multiple plugins coexist."""
    _build([_manifest_with_hints()], tmp_path, prefix="acme-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    script_text = script.read_text()
    assert "ACME_ENABLE_BASH_HINT_HOOK" in script_text
    assert "NERF_ENABLE_BASH_HINT_HOOK" not in script_text


def test_hook_with_hyphenated_brand_uppercases_and_underscores(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="my-tool-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    assert "MY_TOOL_ENABLE_BASH_HINT_HOOK" in script.read_text()


def test_hook_denies_matching_command(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, rc = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    )
    assert rc == 0
    payload = json.loads(stdout)
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    reason = out["permissionDecisionReason"]
    assert "`nerf-git`" in reason
    assert "# nerf:bypass-bash-hint <report-filename>" in reason
    # Bypass message now points the agent at nerf-report to record the reason.
    assert "nerf-report" in reason


def test_hook_lists_all_matching_skills(tmp_path: Path) -> None:
    m1 = _manifest_with_hints(skill_group="git", hints=("\\bgit\\b",))
    m2 = _manifest_with_hints(skill_group="tf", hints=("\\bterraform\\b",))
    _build([m1, m2], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
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
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert reason.count("`nerf-git`") == 1


def test_hook_allows_unmatched_command(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, rc = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
    )
    assert rc == 0
    assert stdout == ""


def test_hook_skips_nerf_wrapper_calls(tmp_path: Path) -> None:
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
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
    """Wrapper invocations preceded by `cd` or bash env-var prefixes are still skipped."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"

    # cd && wrapper
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "cd /repo && nerf-git status"}},
    )
    assert stdout == ""

    # bash env-var prefix + wrapper
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "FOO=bar nerf-git pull"}},
    )
    assert stdout == ""

    # absolute path to the wrapper
    stdout, _ = _run_hook(
        script,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "/abs/path/skills/nerf-git/scripts/nerf-git-add ."},
        },
    )
    assert stdout == ""


@pytest.mark.parametrize(
    "command",
    [
        # timeout with numeric duration
        "timeout 30 nerf-git status",
        # timeout with unit-suffix duration
        "timeout 5s nerf-git status",
        # timeout with --foreground flag
        "timeout --foreground 30 nerf-git status",
        # timeout with -s SIGKILL (short flag with non-numeric value)
        "timeout -s SIGKILL 30 nerf-git status",
        # nice with no arg
        "nice nerf-git status",
        # nice with -n N
        "nice -n 10 nerf-git status",
        # nice with signed numeric (historical `nice -10` form)
        "nice -10 nerf-git status",
        # nice with POSIX end-of-options sentinel
        "nice -- nerf-git status",
        # time
        "time nerf-git status",
        # env (explicit `env` literal) -- also exercises the existing VAR=val path
        "env FOO=bar nerf-git status",
        # env with -u (unset variable, alpha value)
        "env -u PATH nerf-git status",
        # ionice with -c N
        "ionice -c 2 -n 7 nerf-git status",
        # ionice with alpha class value
        "ionice -c idle nerf-git status",
        # nested runners
        "nice timeout 30 nerf-git status",
        # absolute-path runner with absolute-path wrapper
        "/usr/bin/timeout 30 /abs/path/skills/nerf-git/scripts/nerf-git-status",
    ],
)
def test_hook_peeks_through_known_runners_to_wrapper(
    tmp_path: Path, command: str
) -> None:
    """The hook should recognize that the actual command after a known
    runner is a wrapper invocation, and skip the redirect. The detection
    is intentionally lenient -- when the leading token is a known runner,
    any wrapper-prefixed basename later in the segment is treated as a
    wrapper call, regardless of whether the intervening tokens look like
    runner args or something else."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": command}}
    )
    assert stdout == "", f"expected skip, got: {stdout}"


def test_hook_does_not_peek_through_sudo(tmp_path: Path) -> None:
    """sudo is not in the runner allowlist -- `sudo nerf-foo` is unusual
    enough that we'd rather the agent acknowledge it via the bypass
    sentinel. Hook should fire (redirect)."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "sudo nerf-git status"}},
    )
    # Sudo isn't in the runner allowlist; the redirect fires for `sudo` as
    # the apparent command, but it doesn't match the wrapper prefix so the
    # hint hook continues into pattern matching. `nerf-git status` contains
    # `git`, which matches the bash_hint pattern -> deny.
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-git`" in reason


def test_hook_runner_without_command_does_not_skip(tmp_path: Path) -> None:
    """A runner whose target is a raw binary (no wrapper-prefixed basename
    anywhere in the segment) should NOT trigger the wrapper-skip; the
    hook falls through to pattern matching."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    # `timeout 30 git status` -- runner is `timeout`, scan finds no
    # `nerf-*` basename in the remaining tokens, falls through to
    # pattern matching. `git` matches the hint -> deny.
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "timeout 30 git status"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-git`" in reason


@pytest.mark.parametrize(
    "command",
    [
        # Runner followed by raw command with a wrapper-prefixed decoy token.
        "timeout 30 git status nerf-foo",
        # Runner with non-wrapper exec target but a wrapper-prefixed value
        # to one of the runner's options.
        "env -u nerf-V git status",
        # Wrapper-prefixed basename appearing in a path arg to a raw command
        # invoked under a runner.
        "nice git -C /tmp/nerf-stuff status",
    ],
)
def test_hook_intentionally_skips_on_lenient_scan(
    tmp_path: Path, command: str
) -> None:
    """The runner-scan is lenient by design -- any wrapper-prefixed
    basename later in the segment short-circuits the nudge. This is
    intentional: the hook is a UX nudge, not a security boundary, so
    erring toward false negatives (missed nudges, command goes through
    normal permission gating) is cheaper than false positives (nudge
    fires on legitimate wrapper use). These cases pin that behavior so
    a future refactor knows the direction is deliberate."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": command}}
    )
    assert stdout == "", f"expected skip, got: {stdout}"


def test_hook_does_not_skip_on_arg_position_prefix(tmp_path: Path) -> None:
    """A token containing the prefix at arg position does NOT trigger the skip."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"

    # `nerf-tracker` is just an arg to git, not a wrapper invocation -> redirect fires.
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git log --grep nerf-tracker"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-git`" in reason


def test_hook_portable_word_boundary_translation(tmp_path: Path) -> None:
    """Manifest patterns may use \\b; the generated hook ships portable ERE."""
    m = _manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))
    _build([m], tmp_path, prefix="nerf-")
    script_text = (tmp_path / "hooks" / "nerf-pre-tool-use").read_text()
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
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    # Sentinel uses the literal brand 'my.tool', so 'myXtool:bypass' must NOT match.
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # myXtool:bypass-bash-hint reason"}},
        brand="my.tool",
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`my.tool-git`" in reason
    # The literal brand sentinel DOES bypass.
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # my.tool:bypass-bash-hint reason"}},
        brand="my.tool",
    )
    assert stdout == ""


def test_hook_allows_non_bash_tool(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, rc = _run_hook(
        script, {"tool_name": "Edit", "tool_input": {"file_path": "/x"}}
    )
    assert rc == 0
    assert stdout == ""


def test_hook_bypass_with_reason_allows(tmp_path: Path) -> None:
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, rc = _run_hook(
        script,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git log -p  # nerf:bypass-bash-hint need raw diff output"},
        },
    )
    assert rc == 0
    assert stdout == ""


def test_hook_malformed_bypass_falls_through_to_redirect(tmp_path: Path) -> None:
    """A bypass marker missing its reason isn't recognized; redirect fires normally."""
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    # Marker with no following content: just falls through.
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # nerf:bypass-bash-hint"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-git`" in reason
    # The standard redirect message documents the proper bypass syntax.
    assert "# nerf:bypass-bash-hint <report-filename>" in reason


def test_hook_bypass_partial_word_does_not_trigger(tmp_path: Path) -> None:
    """`bypassed-test` shouldn't accidentally trigger the marker."""
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # nerf:bypassed-test"}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-git`" in reason


def test_hook_brand_follows_prefix(tmp_path: Path) -> None:
    _build(
        [_manifest_with_hints(skill_group="git", hints=(r"\bgit\b",))],
        tmp_path,
        prefix="mytool-",
    )
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    # Bypass with the brand-derived sentinel allows
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # mytool:bypass-bash-hint yes"}},
        brand="mytool",
    )
    assert stdout == ""
    # Bypass with the old "nerf:" brand does NOT match -> still denies
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # nerf:bypass-bash-hint yes"}},
        brand="mytool",
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`mytool-git`" in reason
    assert "# mytool:bypass-bash-hint" in reason


def test_hook_bypass_whitespace_only_reason_falls_through(tmp_path: Path) -> None:
    """Whitespace-only reason isn't a reason; marker is malformed; redirect fires."""
    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script,
        {"tool_name": "Bash", "tool_input": {"command": "git status  # nerf:bypass-bash-hint   "}},
    )
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-git`" in reason


# -- stdutils sed/awk line-range bash hints ----------------------------------
#
# The stdutils package's two bash_hints redirect agents from `sed -n 'N,Mp'`
# and `awk 'NR>=N && NR<=M'` idioms to nerf-print-range. These tests pin the
# regexes shipped in nerftools/default_manifests/stdutils.yaml.

_SED_RANGE_HINT = r"\bsed +(-n|--quiet) +['\"]?[0-9$,]+p\b"
_AWK_NR_HINT = r"\bawk\b.*\bNR *[<>=!]+ *[0-9]"


@pytest.mark.parametrize(
    "command",
    [
        "sed -n '1,2p' /etc/passwd",
        "sed -n '100,200p' file.txt",
        "sed -n 5p file",
        "sed -n '$p' file",
        "sed -n '1,$p' file",
        "sed  -n  '50,100p'  file",  # extra whitespace
        "cat /etc/passwd | sed -n '1,5p'",  # piped from another command
        "sed --quiet '1,2p' file",  # long-form -n
        "sed --quiet 5p file",
    ],
)
def test_sed_line_range_hint_matches(tmp_path: Path, command: str) -> None:
    m = _manifest_with_hints(skill_group="stdutils", hints=(_SED_RANGE_HINT,))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": command}}
    )
    assert stdout, f"expected hint redirect, got empty output for: {command}"
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-stdutils`" in reason


@pytest.mark.parametrize(
    "command",
    [
        "sed -n '/foo/p' file",  # regex-address print, not line-range
        "sed 's/x/y/g' file",  # substitution, no -n
        "sed -i 's/x/y/g' file",  # in-place edit
        "sed -e '1d' file",  # delete, not print
        "grep -n pattern file",  # unrelated tool
        "cat file",  # unrelated
        "command with sed in a comment",  # no -n
    ],
)
def test_sed_line_range_hint_no_false_positive(tmp_path: Path, command: str) -> None:
    m = _manifest_with_hints(skill_group="stdutils", hints=(_SED_RANGE_HINT,))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": command}}
    )
    assert stdout == "", f"unexpected hint redirect for: {command}"


@pytest.mark.parametrize(
    "command",
    [
        "awk 'NR>=1 && NR<=10' file",
        "awk 'NR==42' file",
        "awk 'NR <= 100' /var/log/syslog",
        "awk 'NR > 50 && NR < 100' file",
        "awk -F: 'NR == 1' /etc/passwd",
        "cat file | awk 'NR>=10'",  # piped
        "awk 'NR>5' file",  # single-char op, no spaces -- regression of #2
        "awk 'NR<100' file",
        "awk 'NR!=1' file",  # != operator
    ],
)
def test_awk_nr_hint_matches(tmp_path: Path, command: str) -> None:
    m = _manifest_with_hints(skill_group="stdutils", hints=(_AWK_NR_HINT,))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": command}}
    )
    assert stdout, f"expected hint redirect, got empty output for: {command}"
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "`nerf-stdutils`" in reason


@pytest.mark.parametrize(
    "command",
    [
        "awk '{print $1}' file",  # column extraction, no NR
        "awk -F: '{print $1}' /etc/passwd",  # column extraction with field separator
        "awk 'BEGIN { print \"hi\" }'",  # BEGIN block, no NR comparison
        "awk '/regex/' file",  # regex pattern, no NR
        "grep -n pattern file",  # unrelated tool
        "echo NR",  # NR literal in unrelated command
    ],
)
def test_awk_nr_hint_no_false_positive(tmp_path: Path, command: str) -> None:
    m = _manifest_with_hints(skill_group="stdutils", hints=(_AWK_NR_HINT,))
    _build([m], tmp_path, prefix="nerf-")
    script = tmp_path / "hooks" / "nerf-pre-tool-use"
    stdout, _ = _run_hook(
        script, {"tool_name": "Bash", "tool_input": {"command": command}}
    )
    assert stdout == "", f"unexpected hint redirect for: {command}"


# -- print-range tool integration --------------------------------------------


_PRINT_RANGE_SCRIPT = """\
if [[ -n "${_FILE_SET}" ]]; then
  exec awk "NR>=${START} && NR<=${END}; NR>${END} {exit}" <"${FILE}"
else
  exec awk "NR>=${START} && NR<=${END}; NR>${END} {exit}"
fi
"""


def _print_range_tool() -> ToolSpec:
    """Reconstruct the print-range ToolSpec to match stdutils.yaml. The
    integration tests build a small synthetic plugin with this and
    subprocess the rendered script.

    Script mode (not template) because the file is redirected via stdin
    rather than passed as awk argv — that sidesteps awk's var=val
    parsing for filenames containing `=`, and works portably across
    awk implementations (gawk's `--` end-of-options is not recognized
    by mawk or POSIX awk).
    """
    return ToolSpec(
        description="Print a line range from a file or stdin.",
        threat=ThreatSpec(read=ThreatLevel.MACHINE, write=ThreatLevel.NONE),
        script=_PRINT_RANGE_SCRIPT,
        requires=("awk",),
        arguments={
            "start": ArgSpec(description="First line", required=True, pattern="^[1-9][0-9]*$"),
            "end": ArgSpec(description="Last line", required=True, pattern="^[1-9][0-9]*$"),
            "file": ArgSpec(description="File to read", required=False),
        },
    )


def test_print_range_reads_from_file(tmp_path: Path) -> None:
    """File mode: passes the file as a positional to awk."""
    import subprocess

    # Sample file lives outside the build dir so _build's outdir guard
    # doesn't refuse to write into a non-empty tmp_path.
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sample = data_dir / "sample.txt"
    sample.write_text("\n".join(f"line{i}" for i in range(1, 11)) + "\n")

    build_dir = tmp_path / "plugin"
    tools = {"print-range": _print_range_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], build_dir, prefix="nerf-")
    script = build_dir / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range"
    result = subprocess.run(
        [str(script), "3", "5", str(sample)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "line3\nline4\nline5\n"


def test_print_range_reads_from_stdin(tmp_path: Path) -> None:
    """Stdin mode: omit the file arg, pipe content in. The _FILE_SET-gated
    expansion `${_FILE_SET:+"$FILE"}` drops the empty arg so awk reads stdin."""
    import subprocess

    tools = {"print-range": _print_range_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], tmp_path, prefix="nerf-")
    script = tmp_path / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range"
    result = subprocess.run(
        [str(script), "2", "3"],
        input="a\nb\nc\nd\ne\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "b\nc\n"


def test_print_range_rejects_non_positive_start(tmp_path: Path) -> None:
    """The ^[1-9][0-9]*$ pattern rejects 0 and other non-positive-int inputs.
    (Negative inputs like -1 are caught earlier by the dash-prefix guard.)"""
    import subprocess

    tools = {"print-range": _print_range_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], tmp_path, prefix="nerf-")
    script = tmp_path / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range"
    for bad_start in ("0", "1.5", "abc", "1;echo"):
        result = subprocess.run(
            [str(script), bad_start, "5"],
            input="",
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0, f"expected rejection of start={bad_start!r}"
        assert "does not match required pattern" in result.stderr


_PRINT_RANGE_CWD_SCRIPT = """\
exec awk "NR>=${START} && NR<=${END}; NR>${END} {exit}" <"${FILE}"
"""


def _print_range_cwd_tool() -> ToolSpec:
    """print-range-cwd: file required, under_cwd path_test, workspace threat.

    Script mode for the same reason as _print_range_tool: stdin
    redirection so awk doesn't mis-parse a filename like `foo=bar.txt`
    as a var=val assignment.
    """
    return ToolSpec(
        description="Print a line range from a workspace file.",
        threat=ThreatSpec(read=ThreatLevel.WORKSPACE, write=ThreatLevel.NONE),
        script=_PRINT_RANGE_CWD_SCRIPT,
        requires=("awk",),
        arguments={
            "start": ArgSpec(description="First line", required=True, pattern="^[1-9][0-9]*$"),
            "end": ArgSpec(description="Last line", required=True, pattern="^[1-9][0-9]*$"),
            "file": ArgSpec(
                description="File to read",
                required=True,
                path_tests=(PathTest.UNDER_CWD,),
            ),
        },
    )


def test_print_range_cwd_reads_workspace_file(tmp_path: Path) -> None:
    """File under cwd works."""
    import subprocess

    build_dir = tmp_path / "plugin"
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    sample = work_dir / "sample.txt"
    sample.write_text("\n".join(f"line{i}" for i in range(1, 11)) + "\n")

    tools = {"print-range-cwd": _print_range_cwd_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], build_dir, prefix="nerf-")
    script = build_dir / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range-cwd"
    # Run from work_dir so the file is under cwd.
    result = subprocess.run(
        [str(script), "3", "5", "sample.txt"],
        capture_output=True,
        text=True,
        check=False,
        cwd=work_dir,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "line3\nline4\nline5\n"


def test_print_range_cwd_rejects_outside_cwd(tmp_path: Path) -> None:
    """File outside cwd is rejected by the under_cwd path_test."""
    import subprocess

    build_dir = tmp_path / "plugin"
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    # Sample lives outside work_dir.
    outside = tmp_path / "outside.txt"
    outside.write_text("line1\nline2\n")

    tools = {"print-range-cwd": _print_range_cwd_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], build_dir, prefix="nerf-")
    script = build_dir / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range-cwd"
    result = subprocess.run(
        [str(script), "1", "2", str(outside)],
        capture_output=True,
        text=True,
        check=False,
        cwd=work_dir,
    )
    assert result.returncode != 0
    # Path-check error mentions the path or "not under" / "under cwd".
    assert "cwd" in result.stderr.lower() or "outside" in result.stderr.lower()


def test_print_range_handles_var_eq_val_filename(tmp_path: Path) -> None:
    """Awk parses bare args like `foo=bar.txt` as variable assignments unless
    `--` precedes them. Both tools must guard against this regression so a
    filename containing `=` actually gets read."""
    import subprocess

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    weird = data_dir / "foo=bar.txt"
    weird.write_text("line1\nline2\nline3\n")

    build_dir = tmp_path / "plugin"
    tools = {"print-range": _print_range_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], build_dir, prefix="nerf-")
    script = build_dir / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range"
    # If `--` weren't being injected, awk would parse `foo=bar.txt` as a
    # variable assignment, fall through to stdin, and (with closed stdin)
    # return empty output. With `--`, awk treats it as a filename.
    result = subprocess.run(
        [str(script), "2", "3", str(weird)],
        input="",
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "line2\nline3\n"


def test_print_range_cwd_handles_var_eq_val_filename(tmp_path: Path) -> None:
    """Same regression as test_print_range_handles_var_eq_val_filename
    but exercises print-range-cwd's template-mode `--` injection."""
    import subprocess

    build_dir = tmp_path / "plugin"
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    weird = work_dir / "foo=bar.txt"
    weird.write_text("line1\nline2\nline3\n")

    tools = {"print-range-cwd": _print_range_cwd_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], build_dir, prefix="nerf-")
    script = build_dir / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range-cwd"
    result = subprocess.run(
        [str(script), "1", "2", "foo=bar.txt"],
        capture_output=True,
        text=True,
        check=False,
        cwd=work_dir,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "line1\nline2\n"


def test_print_range_cwd_requires_file(tmp_path: Path) -> None:
    """Unlike print-range, file is required -- omitting it errors."""
    import subprocess

    build_dir = tmp_path / "plugin"
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    tools = {"print-range-cwd": _print_range_cwd_tool()}
    _build([_manifest(skill_group="stdutils", tools=tools)], build_dir, prefix="nerf-")
    script = build_dir / "skills" / "nerf-stdutils" / "scripts" / "nerf-print-range-cwd"
    result = subprocess.run(
        [str(script), "1", "5"],
        input="ignored\n",
        capture_output=True,
        text=True,
        check=False,
        cwd=work_dir,
    )
    assert result.returncode != 0
    assert "file" in result.stderr.lower()


# -- PreToolUse current-version check ---------------------------------------


def _versioned_build(tmp_path: Path, version: str, **kwargs: object) -> Path:
    """Build the plugin into tmp_path/<version>/ so the hook can self-derive
    the version (it walks up from its own path). Returns the version-rooted
    output dir."""
    out = tmp_path / version
    _build([_manifest_with_hints()], out, prefix="nerf-", **kwargs)
    return out


def _path_for_version(tmp_path: Path, version: str, tool: str = "nerf-git-add") -> str:
    """Construct a tool path the hook would see in the agent's command,
    under tmp_path/<version>/skills/<group>/scripts/<tool>."""
    return str(tmp_path / version / "skills" / "nerf-git" / "scripts" / tool)


def _run_pre_tool_use(
    script: Path,
    command: str,
    *,
    env: dict[str, str] | None = None,
    brand: str = "nerf",
) -> tuple[str, int]:
    """Like _run_hook but with version-check defaults instead of bash-hint."""
    import os
    import subprocess

    from nerftools.formats import _derive_brand_env_var

    enable_var = _derive_brand_env_var(brand, "CURRENT_VERSION_HOOK")
    merged_env = {**os.environ, enable_var: "true"}
    if env is not None:
        merged_env.update(env)
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        [str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=merged_env,
        check=False,
    )
    return result.stdout, result.returncode


def test_version_check_disabled_by_default(tmp_path: Path) -> None:
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    stale = _path_for_version(tmp_path, "v1.0.0")
    # No NERF_ENABLE_CURRENT_VERSION_HOOK set -> check skipped -> allow.
    import os
    import subprocess

    env = {k: v for k, v in os.environ.items() if k != "NERF_ENABLE_CURRENT_VERSION_HOOK"}
    result = subprocess.run(
        [str(hook)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": f"{stale} arg"}}),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_version_check_denies_older_call(tmp_path: Path) -> None:
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    stale = _path_for_version(tmp_path, "v1.0.0")
    stdout, rc = _run_pre_tool_use(hook, f"{stale} some-arg")
    assert rc == 0
    payload = json.loads(stdout)
    reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
    assert "older version" in reason
    assert "v1.0.0" in reason
    assert "v2.0.0" in reason
    assert "use the current version v2.0.0" in reason
    assert "nerf-report" in reason
    assert "Do not attempt to work around" in reason


def test_version_check_denies_newer_call(tmp_path: Path) -> None:
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    newer = _path_for_version(tmp_path, "v3.0.0")
    stdout, rc = _run_pre_tool_use(hook, f"{newer} some-arg")
    assert rc == 0
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "NEWER version" in reason
    assert "Stop immediately" in reason
    assert "Do not attempt to work around" in reason


def test_version_check_allows_current_version_call(tmp_path: Path) -> None:
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    current = _path_for_version(tmp_path, "v2.0.0")
    stdout, rc = _run_pre_tool_use(hook, f"{current} some-arg")
    assert rc == 0
    assert stdout == ""  # no deny


def test_version_check_ignores_non_brand_tools_in_same_tree(tmp_path: Path) -> None:
    """A path matching our plugin tree but a tool name without the brand
    prefix isn't ours -- don't deny."""
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    foreign = str(tmp_path / "v1.0.0" / "skills" / "nerf-git" / "scripts" / "other-tool")
    stdout, rc = _run_pre_tool_use(hook, f"{foreign} arg")
    assert rc == 0
    assert stdout == ""


def test_version_check_ignores_unrelated_paths(tmp_path: Path) -> None:
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    stdout, rc = _run_pre_tool_use(hook, "/some/random/path arg")
    assert rc == 0
    assert stdout == ""


def test_version_check_has_no_bypass_sentinel(tmp_path: Path) -> None:
    """The bash-hint bypass sentinel must NOT skip the version check."""
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    stale = _path_for_version(tmp_path, "v1.0.0")
    stdout, rc = _run_pre_tool_use(hook, f"{stale} arg  # nerf:bypass-bash-hint testing")
    assert rc == 0
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "older version" in reason


def test_version_check_env_var_is_brand_namespaced(tmp_path: Path) -> None:
    """A non-default brand gets its own version-check env var."""
    out = tmp_path / "v2.0.0"
    _build([_manifest_with_hints()], out, prefix="acme-")
    hook = out / "hooks" / "nerf-pre-tool-use"
    script_text = hook.read_text()
    assert "ACME_ENABLE_CURRENT_VERSION_HOOK" in script_text


def test_version_check_prefers_newer_over_older_when_both_present(tmp_path: Path) -> None:
    """If a single command has BOTH an older and a newer path, report the
    newer one -- it's the higher-signal condition (real config inconsistency
    rather than a stale-path cache miss)."""
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    older = _path_for_version(tmp_path, "v1.0.0")
    newer = _path_for_version(tmp_path, "v3.0.0")
    stdout, _ = _run_pre_tool_use(hook, f"{older} && {newer}")
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "NEWER version" in reason
    assert "v3.0.0" in reason
    # The older-message wording should NOT win.
    assert "older version" not in reason


def _build_with_broken_self_layout(tmp_path: Path) -> Path:
    """Build the plugin then delete the markers the self-derive walk looks
    for. The hook's `realpath`/dirname still resolve, but the
    `[[ -d skills && -d .claude-plugin ]]` validation fails, forcing the
    fallback path."""
    import shutil

    out = tmp_path / "scratch"
    _build([_manifest_with_hints()], out, prefix="nerf-")
    shutil.rmtree(out / "skills")
    shutil.rmtree(out / ".claude-plugin")
    return out


def test_version_check_skips_when_multiple_owners_share_plugin_name(tmp_path: Path) -> None:
    """If self-derive fails AND the cache contains the plugin under multiple
    owners (a misconfig the brand should prevent), warn and skip rather than
    arbitrarily picking one owner's max version."""
    import os
    import subprocess

    out = _build_with_broken_self_layout(tmp_path)
    hook = out / "hooks" / "nerf-pre-tool-use"

    # Stage two installs of the same plugin under different owners.
    home = tmp_path / "home"
    for owner in ("orgA", "orgB"):
        (home / ".claude" / "plugins" / "cache" / owner / "test-plugin" / "1.0.0").mkdir(
            parents=True
        )
    env = {
        **os.environ,
        "HOME": str(home),
        "NERF_ENABLE_CURRENT_VERSION_HOOK": "true",
    }
    result = subprocess.run(
        [str(hook)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo ok"}}),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""  # skipped, no deny
    assert "multiple owners" in result.stderr


def test_session_start_degraded_reminder_when_version_undetermined(tmp_path: Path) -> None:
    """If env is on but self-derive fails (e.g. unusual install layout),
    SessionStart should still warn the agent that enforcement is on."""
    import os
    import subprocess

    out = _build_with_broken_self_layout(tmp_path)
    hook = out / "hooks" / "nerf-session-start"
    env = {**os.environ, "NERF_ENABLE_CURRENT_VERSION_HOOK": "true"}
    result = subprocess.run([str(hook)], capture_output=True, text=True, env=env, check=False)
    assert result.returncode == 0
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "Current-version enforcement is enabled" in context
    assert "active version could not be determined" in context


def test_version_check_runs_before_bash_hint(tmp_path: Path) -> None:
    """When both checks would fire (impossible in practice since they're
    disjoint, but: belt-and-suspenders), version check should win."""
    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-pre-tool-use"
    stale = _path_for_version(tmp_path, "v1.0.0")
    # Command has BOTH a stale wrapper path AND a raw `git` command that
    # bash-hint would normally redirect. With version-check enabled and
    # firing first, we get the version deny message.
    import os
    import subprocess

    env = {
        **os.environ,
        "NERF_ENABLE_CURRENT_VERSION_HOOK": "true",
        "NERF_ENABLE_BASH_HINT_HOOK": "true",
    }
    payload = {"tool_name": "Bash", "tool_input": {"command": f"{stale} && git status"}}
    result = subprocess.run(
        [str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    reason = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "older version" in reason
    # Bash-hint message NOT included (version check short-circuits).
    assert "may wrap this command" not in reason


# -- SessionStart version reminder -------------------------------------------


def test_session_start_no_version_reminder_by_default(tmp_path: Path) -> None:
    import os
    import subprocess

    _build([_manifest_with_hints()], tmp_path, prefix="nerf-")
    hook = tmp_path / "hooks" / "nerf-session-start"
    env = {k: v for k, v in os.environ.items() if k != "NERF_ENABLE_CURRENT_VERSION_HOOK"}
    result = subprocess.run(
        [str(hook)], capture_output=True, text=True, env=env, check=False
    )
    assert result.returncode == 0
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "Current-version enforcement" not in context


def test_session_start_includes_version_reminder_when_env_set(tmp_path: Path) -> None:
    import subprocess

    out = _versioned_build(tmp_path, "v2.0.0")
    hook = out / "hooks" / "nerf-session-start"
    import os

    env = {**os.environ, "NERF_ENABLE_CURRENT_VERSION_HOOK": "true"}
    result = subprocess.run(
        [str(hook)], capture_output=True, text=True, env=env, check=False
    )
    assert result.returncode == 0
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "Current-version enforcement" in context
    assert "version v2.0.0" in context


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
    assert "nerf-report" in content


def test_codex_plugin_per_package_skill_has_nerf_report_footer(tmp_path: Path) -> None:
    tools = {"git-log": _template_tool(["git", "log"])}
    _build_codex([_manifest(skill_group="git", tools=tools)], tmp_path, prefix="nerf-")
    skill = tmp_path / "skills" / "nerf-git" / "SKILL.md"
    assert "nerf-report" in skill.read_text()


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
    (tmp_path / ".nerf-build-manifest").write_text("codex-plugin\n")
    stale = tmp_path / "old-stuff"
    stale.mkdir()
    (stale / "file.txt").write_text("stale")
    _build_codex([_manifest()], tmp_path)
    assert not stale.exists()


def test_codex_plugin_rejects_symlink_in_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / ".nerf-build-manifest").write_text("codex-plugin\n")

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
