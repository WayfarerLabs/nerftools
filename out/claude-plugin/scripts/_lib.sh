# shellcheck shell=bash
# nerfctl shared helpers
#
# Sourced by the five nerfctl-grant-* scripts. Functions here use globals set
# by the calling script (SCOPE, PLUGIN_ROOT, CREATE_SCOPE_DIR, PRUNE_OLDER,
# RESET_OTHER_SCOPES, RESOLVED_ROOT). Each function documents what it expects.
#
# Do not invoke this file directly -- it has no shebang and no main body. The
# calling script should:
#
#   set -euo pipefail
#   _SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   # shellcheck source=_lib.sh
#   source "${_SCRIPT_DIR}/_lib.sh"
#
# Requires bash 4+ (matches the version pin on each calling script).

# -- jq availability ----------------------------------------------------------

_require_jq() {
  if ! command -v jq > /dev/null 2>&1; then
    echo "error: jq is required but not installed" >&2
    exit 1
  fi
}

# -- Settings file resolution -------------------------------------------------

# Map a scope name to its settings file path. Read-only -- does not create
# anything. Returns nonzero on unknown scope. Used by both the current-scope
# resolver and the other-scope handler.
_scope_path() {
  case "$1" in
    user)    echo "$HOME/.claude/settings.json" ;;
    project) echo ".claude/settings.json" ;;
    local)   echo ".claude/settings.local.json" ;;
    *) return 1 ;;
  esac
}

# Ensure .claude/ exists in cwd (project + local scopes both live there).
# Honors $CREATE_SCOPE_DIR; errors if missing and flag not set.
_ensure_claude_dir() {
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
}

# Resolve the settings file path for $SCOPE. For project/local this also
# ensures .claude/ exists (creating it if --create-scope-dir was passed).
_resolve_settings() {
  case "$SCOPE" in
    user)
      echo "$HOME/.claude/settings.json"
      ;;
    project)
      _ensure_claude_dir
      echo ".claude/settings.json"
      ;;
    local)
      _ensure_claude_dir
      echo ".claude/settings.local.json"
      ;;
    *) echo "error: unknown scope '$SCOPE' (use 'user', 'project', or 'local')" >&2; exit 1 ;;
  esac
}

_ensure_settings_file() {
  local file="$1"
  local dir
  dir=$(dirname "$file")
  [[ -d "$dir" ]] || mkdir -p "$dir"
  [[ -f "$file" ]] || echo '{}' > "$file"
}

# -- Plugin root resolution ---------------------------------------------------

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

# -- Version scan -------------------------------------------------------------

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

# -- Cross-scope handling -----------------------------------------------------

# Walk the two scopes that aren't $SCOPE and look for any entry referencing
# the tools we're about to touch (in either allow or deny). For each match:
#   - if RESET_OTHER_SCOPES=1: remove the entry from that scope's settings
#     file and print a "Reset from <scope> (<list>): <entry>" line.
#   - otherwise: print a warning and a hint to use --reset-other-scopes.
# Takes the list of script paths as positional args (e.g.
# `_handle_other_scopes "${MATCHES[@]}"`).
_handle_other_scopes() {
  local other_scopes=()
  case "$SCOPE" in
    user)    other_scopes=(project local) ;;
    project) other_scopes=(user local) ;;
    local)   other_scopes=(user project) ;;
  esac

  # Build the set of canonical entry strings we want to look for. Each tool
  # has both a current form (Bash(path:*)) and a legacy form (Bash(path)).
  local entries_to_check=()
  local _p
  for _p in "$@"; do
    entries_to_check+=("Bash(${_p}:*)" "Bash(${_p})")
  done
  [[ ${#entries_to_check[@]} -eq 0 ]] && return 0
  local entries_json
  entries_json=$(printf '%s\n' "${entries_to_check[@]}" | jq -R '.' | jq -s '.')

  local other_scope other_path warned_hint=0
  for other_scope in "${other_scopes[@]}"; do
    other_path=$(_scope_path "$other_scope") || continue
    # project/local both require .claude/ in cwd. If .claude/ isn't here,
    # there cannot be any entries for those scopes -- skip silently.
    if [[ "$other_scope" != "user" && ! -d ".claude" ]]; then
      continue
    fi
    [[ -f "$other_path" ]] || continue

    # Find entries from our set that are present in this scope's allow/deny.
    # Output one match per line: <list>\t<entry>
    local found
    found=$(jq -r --argjson entries "$entries_json" '
      [
        (.permissions.allow // [] | map({list: "allow", entry: .})),
        (.permissions.deny  // [] | map({list: "deny",  entry: .}))
      ]
      | flatten
      | map(select(.entry as $e | $entries | index($e) != null))
      | .[] | "\(.list)\t\(.entry)"
    ' < "$other_path")
    [[ -z "$found" ]] && continue

    if [[ "$RESET_OTHER_SCOPES" == "1" ]]; then
      local removed_entries_json
      removed_entries_json=$(printf '%s' "$found" | awk -F$'\t' '{print $2}' \
        | jq -R '.' | jq -s '.')
      local updated_other
      updated_other=$(jq --argjson stale "$removed_entries_json" '
        .permissions //= {}
        | .permissions.allow = ((.permissions.allow // []) - $stale)
        | .permissions.deny  = ((.permissions.deny  // []) - $stale)
      ' < "$other_path")
      echo "$updated_other" > "$other_path"
      while IFS=$'\t' read -r list entry; do
        [[ -z "$list" ]] && continue
        echo "  Reset from $other_scope ($list): $entry"
      done <<< "$found"
    else
      while IFS=$'\t' read -r list entry; do
        [[ -z "$list" ]] && continue
        echo "warning: entry exists in '$other_scope' scope ($list): $entry" >&2
      done <<< "$found"
      warned_hint=1
    fi
  done

  if (( warned_hint == 1 )); then
    echo "  hint: pass --reset-other-scopes to remove conflicting entries elsewhere" >&2
  fi
}
