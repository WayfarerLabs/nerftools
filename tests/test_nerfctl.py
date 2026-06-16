"""Tests for nerfctl shell scripts.

Each test runs the shell script as a subprocess and asserts on stdout, exit
code, and the resulting JSON state of the settings file.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_NERFCTL_DIR = Path(__file__).parent.parent / "nerftools" / "nerfctl" / "claude"
_GRANT = _NERFCTL_DIR / "grant-allow.sh"
_DENY = _NERFCTL_DIR / "grant-deny.sh"
_RESET = _NERFCTL_DIR / "grant-reset.sh"
_BY_THREAT = _NERFCTL_DIR / "grant-by-threat.sh"
_LIST = _NERFCTL_DIR / "grant-list.sh"


def _ensure_jq() -> str | None:
    """Ensure jq is available. Returns the bin directory containing jq, or None."""
    check = subprocess.run(
        ["bash", "-c", "type -P jq && echo '{}' | jq ."],
        capture_output=True,
        text=True,
    )
    if check.returncode == 0:
        jq_path = check.stdout.strip().splitlines()[0]
        if "mise" not in jq_path:
            return str(Path(jq_path).parent)
    mise_check = subprocess.run(["bash", "-c", "command -v mise"], capture_output=True)
    if mise_check.returncode != 0:
        return None
    subprocess.run(["mise", "install", "jq"], capture_output=True)
    where = subprocess.run(["mise", "where", "jq"], capture_output=True, text=True)
    if where.returncode != 0:
        return None
    return where.stdout.strip() + "/bin"


_jq_bin_dir = _ensure_jq()

pytestmark = pytest.mark.skipif(_jq_bin_dir is None, reason="jq not available")


def _run(
    script: Path,
    *args: str,
    home: Path | None = None,
    cwd: Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ}
    if home is not None and "PATH" in env:
        env["PATH"] = os.pathsep.join(p for p in env["PATH"].split(os.pathsep) if "mise/shims" not in p)
        if _jq_bin_dir:
            env["PATH"] = _jq_bin_dir + os.pathsep + env["PATH"]
    if home is not None:
        env["HOME"] = str(home)
    if env_extra:
        env.update(env_extra)
    # When isolating to a fake HOME, also default cwd to it so any
    # local-scope writes/reads can't leak into the developer's repo.
    if cwd is None and home is not None:
        cwd = home
    return subprocess.run(
        ["bash", "--norc", "--noprofile", str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _mock_plugin(tmp_path: Path, tools: list[str] | None = None) -> Path:
    """Create a mock plugin directory with tool scripts. Returns the plugin root."""
    plugin_root = tmp_path / "plugin"
    scripts_dir = plugin_root / "skills" / "nerf-test" / "scripts"
    scripts_dir.mkdir(parents=True)
    for tool in tools or ["nerf-test-tool"]:
        script = scripts_dir / tool
        script.write_text("#!/bin/bash\necho ok\n")
        script.chmod(0o755)
    return plugin_root


def _mock_plugin_with_threats(
    tmp_path: Path,
    tools: dict[str, tuple[str, str]],
) -> Path:
    """Create a mock plugin with threat metadata in scripts.

    tools: dict of tool_name -> (read_level, write_level)
    """
    plugin_root = tmp_path / "plugin"
    scripts_dir = plugin_root / "skills" / "nerf-test" / "scripts"
    scripts_dir.mkdir(parents=True)
    for tool_name, (read, write) in tools.items():
        script = scripts_dir / tool_name
        script.write_text(
            f"#!/bin/bash\n"
            f"# {tool_name} -- test tool\n"
            f"# nerf:threat:read={read}\n"
            f"# nerf:threat:write={write}\n"
            f"set -euo pipefail\n"
            f"echo ok\n"
        )
        script.chmod(0o755)
    return plugin_root


def _user_settings(tmp_path: Path, content: dict | None = None) -> Path:
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    f = claude_dir / "settings.json"
    f.write_text(json.dumps(content or {}))
    return f


def _read(path: Path) -> dict:  # type: ignore[type-arg]
    return json.loads(path.read_text())  # type: ignore[no-any-return]


# -- grant --------------------------------------------------------------------


def test_grant_adds_to_allow(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    result = _run(_GRANT, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode == 0
    data = _read(tmp_path / ".claude" / "settings.json")
    entries = data["permissions"]["allow"]
    assert any("nerf-test-tool" in e for e in entries)
    assert any(str(plugin) in e for e in entries)


def test_grant_glob_matches_multiple(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-a", "nerf-test-b", "nerf-test-c"])
    result = _run(_GRANT, "user", "nerf-test-*", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode == 0
    data = _read(tmp_path / ".claude" / "settings.json")
    assert len(data["permissions"]["allow"]) == 3


def test_grant_no_matches_fails(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    result = _run(_GRANT, "user", "nerf-nonexistent-*", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode != 0
    assert "no tools matching" in result.stderr


def test_grant_does_not_duplicate(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    _run(_GRANT, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    _run(_GRANT, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    data = _read(tmp_path / ".claude" / "settings.json")
    assert len(data["permissions"]["allow"]) == 1


def test_grant_removes_from_deny(tmp_path: Path) -> None:
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-test-tool")
    # Seed with stale (no :*) deny entry
    _user_settings(tmp_path, {"permissions": {"allow": [], "deny": [f"Bash({script_path})"]}})
    _run(_GRANT, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    data = _read(tmp_path / ".claude" / "settings.json")
    # New :* entry in allow, stale entry removed from deny
    assert f"Bash({script_path}:*)" in data["permissions"]["allow"]
    assert f"Bash({script_path})" not in data["permissions"]["allow"]
    assert f"Bash({script_path})" not in data["permissions"]["deny"]
    assert f"Bash({script_path}:*)" not in data["permissions"]["deny"]


def test_grant_requires_scope_and_pattern(tmp_path: Path) -> None:
    result = _run(_GRANT, home=tmp_path)
    assert result.returncode != 0
    assert "expected <scope> <pattern>" in result.stderr


def test_grant_rejects_bad_scope(tmp_path: Path) -> None:
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    result = _run(_GRANT, "bogus", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode != 0
    assert "must be 'user', 'project', or 'local'" in result.stderr


def test_grant_local_scope(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir(parents=True)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    result = _run(_GRANT, "local", "nerf-test-tool", "--plugin-root", str(plugin), cwd=tmp_path)
    assert result.returncode == 0
    assert (tmp_path / ".claude" / "settings.local.json").exists()


def test_grant_project_scope(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir(parents=True)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    result = _run(_GRANT, "project", "nerf-test-tool", "--plugin-root", str(plugin), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    # Project scope writes to .claude/settings.json (committed), not .local.json
    assert (tmp_path / ".claude" / "settings.json").exists()
    assert not (tmp_path / ".claude" / "settings.local.json").exists()


# -- deny ---------------------------------------------------------------------


def test_deny_adds_to_deny(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    result = _run(_DENY, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode == 0
    data = _read(tmp_path / ".claude" / "settings.json")
    assert any("nerf-test-tool" in e for e in data["permissions"]["deny"])


def test_deny_removes_from_allow(tmp_path: Path) -> None:
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-test-tool")
    # Seed with stale (no :*) allow entry
    _user_settings(tmp_path, {"permissions": {"allow": [f"Bash({script_path})"], "deny": []}})
    _run(_DENY, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    data = _read(tmp_path / ".claude" / "settings.json")
    # Stale entry removed from allow, new :* entry in deny
    assert f"Bash({script_path})" not in data["permissions"]["allow"]
    assert f"Bash({script_path}:*)" not in data["permissions"]["allow"]
    assert f"Bash({script_path}:*)" in data["permissions"]["deny"]


def test_deny_requires_scope_and_pattern(tmp_path: Path) -> None:
    result = _run(_DENY, home=tmp_path)
    assert result.returncode != 0
    assert "expected <scope> <pattern>" in result.stderr


# -- reset --------------------------------------------------------------------


def test_reset_removes_entries(tmp_path: Path) -> None:
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-test-tool")
    _user_settings(
        tmp_path,
        {
            "permissions": {
                "allow": [f"Bash({script_path})", "Bash(other-tool)"],
                "deny": [f"Bash({script_path})"],
            }
        },
    )
    result = _run(_RESET, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode == 0
    data = _read(tmp_path / ".claude" / "settings.json")
    assert f"Bash({script_path})" not in data["permissions"]["allow"]
    assert f"Bash({script_path})" not in data["permissions"]["deny"]
    assert "Bash(other-tool)" in data["permissions"]["allow"]


def test_reset_noop_when_file_missing(tmp_path: Path) -> None:
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    result = _run(_RESET, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode == 0


def test_reset_requires_scope_and_pattern(tmp_path: Path) -> None:
    result = _run(_RESET, home=tmp_path)
    assert result.returncode != 0
    assert "expected <scope> <pattern>" in result.stderr


# -- list ---------------------------------------------------------------------


def test_list_shows_nerf_entries(tmp_path: Path) -> None:
    _user_settings(
        tmp_path,
        {
            "permissions": {
                "allow": ["Bash(/some/path/nerf-git-commit)", "Bash(unrelated)"],
                "deny": [],
            }
        },
    )
    result = _run(_LIST, home=tmp_path)
    assert result.returncode == 0
    assert "nerf-git-commit" in result.stdout
    assert "unrelated" not in result.stdout


def test_list_no_settings_file(tmp_path: Path) -> None:
    result = _run(_LIST, home=tmp_path)
    assert result.returncode == 0
    assert "No nerf tool permissions" in result.stdout


def test_list_no_nerf_entries(tmp_path: Path) -> None:
    _user_settings(tmp_path, {"permissions": {"allow": ["Bash(unrelated)"], "deny": []}})
    result = _run(_LIST, home=tmp_path)
    assert result.returncode == 0
    assert "No nerf tool permissions" in result.stdout


# -- round-trips ---------------------------------------------------------------


def test_grant_then_deny_moves_entry(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    _run(_GRANT, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    _run(_DENY, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    data = _read(tmp_path / ".claude" / "settings.json")
    assert not any("nerf-test-tool" in e for e in data["permissions"]["allow"])
    assert any("nerf-test-tool" in e for e in data["permissions"]["deny"])


def test_grant_then_reset_clears_entry(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    _run(_GRANT, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    _run(_RESET, "user", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path)
    data = _read(tmp_path / ".claude" / "settings.json")
    assert not any("nerf-test-tool" in e for e in data["permissions"]["allow"])
    assert not any("nerf-test-tool" in e for e in data["permissions"]["deny"])


# -- help flags ---------------------------------------------------------------


# -- grant-by-threat -----------------------------------------------------------


def test_by_threat_allows_inside_denies_outside(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin_with_threats(tmp_path, {
        "nerf-git-log": ("workspace", "none"),
        "nerf-git-add": ("workspace", "workspace"),
        "nerf-git-push": ("workspace", "remote"),
    })
    result = _run(
        _BY_THREAT,
        "user",
        "--read", "workspace", "--write", "workspace",
        "--plugin-root", str(plugin),
        home=tmp_path,
    )
    assert result.returncode == 0
    data = _read(tmp_path / ".claude" / "settings.json")
    allow_str = " ".join(data["permissions"]["allow"])
    deny_str = " ".join(data["permissions"]["deny"])
    assert "nerf-git-log" in allow_str
    assert "nerf-git-add" in allow_str
    assert "nerf-git-push" in deny_str


def test_by_threat_outside_reset(tmp_path: Path) -> None:
    plugin = _mock_plugin_with_threats(tmp_path, {
        "nerf-git-log": ("workspace", "none"),
        "nerf-git-push": ("workspace", "remote"),
    })
    # Pre-seed push as allowed
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-git-push")
    _user_settings(tmp_path, {"permissions": {"allow": [f"Bash({script_path})"], "deny": []}})
    result = _run(
        _BY_THREAT,
        "user",
        "--read", "workspace", "--write", "workspace",
        "--outside", "reset",
        "--plugin-root", str(plugin),
        home=tmp_path,
    )
    assert result.returncode == 0
    data = _read(tmp_path / ".claude" / "settings.json")
    # Push should be removed from allow (reset), not in deny
    deny_str = " ".join(data["permissions"].get("deny", []))
    allow_str = " ".join(data["permissions"].get("allow", []))
    assert "nerf-git-push" not in deny_str
    assert "nerf-git-log" in allow_str


def test_by_threat_filter(tmp_path: Path) -> None:
    _user_settings(tmp_path)
    plugin = _mock_plugin_with_threats(tmp_path, {
        "nerf-git-log": ("workspace", "none"),
        "nerf-az-list": ("remote", "none"),
    })
    result = _run(
        _BY_THREAT,
        "user",
        "--read", "workspace", "--write", "workspace",
        "--filter", "nerf-git-*",
        "--plugin-root", str(plugin),
        home=tmp_path,
    )
    assert result.returncode == 0
    data = _read(tmp_path / ".claude" / "settings.json")
    # Only git tool affected
    all_entries = data["permissions"].get("allow", []) + data["permissions"].get("deny", [])
    assert any("nerf-git-log" in e for e in all_entries)
    assert not any("nerf-az-list" in e for e in all_entries)


def test_by_threat_requires_scope(tmp_path: Path) -> None:
    plugin = _mock_plugin_with_threats(tmp_path, {"nerf-t": ("none", "none")})
    # Missing scope positional -- errors before --read/--write checks fire.
    result = _run(_BY_THREAT, "--read", "none", "--write", "none", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode != 0
    assert "expected <scope>" in result.stderr


def test_by_threat_requires_read_write(tmp_path: Path) -> None:
    plugin = _mock_plugin_with_threats(tmp_path, {"nerf-t": ("none", "none")})
    # Scope provided, but --read/--write still required.
    result = _run(_BY_THREAT, "user", "--plugin-root", str(plugin), home=tmp_path)
    assert result.returncode != 0
    assert "--read is required" in result.stderr


def test_by_threat_invalid_level(tmp_path: Path) -> None:
    plugin = _mock_plugin_with_threats(tmp_path, {"nerf-t": ("none", "none")})
    result = _run(
        _BY_THREAT,
        "user",
        "--read", "galaxy",
        "--write", "none",
        "--plugin-root", str(plugin),
        home=tmp_path,
    )
    assert result.returncode != 0
    assert "invalid read level" in result.stderr


def test_by_threat_annotations(tmp_path: Path) -> None:
    plugin = _mock_plugin_with_threats(tmp_path, {
        "nerf-git-push": ("workspace", "remote"),
    })
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-git-push")
    _user_settings(tmp_path, {"permissions": {"allow": [f"Bash({script_path})"], "deny": []}})
    result = _run(
        _BY_THREAT,
        "user",
        "--read", "workspace", "--write", "workspace",
        "--plugin-root", str(plugin),
        home=tmp_path,
    )
    assert result.returncode == 0
    assert "(was: allowed)" in result.stdout


# -- help flags ---------------------------------------------------------------


@pytest.mark.parametrize("script", [_GRANT, _DENY, _RESET, _BY_THREAT, _LIST])
def test_help_flag_exits_nonzero_with_usage(script: Path) -> None:
    result = _run(script, "--help")
    assert result.returncode != 0
    assert "Usage:" in result.stderr


# -- --create-scope-dir + --prune-older ---------------------------------------


def _versioned_plugin(
    tmp_path: Path, version: str, *, tools: list[str] | None = None
) -> Path:
    """Plugin at tmp_path/plugins/myplugin/<version>/. The grandparent
    (tmp_path/plugins/myplugin/) is the "plugin prefix" for version scans.
    Threat annotations are included so grant-by-threat finds the tools."""
    plugin_root = tmp_path / "plugins" / "myplugin" / version
    scripts_dir = plugin_root / "skills" / "nerf-test" / "scripts"
    scripts_dir.mkdir(parents=True)
    for tool in tools or ["nerf-test-tool"]:
        s = scripts_dir / tool
        s.write_text(
            "#!/bin/bash\n"
            f"# {tool} -- test tool\n"
            "# nerf:threat:read=workspace\n"
            "# nerf:threat:write=workspace\n"
            "echo ok\n"
        )
        s.chmod(0o755)
    return plugin_root


def _stale_entry(tmp_path: Path, version: str, tool: str = "nerf-test-tool") -> str:
    path = tmp_path / "plugins" / "myplugin" / version / "skills" / "nerf-test" / "scripts" / tool
    return f"Bash({path}:*)"


def _invoke_for(script: Path, plugin_root: Path, scope: str, *extra: str) -> list[str]:
    """Build the right CLI args for each write script's normal happy-path
    invocation (so we can exercise the scan in context). Scope is the first
    positional arg for all four write scripts."""
    if script == _BY_THREAT:
        return [
            scope,
            "--read",
            "remote",
            "--write",
            "remote",
            "--plugin-root",
            str(plugin_root),
            *extra,
        ]
    return [scope, "nerf-test-tool", "--plugin-root", str(plugin_root), *extra]


# -- create-scope-dir ---------------------------------------------------------


@pytest.mark.parametrize("script", [_GRANT, _DENY, _RESET, _BY_THREAT])
def test_local_scope_errors_when_claude_missing_without_flag(
    tmp_path: Path, script: Path
) -> None:
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    # No .claude/ pre-created
    result = _run(script, *_invoke_for(script, plugin, "local"), cwd=tmp_path)
    assert result.returncode != 0
    assert ".claude/ not found" in result.stderr
    assert "--create-scope-dir" in result.stderr
    assert not (tmp_path / ".claude").exists()


@pytest.mark.parametrize("script", [_GRANT, _DENY, _RESET, _BY_THREAT])
def test_local_scope_errors_when_claude_is_not_a_directory(
    tmp_path: Path, script: Path
) -> None:
    """If .claude exists as a file or symlink-to-file, --create-scope-dir
    shouldn't try to mkdir it (would fail with a generic 'File exists' error)
    -- the script should surface a clear message instead."""
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    (tmp_path / ".claude").write_text("oops, this is a file")
    result = _run(
        script,
        *_invoke_for(script, plugin, "local", "--create-scope-dir"),
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "not a directory" in result.stderr
    # The file is left alone -- no silent clobber.
    assert (tmp_path / ".claude").read_text() == "oops, this is a file"


@pytest.mark.parametrize("script", [_GRANT, _DENY, _RESET, _BY_THREAT])
def test_create_scope_dir_creates_missing_claude(tmp_path: Path, script: Path) -> None:
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    result = _run(
        script,
        *_invoke_for(script, plugin, "local", "--create-scope-dir"),
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / ".claude").is_dir()
    # grant-reset noop-exits before _ensure_settings_file when no settings
    # exist yet, so its run creates the dir but not the file. The other
    # three explicitly ensure the file.
    if script != _RESET:
        assert (tmp_path / ".claude" / "settings.local.json").is_file()


def test_prune_older_errors_clearly_when_no_version_sort_available(tmp_path: Path) -> None:
    """If neither `sort -V` nor `gsort -V` works (e.g. macOS without coreutils),
    --prune-older errors with an install hint instead of silently miscomparing."""
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    _user_settings(tmp_path, {"permissions": {"allow": [_stale_entry(tmp_path, "1.0.0")], "deny": []}})
    # Stub a PATH containing only a fake `sort` whose -V is a no-op
    # (input passes through unchanged). Mimics BSD sort accepting the flag
    # but not actually version-sorting -- the probe should reject it.
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_sort = fake_bin / "sort"
    fake_sort.write_text("#!/bin/bash\ncat\n")
    fake_sort.chmod(0o755)
    # Also provide jq (the script still needs it).
    if _jq_bin_dir:
        (fake_bin / "jq").symlink_to(Path(_jq_bin_dir) / "jq")
    (fake_bin / "bash").symlink_to("/bin/bash")
    # Provide basename/dirname/cat/printf/find/mkdir/realpath etc. by symlinking
    # everything currently in /usr/bin and /bin minus sort/gsort.
    import contextlib

    for src_dir in ["/usr/bin", "/bin"]:
        for f in Path(src_dir).iterdir():
            if f.name in ("sort", "gsort") or (fake_bin / f.name).exists():
                continue
            with contextlib.suppress(OSError, FileExistsError):
                (fake_bin / f.name).symlink_to(f)

    result = _run(
        _GRANT,
        *_invoke_for(_GRANT, plugin, "user", "--prune-older"),
        home=tmp_path,
        env_extra={"PATH": str(fake_bin)},
    )
    assert result.returncode != 0
    assert "version-aware sort" in result.stderr
    assert "brew install coreutils" in result.stderr
    # Settings untouched
    data = _read(tmp_path / ".claude" / "settings.json")
    assert _stale_entry(tmp_path, "1.0.0") in data["permissions"]["allow"]


def test_no_version_sort_without_prune_flag_warns_and_proceeds(tmp_path: Path) -> None:
    """Without --prune-older, missing version-sort warns the operator (so they
    know the safety check is degraded) and proceeds with the main op."""
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    _user_settings(tmp_path, {"permissions": {"allow": [_stale_entry(tmp_path, "1.0.0")], "deny": []}})
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_sort = fake_bin / "sort"
    fake_sort.write_text("#!/bin/bash\ncat\n")
    fake_sort.chmod(0o755)
    if _jq_bin_dir:
        (fake_bin / "jq").symlink_to(Path(_jq_bin_dir) / "jq")
    (fake_bin / "bash").symlink_to("/bin/bash")
    import contextlib

    for src_dir in ["/usr/bin", "/bin"]:
        for f in Path(src_dir).iterdir():
            if f.name in ("sort", "gsort") or (fake_bin / f.name).exists():
                continue
            with contextlib.suppress(OSError, FileExistsError):
                (fake_bin / f.name).symlink_to(f)

    result = _run(
        _GRANT,
        *_invoke_for(_GRANT, plugin, "user"),  # no --prune-older
        home=tmp_path,
        env_extra={"PATH": str(fake_bin)},
    )
    assert result.returncode == 0, result.stderr
    # Operator is warned about the degraded scan so they know what's missing.
    assert "version analysis not possible" in result.stderr
    assert "brew install coreutils" in result.stderr
    # The main op still completed (entry granted).
    data = _read(tmp_path / ".claude" / "settings.json")
    assert any("nerf-test-tool" in e for e in data["permissions"]["allow"])


# -- prune-older / version scan -----------------------------------------------


@pytest.mark.parametrize("script", [_GRANT, _DENY, _RESET, _BY_THREAT])
def test_warns_on_older_without_prune_flag(tmp_path: Path, script: Path) -> None:
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    stale_1_5 = _stale_entry(tmp_path, "1.5.0")
    stale_1_9 = _stale_entry(tmp_path, "1.9.0-rc.1")
    _user_settings(tmp_path, {"permissions": {"allow": [stale_1_5, stale_1_9], "deny": []}})

    result = _run(script, *_invoke_for(script, plugin, "user"), home=tmp_path)
    assert result.returncode == 0, result.stderr
    # Warning printed, count is right
    assert "2 permission entries reference older versions" in result.stderr
    assert "--prune-older" in result.stderr
    # Stale entries preserved (no prune flag)
    data = _read(tmp_path / ".claude" / "settings.json")
    assert stale_1_5 in data["permissions"]["allow"]
    assert stale_1_9 in data["permissions"]["allow"]


@pytest.mark.parametrize("script", [_GRANT, _DENY, _RESET, _BY_THREAT])
def test_prune_older_removes_stale_entries(tmp_path: Path, script: Path) -> None:
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    stale_1_5 = _stale_entry(tmp_path, "1.5.0")
    stale_1_9 = _stale_entry(tmp_path, "1.9.0-rc.1")
    _user_settings(tmp_path, {"permissions": {"allow": [stale_1_5], "deny": [stale_1_9]}})

    result = _run(script, *_invoke_for(script, plugin, "user", "--prune-older"), home=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Pruned 2 stale entries from older plugin versions" in result.stdout
    data = _read(tmp_path / ".claude" / "settings.json")
    assert stale_1_5 not in data["permissions"].get("allow", [])
    assert stale_1_9 not in data["permissions"].get("deny", [])


@pytest.mark.parametrize("script", [_GRANT, _DENY, _RESET, _BY_THREAT])
def test_errors_on_newer_versions_without_modifying(tmp_path: Path, script: Path) -> None:
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    newer = _stale_entry(tmp_path, "3.0.0")
    initial = {"permissions": {"allow": [newer], "deny": []}}
    _user_settings(tmp_path, initial)

    result = _run(script, *_invoke_for(script, plugin, "user", "--prune-older"), home=tmp_path)
    assert result.returncode != 0
    assert "newer version" in result.stderr
    # Settings untouched
    data = _read(tmp_path / ".claude" / "settings.json")
    assert data == initial


@pytest.mark.parametrize("script", [_GRANT, _DENY])
def test_prune_older_full_sweep_regardless_of_pattern(tmp_path: Path, script: Path) -> None:
    """Even when the current grant targets one narrow tool, --prune-older removes
    ALL older-version entries in scope."""
    plugin = _versioned_plugin(tmp_path, "2.0.0", tools=["nerf-test-a", "nerf-test-b"])
    # Stale entries for tools the current invocation isn't even touching
    stale_a = _stale_entry(tmp_path, "1.0.0", tool="nerf-test-a")
    stale_b = _stale_entry(tmp_path, "1.0.0", tool="nerf-test-b")
    _user_settings(tmp_path, {"permissions": {"allow": [stale_a, stale_b], "deny": []}})

    # Grant just one tool, but prune everything stale
    result = _run(
        script,
        "user",
        "nerf-test-a",
        "--plugin-root",
        str(plugin),
        "--prune-older",
        home=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert "Pruned 2 stale entries" in result.stdout
    data = _read(tmp_path / ".claude" / "settings.json")
    assert stale_a not in data["permissions"].get("allow", [])
    assert stale_b not in data["permissions"].get("allow", [])


def test_scan_ignores_entries_outside_plugin_prefix(tmp_path: Path) -> None:
    """Entries pointing at totally different plugins aren't touched or counted."""
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    unrelated = "Bash(/some/other/plugin/scripts/whatever:*)"
    _user_settings(tmp_path, {"permissions": {"allow": [unrelated], "deny": []}})

    result = _run(_GRANT, *_invoke_for(_GRANT, plugin, "user", "--prune-older"), home=tmp_path)
    assert result.returncode == 0, result.stderr
    # Unrelated entry untouched
    data = _read(tmp_path / ".claude" / "settings.json")
    assert unrelated in data["permissions"]["allow"]


