#!/usr/bin/env bash
# nerfctl-grant-allow -- Allow nerf tools without prompting
# This is a control-plane tool for operators, not for agents.

if [[ "${BASH_VERSINFO[0]:-0}" -lt 4 ]]; then
  echo "error: nerfctl-grant-allow requires bash 4+. Found bash ${BASH_VERSION:-unknown}" >&2
  echo "  hint: on macOS, install a newer bash via 'brew install bash'" >&2
  exit 1
fi

set -euo pipefail

SCOPE="user"
PLUGIN_ROOT=""
PATTERN=""
CREATE_SCOPE_DIR=0
PRUNE_OLDER=0

usage() {
  cat >&2 <<'EOF'
Usage: nerfctl-grant-allow <pattern> [--scope user|local] [--plugin-root <path>]
                          [--create-scope-dir] [--prune-older]

  <pattern>              Tool name or glob pattern (e.g. nerf-git-commit or nerf-git-*)
  --scope user|local     Settings scope (default: user)
  --plugin-root <path>   Override plugin root (for testing; skips auto-detection)
  --create-scope-dir     Create .claude/ if missing (local scope only; default: error)
  --prune-older          Remove stale entries referencing older versions of this plugin
                         from the chosen scope's settings (in addition to the main op)

The version scan runs on every invocation when a version-aware sort is
available (GNU `sort -V` or `gsort -V` from brew coreutils). If found: newer-
version entries cause the command to refuse to modify settings; older-version
entries are warned about (or removed with --prune-older). If no version-aware
sort is available, the scan is skipped with a warning -- or, if --prune-older
was passed, the command errors with an install hint. Scope-limited;
--prune-older removes ALL older-version entries in scope, regardless of how
narrow the current pattern is.

Finds all matching tool scripts under the plugin root and adds permission
entries for each to the allow list.

The plugin root is auto-detected from CLAUDE_PLUGIN_ROOT or the script's
own location. Use --plugin-root only for testing.

Requires jq.
EOF
  exit 1
}

_require_jq() {
  if ! command -v jq > /dev/null 2>&1; then
    echo "error: jq is required but not installed" >&2
    exit 1
  fi
}

_resolve_settings() {
  case "$SCOPE" in
    user)  echo "$HOME/.claude/settings.json" ;;
    local)
      if [[ ! -d ".claude" ]]; then
        if [[ -e ".claude" ]]; then
          # .claude exists but isn't a directory (file, symlink-to-file, etc.).
          # mkdir would just fail with a generic error; surface a clearer one.
          echo "error: .claude exists in the current directory but is not a directory; refusing to proceed" >&2
          exit 1
        fi
        if [[ "$CREATE_SCOPE_DIR" == "1" ]]; then
          mkdir -p ".claude"
        else
          echo "error: .claude/ not found in current directory" >&2
          echo "  hint: pass --create-scope-dir to create it" >&2
          exit 1
        fi
      fi
      echo ".claude/settings.local.json"
      ;;
    *) echo "error: unknown scope '$SCOPE' (use 'user' or 'local')" >&2; exit 1 ;;
  esac
}

# Find a sort command that actually does version-aware sorting. GNU sort
# has -V; BSD sort (default macOS) does not. Try `sort -V` then `gsort -V`
# (brew coreutils). Probes with a known input/output to confirm correctness
# (BSD sort may accept -V but fall back to lex). Outputs the command name
# on stdout, or returns 1 if none works.
_pick_version_sorter() {
  # Probe input has a trailing newline; expected has none because $(...)
  # strips trailing newlines from command substitution output.
  local probe_in=$'1.10.0\n1.9.0\n'
  local probe_out=$'1.9.0\n1.10.0'
  local cmd
  for cmd in sort gsort; do
    command -v "$cmd" > /dev/null 2>&1 || continue
    if [[ "$(printf '%s' "$probe_in" | "$cmd" -V 2>/dev/null)" == "$probe_out" ]]; then
      echo "$cmd"
      return 0
    fi
  done
  return 1
}

