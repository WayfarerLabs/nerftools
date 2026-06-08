"""Integration tests for the nerf-report manifest tools (write/show/archive)."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from nerftools import BUILTIN_MANIFESTS_DIR
from nerftools.builder import build_script_text
from nerftools.manifest import load_manifest

_MANIFEST = BUILTIN_MANIFESTS_DIR / "nerf-report.yaml"


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# Reference timestamps relative to "now" so tests don't rot. Past timestamps
# are guaranteed to be in the past for any reasonable test run; cutoffs are
# anchored to those past timestamps.
_NOW = datetime.now(UTC)
_LONG_AGO = _NOW - timedelta(days=30)
_MID = _NOW - timedelta(days=20)
_RECENT = _NOW - timedelta(days=10)
_BARELY_PAST = _NOW - timedelta(seconds=60)


@pytest.fixture(scope="module")
def report_tools(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Render the three nerf-report wrapper scripts once per test session."""
    out = tmp_path_factory.mktemp("report-bin")
    manifest = load_manifest(_MANIFEST)
    tools: dict[str, Path] = {}
    for tool_name, tool_spec in manifest.tools.items():
        full_name = f"nerf-{tool_name}"
        script = out / full_name
        script.write_text(
            build_script_text(full_name, manifest.package.name, tool_spec, brand="nerf")
        )
        script.chmod(0o755)
        tools[tool_name] = script
    return tools


