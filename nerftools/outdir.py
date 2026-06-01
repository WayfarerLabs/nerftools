"""Helpers for managing nerf generate output directories safely.

Each builder that cleans its output directory before writing must call
prepare_output_dir at the start of the build and write_build_marker at the
end. This protects against the catastrophic case where --outdir points at a
directory the user did not intend to wipe (e.g. a repo root).
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

BUILD_MARKER = ".nerf-build-manifest"

CleanStrategy = Literal["files", "subdirs", "all"]


class OutdirGuardError(ValueError):
    """Raised when an output directory is not safe to clean."""


def prepare_output_dir(
    output_dir: Path,
    *,
    target: str,
    keep_existing: bool,
    clean: CleanStrategy,
    force: bool = False,
) -> bool:
    """Ensure output_dir exists, refuse if it looks unmanaged, then clean it.

    A directory is considered managed if it is empty or contains a regular
    BUILD_MARKER file written by a previous nerf generate run. Any other
    non-empty directory is refused (with --outdir / --keep-existing /
    --force hints) so we never wipe a user's working tree.

    The clean strategy mirrors each target's existing behavior: bin removes
    only files, skills removes only subdirs, and the two plugin targets
    remove everything (with symlinks rejected even under force, since a
    symlinked entry at the top level triggers shutil.rmtree to error
    partway through). keep_existing=True skips the clean step entirely
    while still ensuring the directory exists. force=True skips the
    marker and .git checks but does not relax the symlink check.

    Returns True iff it is safe for the caller to mark this directory as a
    managed build output at the end of the build. keep_existing on an
    unmanaged non-empty directory returns False so we do not claim
    ownership of (and thus authorize future wipes of) foreign files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    marker = output_dir / BUILD_MARKER
    # A symlinked marker would otherwise both bypass the per-entry symlink
    # check below (entries excludes BUILD_MARKER) and let exists()/is_file()
    # be tricked into treating a foreign path as managed.
    if marker.is_symlink():
        raise OutdirGuardError(
            f"refusing to use output directory {output_dir} for target "
            f"'{target}': {BUILD_MARKER} is a symlink. Remove it manually "
            f"before proceeding."
        )

    entries = [e for e in output_dir.iterdir() if e.name != BUILD_MARKER]
    has_marker = marker.is_file()

    if keep_existing:
        return has_marker or not entries

    if not force:
        if entries and not has_marker:
            raise OutdirGuardError(
                f"refusing to clean output directory {output_dir} for target "
                f"'{target}': it is non-empty and was not produced by a previous "
                f"nerf generate run (no {BUILD_MARKER} marker). Pass --outdir "
                f"to a fresh or previously-built location, --keep-existing to "
                f"preserve unmanaged files, or --force to clean it anyway."
            )
        # Defense in depth: even a marker-bearing dir is refused if it also
        # contains a .git -- that combination almost always means the marker
        # was committed/copied into a place that shouldn't be wiped.
        if (output_dir / ".git").exists():
            raise OutdirGuardError(
                f"refusing to clean output directory {output_dir} for target "
                f"'{target}': it contains a .git entry. Pass --outdir to a "
                f"different location, or --force to clean it anyway."
            )

    # Scan for symlinks before deleting anything so a rejected directory is
    # left untouched.
    for entry in entries:
        if entry.is_symlink():
            raise OutdirGuardError(
                f"refusing to clean symlink in output directory: {entry}. "
                "Remove the symlink manually before proceeding."
            )

    for entry in entries:
        if entry.is_dir() and clean in ("subdirs", "all"):
            shutil.rmtree(entry)
        elif entry.is_file() and clean in ("files", "all"):
            entry.unlink()

    return True


def write_build_marker(output_dir: Path, *, target: str) -> None:
    """Mark output_dir as a managed nerf build output."""
    marker = output_dir / BUILD_MARKER
    if marker.is_symlink():
        raise OutdirGuardError(
            f"refusing to write {BUILD_MARKER} in {output_dir}: it is a "
            f"symlink. Remove it manually before proceeding."
        )
    marker.write_text(f"{target}\n")
