"""nerftools: build and manage nerf tools."""

from importlib.resources import files
from pathlib import Path

# Default manifests ship as a subpackage, accessible via importlib.resources
# for both editable installs and published wheels.
BUILTIN_MANIFESTS_DIR = Path(str(files("nerftools.default_manifests")))

_NERFCTL_DIR = Path(__file__).parent / "nerfctl" / "claude"
_NERF_REPORT_SCRIPT = Path(__file__).parent / "nerf_report" / "script.sh"
_NERF_REPORT_VERSION_PLACEHOLDER = "__NERFTOOLS_VERSION__"

NERFCTL_SCRIPTS: dict[str, Path] = {
    "nerfctl-grant-allow": _NERFCTL_DIR / "grant-allow.sh",
    "nerfctl-grant-deny": _NERFCTL_DIR / "grant-deny.sh",
    "nerfctl-grant-reset": _NERFCTL_DIR / "grant-reset.sh",
    "nerfctl-grant-by-threat": _NERFCTL_DIR / "grant-by-threat.sh",
    "nerfctl-grant-list": _NERFCTL_DIR / "grant-list.sh",
}


def install_nerfctl(output: Path) -> list[Path]:
    """Copy nerfctl scripts into *output*. Returns paths written."""
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, src in NERFCTL_SCRIPTS.items():
        if not src.exists():
            msg = f"nerfctl script not found: {src}"
            raise FileNotFoundError(msg)
        dest = output / name
        # Read as text to normalize CRLF -> LF (Windows checkout), then
        # write as raw UTF-8 bytes to guarantee Unix line endings.
        dest.write_bytes(src.read_text(encoding="utf-8").encode("utf-8"))
        dest.chmod(0o755)
        written.append(dest)
    return written


def install_nerf_report(output: Path, *, version: str) -> Path:
    """Install the nerf-report script into *output*, stamping in *version*.

    Returns the path written. Raises ValueError if the template is missing
    its version placeholder, or if the placeholder somehow survives the
    substitution (defense against a malformed template shipping a script
    that misreports its own version).
    """
    if not _NERF_REPORT_SCRIPT.exists():
        msg = f"nerf-report script template not found: {_NERF_REPORT_SCRIPT}"
        raise FileNotFoundError(msg)
    output.mkdir(parents=True, exist_ok=True)
    text = _NERF_REPORT_SCRIPT.read_text(encoding="utf-8")
    if _NERF_REPORT_VERSION_PLACEHOLDER not in text:
        msg = (
            f"nerf-report script template at {_NERF_REPORT_SCRIPT} is "
            f"missing the {_NERF_REPORT_VERSION_PLACEHOLDER!r} placeholder"
        )
        raise ValueError(msg)
    text = text.replace(_NERF_REPORT_VERSION_PLACEHOLDER, version)
    if _NERF_REPORT_VERSION_PLACEHOLDER in text:
        msg = (
            f"nerf-report version stamping incomplete: "
            f"{_NERF_REPORT_VERSION_PLACEHOLDER!r} still present after "
            f"substitution (version={version!r})"
        )
        raise ValueError(msg)
    dest = output / "nerf-report"
    dest.write_bytes(text.encode("utf-8"))
    dest.chmod(0o755)
    return dest
