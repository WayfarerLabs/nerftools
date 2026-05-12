#!/usr/bin/env bash

# ============================================================================
# Rulesync update and generate
#
# Runs version-pinned rulesync install --update and generate commands.
# The version is read from .rulesync-version (required).
#
# Usage: ./ops/scripts/rulesync-upgen.bash
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=./_common.bash
source "$SCRIPT_DIR/_common.bash"
require_npm_package_runner

# Note: `set -e` does not reliably propagate failures from command substitution
# on the right side of an assignment, so check the exit status explicitly.
RULESYNC_VERSION=$(read_version_file .rulesync-version "$REPO_ROOT") || exit 1
if [[ -z "$RULESYNC_VERSION" ]]; then
    echo "Error: .rulesync-version is empty or contains only whitespace." >&2
    exit 1
fi

cd "$REPO_ROOT"

echo "Running rulesync install --update (v$RULESYNC_VERSION)..."
run_npm_package rulesync@"$RULESYNC_VERSION" install --update

echo "Running rulesync generate (v$RULESYNC_VERSION)..."
run_npm_package rulesync@"$RULESYNC_VERSION" generate

echo "Done."
