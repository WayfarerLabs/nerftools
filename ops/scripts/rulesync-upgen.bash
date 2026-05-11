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

RULESYNC_VERSION=$(read_version_file .rulesync-version "$REPO_ROOT")

cd "$REPO_ROOT"

echo "Running rulesync install --update (v$RULESYNC_VERSION)..."
run_npm_package rulesync@"$RULESYNC_VERSION" install --update

echo "Running rulesync generate (v$RULESYNC_VERSION)..."
run_npm_package rulesync@"$RULESYNC_VERSION" generate

echo "Done."
