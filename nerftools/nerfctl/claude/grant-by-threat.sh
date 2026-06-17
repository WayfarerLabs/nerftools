#!/usr/bin/env bash
# nerfctl-grant-by-threat -- Allow/deny nerf tools by threat profile
# This is a control-plane tool for operators, not for agents.

set -euo pipefail

if [[ "${BASH_VERSINFO[0]:-0}" -lt 4 ]]; then
  echo "error: nerfctl-grant-by-threat requires bash 4+. Found bash ${BASH_VERSION:-unknown}" >&2
  echo "  hint: on macOS, install a newer bash via 'brew install bash'" >&2
  exit 1
fi

# Shared helpers (must come after set -euo and the bash version check).
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "${_SCRIPT_DIR}/_lib.sh"

SCOPE=""
PLUGIN_ROOT=""
READ_CEILING=""
WRITE_CEILING=""
FILTER="*"
OUTSIDE="deny"
CREATE_SCOPE_DIR=0
PRUNE_OLDER=0
RESET_OTHER_SCOPES=0

THREAT_ORDER="none workspace machine remote admin"

usage() {
  cat >&2 <<'EOF'
Usage: nerfctl-grant-by-threat <scope> --read <level> --write <level>
       [--filter <glob>] [--outside deny|reset]
       [--plugin-root <path>] [--create-scope-dir]
       [--prune-older] [--reset-other-scopes]

  <scope>                Settings scope: user, project, or local (required)
  --read <level>         Read ceiling (none|workspace|machine|remote|admin)
  --write <level>        Write ceiling (none|workspace|machine|remote|admin)
  --filter <glob>        Only affect tools matching this name pattern (default: *)
  --outside deny|reset   Action for tools outside the box (default: deny)
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
narrow the current --filter is.

Allows all tools within the threat box (read <= ceiling AND write <= ceiling).
Tools outside the box are denied or reset based on --outside.

The plugin root is auto-detected from CLAUDE_PLUGIN_ROOT or the script's
own location. Use --plugin-root only for testing.

Requires jq.
EOF
  exit 1
}

# Threat ranking is by-threat-specific; not in _lib.sh.
_threat_rank() {
  local level="$1"
  local i=0
  for t in $THREAT_ORDER; do
    if [[ "$t" == "$level" ]]; then
      echo "$i"
      return
    fi
    i=$((i + 1))
  done
  echo "error: invalid threat level '$level'" >&2
  exit 1
}

_valid_threat() {
  local level="$1"
  for t in $THREAT_ORDER; do
    if [[ "$t" == "$level" ]]; then
      return 0
    fi
  done
  return 1
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --read) READ_CEILING="$2"; shift 2 ;;
    --write) WRITE_CEILING="$2"; shift 2 ;;
    --filter) FILTER="$2"; shift 2 ;;
    --outside) OUTSIDE="$2"; shift 2 ;;
    --plugin-root) PLUGIN_ROOT="$2"; shift 2 ;;
    --create-scope-dir) CREATE_SCOPE_DIR=1; shift ;;
    --prune-older) PRUNE_OLDER=1; shift ;;
    --reset-other-scopes) RESET_OTHER_SCOPES=1; shift ;;
    -h|--help) usage ;;
    -*)  echo "error: unknown option: $1" >&2; usage ;;
    *)   POSITIONAL+=("$1"); shift ;;
  esac
done

if [[ ${#POSITIONAL[@]} -ne 1 ]]; then
  echo "error: expected <scope>, got ${#POSITIONAL[@]} positional argument(s)" >&2
  usage
fi
SCOPE="${POSITIONAL[0]}"

case "$SCOPE" in
  user|project|local) ;;
  *) echo "error: <scope> must be 'user', 'project', or 'local' (got '$SCOPE')" >&2; usage ;;
esac

if [[ -z "$READ_CEILING" ]]; then
  echo "error: --read is required" >&2; usage
fi
if [[ -z "$WRITE_CEILING" ]]; then
  echo "error: --write is required" >&2; usage
fi
if ! _valid_threat "$READ_CEILING"; then
  echo "error: invalid read level '$READ_CEILING' (use: none, workspace, machine, remote, admin)" >&2
  exit 1
fi
if ! _valid_threat "$WRITE_CEILING"; then
  echo "error: invalid write level '$WRITE_CEILING' (use: none, workspace, machine, remote, admin)" >&2
  exit 1
fi
if [[ "$OUTSIDE" != "deny" && "$OUTSIDE" != "reset" ]]; then
  echo "error: --outside must be 'deny' or 'reset'" >&2; exit 1
fi

_require_jq

RESOLVED_ROOT="$(_resolve_plugin_root)"

READ_RANK=$(_threat_rank "$READ_CEILING")
WRITE_RANK=$(_threat_rank "$WRITE_CEILING")

# Find tools with embedded threat metadata
declare -a TOOL_PATHS=()
declare -A TOOL_READ=()
declare -A TOOL_WRITE=()

while IFS= read -r script_path; do
  [[ -z "$script_path" ]] && continue
  tool_name=$(basename "$script_path")

  # Apply filter
  case "$tool_name" in
    $FILTER) ;;
    *) continue ;;
  esac

  # Parse threat metadata from script header
  read_level=""
  write_level=""
  while IFS= read -r line; do
    case "$line" in
      "# nerf:threat:read="*) read_level="${line#*=}" ;;
      "# nerf:threat:write="*) write_level="${line#*=}" ;;
      "set -"*) break ;;
    esac
  done < "$script_path"

  if [[ -z "$read_level" || -z "$write_level" ]]; then
    continue  # skip tools without threat metadata
  fi

  TOOL_PATHS+=("$script_path")
  TOOL_READ["$script_path"]="$read_level"
  TOOL_WRITE["$script_path"]="$write_level"
