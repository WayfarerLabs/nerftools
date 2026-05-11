#!/usr/bin/env bash

# ============================================================================
# Shared helpers for ops scripts.
# Source this file, do not execute it directly.
#
# Usage: source "$(dirname "${BASH_SOURCE[0]}")/_common.bash"
# ============================================================================

# Check that a supported npm package runner is available.
# Call this early to fail fast with a clear message.
require_npm_package_runner() {
    if command -v bunx &>/dev/null; then return 0; fi
    if command -v pnpm &>/dev/null; then return 0; fi
    if command -v npx &>/dev/null; then return 0; fi
    echo "Error: no npm package runner found (tried bunx, pnpm dlx, npx)." >&2
    echo "Install one of: bun, pnpm, or Node.js." >&2
    return 1
}

# Run an npm package via the best available package runner.
# Detects bunx, pnpm dlx, or npx (in that order).
#
# Usage: run_npm_package <package[@version]> [args...]
# Example: run_npm_package "rulesync@7.14.0" generate
run_npm_package() {
    if command -v bunx &>/dev/null; then
        bunx "$@"
    elif command -v pnpm &>/dev/null; then
        pnpm dlx "$@"
    elif command -v npx &>/dev/null; then
        npx -y "$@"
    else
        echo "Error: no npm package runner found (tried bunx, pnpm dlx, npx)." >&2
        echo "Install one of: bun, pnpm, or Node.js." >&2
        return 1
    fi
}

# Read a version string from a file.
# Searches from the given directory upward to the filesystem root.
# Fails if the file is not found.
#
# Usage: read_version_file <filename> [start_dir]
read_version_file() {
    local filename="$1"
    local dir="${2:-$PWD}"

    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/$filename" ]]; then
            head -1 "$dir/$filename" | tr -d '[:space:]'
            return 0
        fi
        dir="$(dirname "$dir")"
    done

    echo "Error: could not find $filename in $PWD or any parent directory." >&2
    return 1
}