def _run(script: Path, *args: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run(
        [str(script), *args], capture_output=True, text=True, env=env, check=False
    )


def _reports_dir(home: Path) -> Path:
    return home / ".nerftools" / "nerf" / "reports"


# -- write -------------------------------------------------------------------


def test_report_writes_to_brand_namespaced_path(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    result = _run(
        report_tools["report"], "bug", "nerf-foo", "body text", home=tmp_path
    )
    assert result.returncode == 0, result.stderr
    files = list(_reports_dir(tmp_path).iterdir())
    assert len(files) == 1
    assert "body text" in files[0].read_text()


def test_report_frontmatter_includes_brand_and_kind(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    _run(report_tools["report"], "complaint", "nerf-x", "x", home=tmp_path)
    text = next(_reports_dir(tmp_path).iterdir()).read_text()
    assert "kind: complaint" in text
    assert 'nerftools_brand: "nerf"' in text
    assert 'tool: "nerf-x"' in text


def test_report_rejects_invalid_kind(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    result = _run(report_tools["report"], "oops", "nerf-foo", "x", home=tmp_path)
    assert result.returncode != 0
    assert "allowed" in result.stderr.lower() or "kind" in result.stderr


def test_report_filename_includes_kind_tool_and_version(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    _run(report_tools["report"], "bug", "nerf-az-repos-pr-edit", "x", home=tmp_path)
    name = next(_reports_dir(tmp_path).iterdir()).name
    # 20260607T123456Z_bug_nerf-az-repos-pr-edit_unknown.md (no plugin.json -> unknown)
    assert re.match(
        r"^\d{8}T\d{6}Z_bug_nerf-az-repos-pr-edit_[A-Za-z0-9._+-]+\.md$", name
    ), name


# -- show --------------------------------------------------------------------


def _seed_reports(tmp_path: Path, specs: list[tuple[str, str, str, str]]) -> None:
    """specs: list of (timestamp, kind, tool, body). Writes files directly."""
    rd = _reports_dir(tmp_path)
    rd.mkdir(parents=True, exist_ok=True)
    for ts, kind, tool, body in specs:
        compact = ts.replace("-", "").replace(":", "").replace("T", "T")
        fname = f"{compact[:15]}Z_{kind}_{tool}_test.md"
        f = rd / fname
        f.write_text(
            f"---\nkind: {kind}\ntool: \"{tool}\"\ntimestamp: \"{ts}\"\n---\n\n{body}\n"
        )


def test_show_filters_by_before_strictly(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    boundary = _MID
    _seed_reports(
        tmp_path,
        [
            (_iso(_LONG_AGO), "bug", "nerf-a", "old body"),
            (_iso(boundary), "bug", "nerf-a", "boundary body"),
            (_iso(boundary + timedelta(seconds=1)), "bug", "nerf-a", "newer body"),
        ],
    )
    # Cutoff exactly matches second entry; strict-less excludes it.
    result = _run(report_tools["report-show"], _iso(boundary), home=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "old body" in result.stdout
    assert "boundary body" not in result.stdout  # equal to cutoff -> excluded
    assert "newer body" not in result.stdout


def test_show_rejects_future_before(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    _seed_reports(tmp_path, [(_iso(_LONG_AGO), "bug", "nerf-a", "x")])
    future = _iso(_NOW + timedelta(days=1))
    result = _run(report_tools["report-show"], future, home=tmp_path)
    assert result.returncode != 0
    assert "future" in result.stderr


@pytest.mark.parametrize(
    "bad_before",
    [
        "2026-05-23",  # bare date, no time/zone
        "2026-05-23T12:00:00",  # naive datetime, no timezone designator
        "yesterday",  # not even a valid format
        "2026-05-23T12:00:00+0800",  # offset must be ±HH:MM, not ±HHMM
    ],
)
def test_show_rejects_before_without_explicit_timezone(
    tmp_path: Path, report_tools: dict[str, Path], bad_before: str
) -> None:
    result = _run(report_tools["report-show"], bad_before, home=tmp_path)
    assert result.returncode != 0


def test_show_normalizes_non_utc_offset_to_utc(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    """An offset cutoff must be converted to UTC for comparison. The same
    instant expressed with different offsets must filter identically."""
    boundary = _MID  # some past instant
    _seed_reports(
        tmp_path,
        [
            (_iso(boundary - timedelta(hours=1)), "bug", "nerf-a", "hour-before"),
            (_iso(boundary + timedelta(hours=1)), "bug", "nerf-a", "hour-after"),
        ],
    )
    # Express the boundary as "-08:00" -- the offset push the wallclock time
    # 8 hours later, so the *instant* is the same as boundary. Strict-less
    # excludes the boundary; hour-before matches, hour-after doesn't.
    offset_cutoff = (
        (boundary + timedelta(hours=-8)).strftime("%Y-%m-%dT%H:%M:%S") + "-08:00"
    )
    result = _run(report_tools["report-show"], offset_cutoff, home=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "hour-before" in result.stdout
    assert "hour-after" not in result.stdout


def test_show_filters_by_kind_and_tool(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    _seed_reports(
        tmp_path,
        [
            (_iso(_LONG_AGO), "bug", "nerf-a", "bug-a"),
            (_iso(_LONG_AGO + timedelta(days=1)), "complaint", "nerf-a", "complaint-a"),
            (_iso(_LONG_AGO + timedelta(days=2)), "bug", "nerf-b", "bug-b"),
        ],
    )
    # Cutoff includes everything seeded; filter to bug + nerf-a.
    # Switches/options come BEFORE positionals per the parser convention.
    result = _run(
        report_tools["report-show"],
        "--kind", "bug",
        "--tool", "nerf-a",
        _iso(_BARELY_PAST),
        home=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert "bug-a" in result.stdout
    assert "complaint-a" not in result.stdout
    assert "bug-b" not in result.stdout


def test_show_skips_reviewed_by_default(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    _seed_reports(tmp_path, [(_iso(_LONG_AGO), "bug", "nerf-a", "fresh")])
    reviewed = _reports_dir(tmp_path) / "reviewed"
    reviewed.mkdir(parents=True)
    triaged_ts = _iso(_LONG_AGO - timedelta(days=10))
    (reviewed / "old_bug_nerf-x_test.md").write_text(
        f'---\nkind: bug\ntool: "nerf-x"\ntimestamp: "{triaged_ts}"\n---\n\nalready-triaged\n'
    )
    cutoff = _iso(_BARELY_PAST)
    result = _run(report_tools["report-show"], cutoff, home=tmp_path)
    assert "fresh" in result.stdout
    assert "already-triaged" not in result.stdout

    # With --include-reviewed both show up.
    result2 = _run(
        report_tools["report-show"], "--include-reviewed", cutoff, home=tmp_path
    )
    assert "fresh" in result2.stdout
    assert "already-triaged" in result2.stdout


# -- archive -----------------------------------------------------------------


def test_archive_moves_matching_to_reviewed_subdir(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    boundary = _MID
    _seed_reports(
        tmp_path,
        [
            (_iso(_LONG_AGO), "bug", "nerf-a", "old"),
            (_iso(boundary), "bug", "nerf-a", "boundary"),
        ],
    )
    result = _run(report_tools["report-archive"], _iso(boundary), home=tmp_path)
    assert result.returncode == 0, result.stderr
    rd = _reports_dir(tmp_path)
    # 'old' (< cutoff) moved; boundary (= cutoff) not moved.
    top_files = [f for f in rd.iterdir() if f.is_file()]
    assert len(top_files) == 1
    assert "boundary" in top_files[0].read_text()
    archived = list((rd / "reviewed").iterdir())
    assert len(archived) == 1
    assert "old" in archived[0].read_text()


def test_archive_rejects_future_before(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    _seed_reports(tmp_path, [(_iso(_LONG_AGO), "bug", "nerf-a", "x")])
    future = _iso(_NOW + timedelta(days=1))
    result = _run(report_tools["report-archive"], future, home=tmp_path)
    assert result.returncode != 0
    assert "future" in result.stderr


def test_archive_with_filters(
    tmp_path: Path, report_tools: dict[str, Path]
) -> None:
    _seed_reports(
        tmp_path,
        [
            (_iso(_LONG_AGO), "bug", "nerf-a", "bug-a"),
            (_iso(_LONG_AGO + timedelta(days=1)), "complaint", "nerf-a", "complaint-a"),
        ],
    )
    result = _run(
        report_tools["report-archive"],
        "--kind", "bug",
        _iso(_BARELY_PAST),
        home=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    rd = _reports_dir(tmp_path)
    top_files = [f for f in rd.iterdir() if f.is_file()]
    # Only complaint remains at top level
    assert len(top_files) == 1
    assert "complaint-a" in top_files[0].read_text()


# -- NERFTOOLS_BRAND exposure -----------------------------------------------


def test_nerftools_brand_is_exposed_to_script_mode_tools(
    report_tools: dict[str, Path],
) -> None:
    """The builder change to expose NERFTOOLS_BRAND should appear verbatim
    in the generated wrapper for any script-mode tool."""
    text = report_tools["report"].read_text()
    assert 'NERFTOOLS_BRAND="nerf"' in text


def test_nerftools_brand_reflects_custom_prefix() -> None:
    """A non-default prefix should produce a different NERFTOOLS_BRAND."""
    manifest = load_manifest(_MANIFEST)
    spec = next(iter(manifest.tools.values()))
    text = build_script_text("acme-report", manifest.package.name, spec, brand="acme")
    assert 'NERFTOOLS_BRAND="acme"' in text
