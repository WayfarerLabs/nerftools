#!/usr/bin/env bash
# nerfctl-grant-deny -- Deny nerf tools entirely
# This is a control-plane tool for operators, not for agents.

set -euo pipefail

if [[ "${BASH_VERSINFO[0]:-0}" -lt 4 ]]; then
  echo "error: nerfctl-grant-deny requires bash 4+. Found bash ${BASH_VERSION:-unknown}" >&2
  echo "  hint: on macOS, install a newer bash via 'brew install bash'" >&2
  exit 1
fi

# Shared helpers (must come after set -euo and the bash version check).
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "${_SCRIPT_DIR}/_lib.sh"

SCOPE=""
PLUGIN_ROOT=""
PATTERN=""
CREATE_SCOPE_DIR=0
PRUNE_OLDER=0
RESET_OTHER_SCOPES=0

usage() {
  cat >&2 <<'EOF'
Usage: nerfctl-grant-deny <scope> <pattern>
                         [--plugin-root <path>] [--create-scope-dir]
                         [--prune-older] [--reset-other-scopes]

  <scope>                Settings scope: user, project, or local (required)
  <pattern>              Tool name or glob pattern (e.g. nerf-git-commit or nerf-git-*)
  --plugin-root <path>   Override plugin root (for testing; skips auto-detection)
  --create-scope-dir     Create .claude/ if missing (project/local; default: error)
  --prune-older          Remove stale entries referencing older versions of this plugin
                         from the chosen scope's settings (in addition to the main op)
  --reset-other-scopes   Remove matching entries from the two scopes that aren't <scope>,
                         making <scope> the sole source of truth for these tools. Without
                         this flag, conflicting entries in other scopes are warned about.

Scopes:
  user     ~/.claude/settings.json
  project  .claude/settings.json        (committed)
  local    .claude/settings.local.json  (gitignored)

The version scan runs on every invocation when a version-aware sort is
available (GNU `sort -V` or `gsort -V` from brew coreutils). If found: newer-
version entries cause the command to refuse to modify settings; older-version
entries are warned about (or removed with --prune-older). If no version-aware
sort is available, the scan is skipped with a warning -- or, if --prune-older
was passed, the command errors with an install hint. Scope-limited;
--prune-older removes ALL older-version entries in scope, regardless of how
narrow the current pattern is.

Finds all matching tool scripts under the plugin root and adds deny entries
for each, removing any matching allow entries.

The plugin root is auto-detected from CLAUDE_PLUGIN_ROOT or the script's
own location. Use --plugin-root only for testing.

Requires jq.
EOF
  exit 1
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --plugin-root) PLUGIN_ROOT="$2"; shift 2 ;;
    --create-scope-dir) CREATE_SCOPE_DIR=1; shift ;;
    --prune-older) PRUNE_OLDER=1; shift ;;
    --reset-other-scopes) RESET_OTHER_SCOPES=1; shift ;;
    -h|--help) usage ;;
    -*) echo "error: unknown option: $1" >&2; usage ;;
    *) POSITIONAL+=("$1"); shift ;;
  esac
done

if [[ ${#POSITIONAL[@]} -ne 2 ]]; then
  echo "error: expected <scope> <pattern>, got ${#POSITIONAL[@]} positional argument(s)" >&2
  usage
fi
SCOPE="${POSITIONAL[0]}"
PATTERN="${POSITIONAL[1]}"

case "$SCOPE" in
  user|project|local) ;;
  *) echo "error: <scope> must be 'user', 'project', or 'local' (got '$SCOPE')" >&2; usage ;;
esac

_require_jq

RESOLVED_ROOT="$(_resolve_plugin_root)"

mapfile -t MATCHES < <(find "$RESOLVED_ROOT/skills" -path "*/scripts/$PATTERN" -type f 2>/dev/null | sort)

if [[ ${#MATCHES[@]} -eq 0 ]]; then
  echo "error: no tools matching '$PATTERN' found under $RESOLVED_ROOT/skills/*/scripts/" >&2
  echo "hint: use 'nerf-git-*' to match a package, or check tool names in the nerf skills" >&2
  exit 1
fi

SETTINGS="$(_resolve_settings)"
_ensure_settings_file "$SETTINGS"

UPDATED=$(cat "$SETTINGS")

_handle_other_scopes "${MATCHES[@]}"

_scan_stale_versions "$UPDATED" "nerfctl-grant-deny"
if (( STALE_COUNT > 0 )); then
  if [[ "$PRUNE_OLDER" == "1" ]]; then
    UPDATED=$(_remove_stale_entries "$UPDATED")
    echo "Pruned $STALE_COUNT stale entr$( ((STALE_COUNT == 1)) && echo "y" || echo "ies") from older plugin versions"
  else
    echo "warning: $STALE_COUNT permission entr$( ((STALE_COUNT == 1)) && echo "y" || echo "ies") reference older versions of this plugin (pass --prune-older to remove)" >&2
  fi
fi

for SCRIPT_PATH in "${MATCHES[@]}"; do
  TOOL_NAME=$(basename "$SCRIPT_PATH")
  ENTRY="Bash($SCRIPT_PATH:*)"
  STALE_ENTRY="Bash($SCRIPT_PATH)"

  UPDATED=$(printf '%s' "$UPDATED" | jq \
    --arg entry "$ENTRY" \
    --arg stale "$STALE_ENTRY" \
    '
      .permissions //= {}
      | .permissions.allow //= []
      | .permissions.deny //= []
      | .permissions.allow = [.permissions.allow[] | select(. != $entry and . != $stale)]
      | .permissions.deny = [.permissions.deny[] | select(. != $stale)]
      | if (.permissions.deny | index($entry)) == null
        then .permissions.deny += [$entry]
        else .
        end
    ')
  echo "  Denied: $TOOL_NAME"
  echo "    $ENTRY"
done

echo "$UPDATED" > "$SETTINGS"
echo ""
echo "Denied ${#MATCHES[@]} tool(s) (scope: $SCOPE)"
