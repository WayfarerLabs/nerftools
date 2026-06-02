#!/usr/bin/env bash

# ============================================================================
# Generate plugins
#
# Regenerates the committed plugin outputs under out/ from nerf.yaml,
# manifests under nerftools/default_manifests/, and the plugin generation
# code in nerftools/. Run after changing any of those sources, then commit
# the resulting out/ changes.
#
# Usage:
#   ./scripts/generate-plugins.sh           # regenerate out/ in place
#   ./scripts/generate-plugins.sh --check   # regenerate, then fail if out/ differs from HEAD
# ============================================================================

set -euo pipefail

CHECK_MODE=false
for arg in "$@"; do
    case "$arg" in
        --check) CHECK_MODE=true ;;
        *) echo "Error: unknown argument: $arg" >&2; exit 2 ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v uv &>/dev/null; then
    echo "Error: uv is not installed. See https://docs.astral.sh/uv/" >&2
    exit 1
fi

cd "$REPO_ROOT"

echo "Generating claude-plugin..."
uv run nerf generate --target claude-plugin -c nerf.yaml --outdir ./out/claude-plugin

echo "Generating codex-plugin..."
uv run nerf generate --target codex-plugin -c nerf.yaml --outdir ./out/codex-plugin

if [[ "$CHECK_MODE" == "true" ]]; then
    drift=false
    if ! git diff --quiet -- out/; then
        echo "::error::Plugin output under out/ is out of sync with sources."
        git diff --stat -- out/
        drift=true
    fi
    untracked=$(git ls-files --others --exclude-standard out/)
    if [[ -n "$untracked" ]]; then
        echo "::error::Plugin generation produced untracked files under out/:"
        echo "$untracked"
        drift=true
    fi
    if [[ "$drift" == "true" ]]; then
        echo "Run ./scripts/generate-plugins.sh locally and commit the result."
        exit 1
    fi
    echo "Plugin outputs match committed state."
fi

echo "Done."