done < <(find "$RESOLVED_ROOT/skills" -path "*/scripts/*" -type f 2>/dev/null | sort)

if [[ ${#TOOL_PATHS[@]} -eq 0 ]]; then
  echo "No tools found matching filter '$FILTER' under $RESOLVED_ROOT/skills/*/scripts/"
  exit 0
fi

SETTINGS="$(_resolve_settings)"
_ensure_settings_file "$SETTINGS"

UPDATED=$(cat "$SETTINGS")

_handle_other_scopes "${TOOL_PATHS[@]}"

_scan_stale_versions "$UPDATED" "nerfctl-grant-by-threat"
if (( STALE_COUNT > 0 )); then
  if [[ "$PRUNE_OLDER" == "1" ]]; then
    UPDATED=$(_remove_stale_entries "$UPDATED")
    echo "Pruned $STALE_COUNT stale entr$( ((STALE_COUNT == 1)) && echo "y" || echo "ies") from older plugin versions"
  else
    echo "warning: $STALE_COUNT permission entr$( ((STALE_COUNT == 1)) && echo "y" || echo "ies") reference older versions of this plugin (pass --prune-older to remove)" >&2
  fi
fi

ALLOWED_COUNT=0
OUTSIDE_COUNT=0

for SCRIPT_PATH in "${TOOL_PATHS[@]}"; do
  TOOL_NAME=$(basename "$SCRIPT_PATH")
  ENTRY="Bash($SCRIPT_PATH:*)"
  STALE_ENTRY="Bash($SCRIPT_PATH)"

  tool_read_rank=$(_threat_rank "${TOOL_READ[$SCRIPT_PATH]}")
  tool_write_rank=$(_threat_rank "${TOOL_WRITE[$SCRIPT_PATH]}")

  # Check current status for annotations (check both new and stale entry forms)
  was=""
  if printf '%s' "$UPDATED" | jq -e --arg e "$ENTRY" --arg s "$STALE_ENTRY" \
    '(.permissions.allow // [] | (index($e) != null or index($s) != null))' > /dev/null 2>&1; then
    was="allowed"
  elif printf '%s' "$UPDATED" | jq -e --arg e "$ENTRY" --arg s "$STALE_ENTRY" \
    '(.permissions.deny // [] | (index($e) != null or index($s) != null))' > /dev/null 2>&1; then
    was="denied"
  fi

  if [[ $tool_read_rank -le $READ_RANK && $tool_write_rank -le $WRITE_RANK ]]; then
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
    annotation=""
    [[ -n "$was" && "$was" != "allowed" ]] && annotation=" (was: $was)"
    echo "  Allowed: $TOOL_NAME  read:${TOOL_READ[$SCRIPT_PATH]}  write:${TOOL_WRITE[$SCRIPT_PATH]}$annotation"
    ALLOWED_COUNT=$((ALLOWED_COUNT + 1))
  else
    if [[ "$OUTSIDE" == "deny" ]]; then
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
      annotation=""
      [[ -n "$was" && "$was" != "denied" ]] && annotation=" (was: $was)"
      echo "  Denied:  $TOOL_NAME  read:${TOOL_READ[$SCRIPT_PATH]}  write:${TOOL_WRITE[$SCRIPT_PATH]}$annotation"
    else
      UPDATED=$(printf '%s' "$UPDATED" | jq \
        --arg entry "$ENTRY" \
        --arg stale "$STALE_ENTRY" \
        '
          .permissions //= {}
          | .permissions.allow //= []
          | .permissions.deny //= []
          | .permissions.allow = [.permissions.allow[] | select(. != $entry and . != $stale)]
          | .permissions.deny = [.permissions.deny[] | select(. != $entry and . != $stale)]
        ')
      annotation=""
      [[ -n "$was" ]] && annotation=" (was: $was)"
      echo "  Reset:   $TOOL_NAME  read:${TOOL_READ[$SCRIPT_PATH]}  write:${TOOL_WRITE[$SCRIPT_PATH]}$annotation"
    fi
    OUTSIDE_COUNT=$((OUTSIDE_COUNT + 1))
  fi
done

echo "$UPDATED" > "$SETTINGS"
echo ""
echo "Allowed $ALLOWED_COUNT tool(s), ${OUTSIDE}ed $OUTSIDE_COUNT tool(s) (scope: $SCOPE)"
