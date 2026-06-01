"""Tests for the nerf-report shell helper."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from nerftools import install_nerf_report


def _install(tmp_path: Path, *, version: str = "9.9.9") -> Path:
    return install_nerf_report(tmp_path / "scripts", version=version)


def _run(script: Path, args: list[str], *, home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        check=False,
    )


def test_install_stamps_version_into_script(tmp_path: Path) -> None:
    script = _install(tmp_path, version="1.2.3")
    text = script.read_text()
    assert 'NERFTOOLS_VERSION="1.2.3"' in text
    assert "__NERFTOOLS_VERSION__" not in text
    assert script.stat().st_mode & 0o111  # executable


def test_no_args_prints_usage_and_exits_nonzero(tmp_path: Path) -> None:
    script = _install(tmp_path)
    result = _run(script, [], home=tmp_path / "home")
    assert result.returncode == 2
    assert "Usage: nerf-report" in result.stderr


def test_wrong_arg_count_prints_usage(tmp_path: Path) -> None:
    script = _install(tmp_path)
    result = _run(script, ["bug", "nerf-foo"], home=tmp_path / "home")
    assert result.returncode == 2
    assert "Usage: nerf-report" in result.stderr


def test_invalid_kind_rejected(tmp_path: Path) -> None:
    script = _install(tmp_path)
    result = _run(script, ["oopsie", "nerf-foo", "body"], home=tmp_path / "home")
    assert result.returncode == 2
    assert "invalid kind" in result.stderr


@pytest.mark.parametrize("kind", ["bug", "bypass", "complaint", "request"])
def test_each_kind_writes_report(tmp_path: Path, kind: str) -> None:
    script = _install(tmp_path)
    home = tmp_path / "home"
    result = _run(script, [kind, "nerf-foo", "the body"], home=home)
    assert result.returncode == 0, result.stderr
    reports = list((home / ".nerftools" / "reports").iterdir())
    assert len(reports) == 1
    content = reports[0].read_text()
    assert f"kind: {kind}" in content
    assert "the body" in content


def test_filename_composition(tmp_path: Path) -> None:
    script = _install(tmp_path, version="2.0.0")
    home = tmp_path / "home"
    _run(script, ["bug", "nerf-az-repos-pr-edit", "x"], home=home)
    reports = list((home / ".nerftools" / "reports").iterdir())
    assert len(reports) == 1
    name = reports[0].name
    # 20260601T123456Z_abcd_bug_nerf-az-repos-pr-edit_2.0.0.md
    assert re.match(
        r"^\d{8}T\d{6}Z_[0-9a-f]{4}_bug_nerf-az-repos-pr-edit_2\.0\.0\.md$", name
    ), name


def test_frontmatter_fields_present(tmp_path: Path) -> None:
    script = _install(tmp_path, version="3.1.4")
    home = tmp_path / "home"
    result = subprocess.run(
        ["bash", str(script), "complaint", "nerf-foo", "the body"],
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "NERF_REPORT_SESSION": "sess-abc"},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    content = next((home / ".nerftools" / "reports").iterdir()).read_text()
    assert "kind: complaint" in content
    assert 'tool: "nerf-foo"' in content
    assert 'nerftools_version: "3.1.4"' in content
    assert 'session: "sess-abc"' in content
    assert re.search(r'timestamp: "\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"', content)


def test_tool_name_sanitized_in_filename(tmp_path: Path) -> None:
    script = _install(tmp_path)
    home = tmp_path / "home"
    # Tool name with characters not allowed in the filename set.
    _run(script, ["bug", "weird/name with spaces", "body"], home=home)
    name = next((home / ".nerftools" / "reports").iterdir()).name
    # / and space replaced with _
    assert "weird_name_with_spaces" in name


def test_body_with_special_chars_preserved(tmp_path: Path) -> None:
    script = _install(tmp_path)
    home = tmp_path / "home"
    body = 'has "quotes" and $vars and `backticks` and\nnewline'
    _run(script, ["bug", "nerf-foo", body], home=home)
    content = next((home / ".nerftools" / "reports").iterdir()).read_text()
    assert body in content


def test_session_override_takes_precedence(tmp_path: Path) -> None:
    script = _install(tmp_path)
    home = tmp_path / "home"
    result = subprocess.run(
        ["bash", str(script), "bug", "nerf-foo", "x"],
        capture_output=True,
        text=True,
        env={
            "HOME": str(home),
            "PATH": "/usr/bin:/bin",
            "NERF_REPORT_SESSION": "explicit",
            "CLAUDE_SESSION_ID": "claude-id",
        },
        check=False,
    )
    assert result.returncode == 0, result.stderr
    content = next((home / ".nerftools" / "reports").iterdir()).read_text()
    assert 'session: "explicit"' in content