# Scan permission entries in $1 (settings JSON) for paths under this plugin's
# version-cousin tree (same plugin prefix, different version segment). Sets:
#   STALE_COUNT  -- number of older-version entries found
#   STALE_JSON   -- JSON array of stale entry strings (for the prune jq filter)
# Exits 1 if any newer-version entries are found (refuses to mutate settings
# when the operator may have run the wrong nerfctl binary). Also exits 1 if
# the operator asked for --prune-older but no version-aware sort is available.
_scan_stale_versions() {
  local settings_json="$1"
  local tool_name="$2"
  local current_version
  local plugin_prefix
  current_version=$(basename "$RESOLVED_ROOT")
  plugin_prefix="$(dirname "$RESOLVED_ROOT")/"

  STALE_COUNT=0
  STALE_JSON="[]"

  local vsort
  vsort=$(_pick_version_sorter) || vsort=""
  if [[ -z "$vsort" ]]; then
    if [[ "$PRUNE_OLDER" == "1" ]]; then
      echo "error: ${tool_name}: --prune-older requires a version-aware sort, but neither 'sort -V' nor 'gsort -V' works on this system" >&2
      echo "  hint: on macOS, run 'brew install coreutils' (provides gsort); on other platforms, install GNU coreutils" >&2
      echo "  hint: or omit --prune-older to skip the version scan" >&2
      exit 1
    fi
    # No prune requested: warn that the scan can't run, then proceed. We
    # lose newer-version detection here, but blocking the operator's main
    # work over a missing optional tool isn't right.
    echo "warning: ${tool_name}: version analysis not possible -- neither 'sort -V' nor 'gsort -V' works on this system" >&2
    echo "  hint: on macOS, run 'brew install coreutils' (provides gsort); on other platforms, install GNU coreutils" >&2
    return 0
  fi

  # Extract <version>\t<entry> for any allow/deny entry whose Bash(...) path
  # starts with the plugin prefix.
  local entries
  entries=$(printf '%s' "$settings_json" | jq -r --arg prefix "$plugin_prefix" '
    [
      (.permissions.allow // [] | map({entry: .})),
      (.permissions.deny  // [] | map({entry: .}))
    ]
    | flatten
    | map(. as $row
          | ($row.entry | capture("^Bash\\((?<path>[^)]+?)(?::\\*)?\\)$")? // null) as $cap
          | if $cap != null and ($cap.path | startswith($prefix))
            then {entry: $row.entry, ver: ($cap.path | ltrimstr($prefix) | split("/")[0])}
            else null
            end)
    | map(select(. != null))
    | .[] | "\(.ver)\t\(.entry)"
  ')

  local newer_count=0
  local stale_entries=()
  if [[ -n "$entries" ]]; then
    while IFS=$'\t' read -r ver entry; do
      [[ -z "$ver" ]] && continue
      [[ "$ver" == "$current_version" ]] && continue
      # vsort -V puts the larger version last; if ver sorts after current, ver is newer.
      if [[ "$(printf '%s\n%s\n' "$ver" "$current_version" | "$vsort" -V | tail -1)" == "$ver" ]]; then
        newer_count=$((newer_count + 1))
      else
        stale_entries+=("$entry")
      fi
    done <<< "$entries"
  fi

  if (( newer_count > 0 )); then
    echo "error: ${tool_name}: found ${newer_count} permission entr$( ((newer_count == 1)) && echo "y" || echo "ies") referencing a newer version of this plugin; refusing to modify settings" >&2
    echo "  hint: run the matching newer nerfctl binary, or remove the entries manually" >&2
    exit 1
  fi

  STALE_COUNT=${#stale_entries[@]}
  if (( STALE_COUNT > 0 )); then
    STALE_JSON=$(printf '%s\n' "${stale_entries[@]}" | jq -R '.' | jq -s '.')
  fi
}

# Given the current settings JSON in $1 and STALE_JSON populated by
# _scan_stale_versions, return new JSON with the stale entries removed from
# both allow and deny lists.
_remove_stale_entries() {
  printf '%s' "$1" | jq --argjson stale "$STALE_JSON" '
    .permissions //= {}
    | .permissions.allow = ((.permissions.allow // []) - $stale)
    | .permissions.deny  = ((.permissions.deny  // []) - $stale)
  '
}

_ensure_settings_file() {
  local file="$1"
  local dir
  dir=$(dirname "$file")
  [[ -d "$dir" ]] || mkdir -p "$dir"
  [[ -f "$file" ]] || echo '{}' > "$file"
}

_resolve_plugin_root() {
  # If --plugin-root was given, use it directly (testing override)
  if [[ -n "$PLUGIN_ROOT" ]]; then
    echo "$PLUGIN_ROOT"
    return
  fi

  local resolved=""

  # Try CLAUDE_PLUGIN_ROOT env var (canonicalize to prevent path traversal)
  if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
    local canonical
    canonical=$(realpath "$CLAUDE_PLUGIN_ROOT" 2>/dev/null || echo "")
    if [[ -n "$canonical" && "$canonical" == "$HOME/.claude/plugins/"* ]]; then
      resolved="$canonical"
    else
      echo "warning: CLAUDE_PLUGIN_ROOT '$CLAUDE_PLUGIN_ROOT' is not under ~/.claude/plugins/; deriving from script location" >&2
    fi
  else
    echo "warning: CLAUDE_PLUGIN_ROOT not set; deriving from script location" >&2
  fi

  # Fall back to deriving from script location: <plugin-root>/scripts/<this-script>
  if [[ -z "$resolved" ]]; then
    local script_dir
    script_dir=$(cd "$(dirname "$(realpath "$0")")" && pwd)
    resolved=$(cd "$script_dir/.." && pwd)
  fi

  # Verify the resolved root is under the Claude plugin hierarchy
  if [[ "$resolved" != "$HOME/.claude/plugins/"* ]]; then
    echo "error: resolved plugin root '$resolved' is not under ~/.claude/plugins/" >&2
    echo "  hint: if testing, use --plugin-root to override" >&2
    exit 1
  fi

  # Verify it looks like a plugin
  if [[ ! -d "$resolved/.claude-plugin" ]]; then
    echo "error: '$resolved' does not contain .claude-plugin/ -- not a valid plugin root" >&2
    exit 1
  fi
  if [[ ! -d "$resolved/skills" ]]; then
    echo "error: '$resolved' does not contain skills/ -- not a valid plugin root" >&2
    exit 1
  fi

  echo "$resolved"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="$2"; shift 2 ;;
    --plugin-root) PLUGIN_ROOT="$2"; shift 2 ;;
    --create-scope-dir) CREATE_SCOPE_DIR=1; shift ;;
    --prune-older) PRUNE_OLDER=1; shift ;;
    -h|--help) usage ;;
    -*) echo "error: unknown option: $1" >&2; usage ;;
    *)
      if [[ -z "$PATTERN" ]]; then
        PATTERN="$1"; shift
      else
        echo "error: unexpected argument: $1" >&2; usage
      fi
      ;;
  esac
done

if [[ -z "$PATTERN" ]]; then
  echo "error: <pattern> is required" >&2; usage
fi

_require_jq

RESOLVED_ROOT="$(_resolve_plugin_root)"

# Find matching tool scripts
mapfile -t MATCHES < <(find "$RESOLVED_ROOT/skills" -path "*/scripts/$PATTERN" -type f 2>/dev/null | sort)

if [[ ${#MATCHES[@]} -eq 0 ]]; then
  echo "error: no tools matching '$PATTERN' found under $RESOLVED_ROOT/skills/*/scripts/" >&2
  echo "hint: use 'nerf-git-*' to match a package, or check tool names in the nerf skills" >&2
  exit 1
fi

SETTINGS="$(_resolve_settings)"
_ensure_settings_file "$SETTINGS"

UPDATED=$(cat "$SETTINGS")

# Version scan: always-on; exits with error on newer entries, warns on older
# entries (or prunes them with --prune-older). Limited to the chosen scope.
_scan_stale_versions "$UPDATED" "nerfctl-grant-allow"
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
      | .permissions.deny = [.permissions.deny[] | select(. != $entry and . != $stale)]
      | .permissions.allow = [.permissions.allow[] | select(. != $stale)]
      | if (.permissions.allow | index($entry)) == null
        then .permissions.allow += [$entry]
        else .
        end
    ')
  echo "  Allowed: $TOOL_NAME"
  echo "    $ENTRY"
done

echo "$UPDATED" > "$SETTINGS"
echo ""
echo "Allowed ${#MATCHES[@]} tool(s) (scope: $SCOPE)"
