#!/usr/bin/env bash

# ============================================================================
# Rulesync update and generate
#
# Runs version-pinned rulesync install --update and generate commands.
# The version is read from .rulesync-version at the repo root.
#
# Usage: ./scripts/rulesync-upgen.bash
# ============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

VERSION_FILE="$REPO_ROOT/.rulesync-version"
if [[ ! -f "$VERSION_FILE" ]]; then
    echo "Error: $VERSION_FILE not found." >&2
    exit 1
fi
RULESYNC_VERSION=$(head -1 "$VERSION_FILE" | tr -d '[:space:]')
if [[ -z "$RULESYNC_VERSION" ]]; then
    echo "Error: $VERSION_FILE is empty or contains only whitespace." >&2
    exit 1
fi

# Pick the first available npm package runner.
if command -v bunx &>/dev/null; then
    RUNNER=(bunx)
elif command -v pnpm &>/dev/null; then
    RUNNER=(pnpm dlx)
elif command -v npx &>/dev/null; then
    RUNNER=(npx -y)
else
    echo "Error: no npm package runner found (tried bunx, pnpm dlx, npx)." >&2
    echo "Install one of: bun, pnpm, or Node.js." >&2
    exit 1
fi

cd "$REPO_ROOT"

echo "Running rulesync install --update (v$RULESYNC_VERSION)..."
"${RUNNER[@]}" rulesync@"$RULESYNC_VERSION" install --update

echo "Running rulesync generate (v$RULESYNC_VERSION)..."
"${RUNNER[@]}" rulesync@"$RULESYNC_VERSION" generate

echo "Done."