# -- --reset-other-scopes -----------------------------------------------------


def _local_settings(tmp_path: Path, content: dict | None = None) -> Path:
    """Write a local-scope settings file (under cwd's .claude/) in tmp_path."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    f = claude_dir / "settings.local.json"
    f.write_text(json.dumps(content or {}))
    return f


def _project_settings(tmp_path: Path, content: dict | None = None) -> Path:
    """Write a project-scope (committed) settings file."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    f = claude_dir / "settings.json"
    f.write_text(json.dumps(content or {}))
    return f


def _split_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Set up separate home/cwd subdirs so user and project scope settings
    don't share a file path (they would if home == cwd == tmp_path)."""
    home_dir = tmp_path / "home"
    work_dir = tmp_path / "work"
    home_dir.mkdir()
    work_dir.mkdir()
    return home_dir, work_dir


def test_reset_other_scopes_warns_without_flag(tmp_path: Path) -> None:
    """Default behavior: scan other scopes, warn about conflicts, proceed
    with the main op without touching them."""
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-test-tool")
    entry = f"Bash({script_path}:*)"
    # User scope denies the tool; we're about to allow it at local. With
    # home == cwd == tmp_path, user and local files live at different paths
    # under the same .claude/ dir, so they don't clash.
    _user_settings(tmp_path, {"permissions": {"allow": [], "deny": [entry]}})

    result = _run(
        _GRANT, "local", "nerf-test-tool", "--plugin-root", str(plugin), home=tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert "entry exists in 'user' scope (deny)" in result.stderr
    assert "--reset-other-scopes" in result.stderr
    # User scope is untouched -- deny still present.
    data = _read(tmp_path / ".claude" / "settings.json")
    assert entry in data["permissions"]["deny"]
    # Local scope has the new allow entry.
    local = _read(tmp_path / ".claude" / "settings.local.json")
    assert entry in local["permissions"]["allow"]


def test_reset_other_scopes_removes_conflicts(tmp_path: Path) -> None:
    """With --reset-other-scopes: entries in other scopes get removed and
    each removal is printed."""
    home_dir, work_dir = _split_dirs(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-test-tool")
    entry = f"Bash({script_path}:*)"
    # User scope (under home) denies the tool; project scope (under cwd)
    # allows it. We're about to set the final state at local with
    # --reset-other-scopes. home != cwd so the two .json files don't collide.
    _user_settings(home_dir, {"permissions": {"allow": [], "deny": [entry]}})
    _project_settings(work_dir, {"permissions": {"allow": [entry], "deny": []}})

    result = _run(
        _GRANT,
        "local",
        "nerf-test-tool",
        "--plugin-root",
        str(plugin),
        "--reset-other-scopes",
        home=home_dir,
        cwd=work_dir,
    )
    assert result.returncode == 0, result.stderr
    # Both reset lines printed
    assert "Reset from user (deny):" in result.stdout
    assert "Reset from project (allow):" in result.stdout
    # User and project both cleaned out
    user_data = _read(home_dir / ".claude" / "settings.json")
    assert entry not in user_data["permissions"]["deny"]
    project_data = _read(work_dir / ".claude" / "settings.json")
    assert entry not in project_data["permissions"].get("allow", [])
    # Local has the new entry
    local_data = _read(work_dir / ".claude" / "settings.local.json")
    assert entry in local_data["permissions"]["allow"]


def test_reset_other_scopes_noop_when_no_other_entries(tmp_path: Path) -> None:
    """No conflicts in other scopes -> no warning, no reset lines."""
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    _user_settings(tmp_path, {"permissions": {"allow": [], "deny": []}})
    result = _run(
        _GRANT,
        "user",
        "nerf-test-tool",
        "--plugin-root",
        str(plugin),
        "--reset-other-scopes",
        home=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert "Reset from" not in result.stdout
    assert "entry exists in" not in result.stderr


def test_reset_other_scopes_skips_missing_claude_dir(tmp_path: Path) -> None:
    """When scope=user and there's no .claude/ in cwd, the project/local
    scope scans should silently skip rather than error."""
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    _user_settings(tmp_path, {"permissions": {"allow": [], "deny": []}})
    # tmp_path has .claude/ (the user-scope dir), but cwd doesn't.
    # Run from a sibling dir that has no .claude/.
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    result = _run(
        _GRANT,
        "user",
        "nerf-test-tool",
        "--plugin-root",
        str(plugin),
        "--reset-other-scopes",
        home=tmp_path,
        cwd=other_dir,
    )
    assert result.returncode == 0, result.stderr


def test_reset_other_scopes_in_grant_reset_cleans_everywhere(tmp_path: Path) -> None:
    """grant-reset with --reset-other-scopes should wipe the tool from
    all three scopes."""
    home_dir, work_dir = _split_dirs(tmp_path)
    plugin = _mock_plugin(tmp_path, ["nerf-test-tool"])
    script_path = str(plugin / "skills" / "nerf-test" / "scripts" / "nerf-test-tool")
    entry = f"Bash({script_path}:*)"
    _user_settings(home_dir, {"permissions": {"allow": [entry], "deny": []}})
    _project_settings(work_dir, {"permissions": {"allow": [], "deny": [entry]}})
    _local_settings(work_dir, {"permissions": {"allow": [entry], "deny": []}})

    result = _run(
        _RESET,
        "local",
        "nerf-test-tool",
        "--plugin-root",
        str(plugin),
        "--reset-other-scopes",
        home=home_dir,
        cwd=work_dir,
    )
    assert result.returncode == 0, result.stderr
    # User cleaned
    assert entry not in _read(home_dir / ".claude" / "settings.json")["permissions"].get("allow", [])
    # Project cleaned
    assert entry not in _read(work_dir / ".claude" / "settings.json")["permissions"].get("deny", [])
    # Local also cleaned (the main op)
    assert entry not in _read(work_dir / ".claude" / "settings.local.json")["permissions"].get("allow", [])


def test_scan_handles_non_bash_permission_entries(tmp_path: Path) -> None:
    """Real settings can contain WebFetch(...), Read(...), mcp__*, etc. The
    capture("^Bash...") jq filter must not error on those non-matching entries."""
    plugin = _versioned_plugin(tmp_path, "2.0.0")
    stale = _stale_entry(tmp_path, "1.0.0")
    _user_settings(
        tmp_path,
        {
            "permissions": {
                "allow": [
                    stale,
                    "WebFetch(*)",
                    "Read(*)",
                    "mcp__server__tool",
                ],
                "deny": ["Write(/tmp/*)"],
            }
        },
    )
    result = _run(_GRANT, *_invoke_for(_GRANT, plugin, "user", "--prune-older"), home=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Pruned 1 stale entry" in result.stdout
    data = _read(tmp_path / ".claude" / "settings.json")
    # Stale removed, all non-Bash entries preserved untouched
    assert stale not in data["permissions"]["allow"]
    assert "WebFetch(*)" in data["permissions"]["allow"]
    assert "Read(*)" in data["permissions"]["allow"]
    assert "mcp__server__tool" in data["permissions"]["allow"]
    assert "Write(/tmp/*)" in data["permissions"]["deny"]
