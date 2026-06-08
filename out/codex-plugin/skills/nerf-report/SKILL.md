---
name: nerf-report
description: "Structured feedback loop for nerf tools (file bugs/bypass reasons/complaints/requests)"
targets: ["*"]
---

# nerf-report

These tools are available as scripts within this skill. Call them using the paths shown in each usage line.

These tools wrap the operator-facing feedback loop for nerf tools. Reports
are durable Markdown files under `~/.nerftools/<brand>/reports/`.

Three tools:
- `<prefix>report` writes a new report. Use when you hit a bug, need to
  bypass a guard (with reason), find UX friction, or want a feature.
- `<prefix>report-show` concatenates matching reports for the operator (or
  a triage subagent) to read. Requires a `<before>` cutoff timestamp.
- `<prefix>report-archive` moves processed reports to a `reviewed/`
  subdirectory so they don't show up next time. Same `<before>` cutoff.

The `<before>` cutoff filters strictly: only reports with timestamp <
`<before>` match. The cutoff must be a full ISO 8601 timestamp with an
explicit timezone designator (`Z` for UTC, or `±HH:MM` offset) and must
not be in the future. Bare dates and naive datetimes are intentionally
rejected -- a timestamp without a timezone is too ambiguous (UTC?
system local? both are plausible defaults), and a date-only cutoff
leads to off-by-one confusion. Offsets are normalized to UTC for
comparison via GNU `date -d` (or `gdate` on macOS via brew coreutils).

## nerf-report

File a structured report about a nerf tool (bug / bypass reason / complaint / feature request). Writes a Markdown file with auto-captured frontmatter to `~/.nerftools/<brand>/reports/`.

**Usage:** `scripts/nerf-report <kind> <tool> <body>`

**Arguments:**

- `<kind>` (required): Report kind. one of `bug`, `bypass`, `complaint`, `request`
- `<tool>` (required): Tool the report is about (e.g. nerf-az-repos-pr-edit), or "nerftools" for the package itself
- `<body>` (required): Free-form prose describing the issue/request. Quote it so it reaches the script as a single argument.

---

## nerf-report-show

Concatenate matching reports under `~/.nerftools/<brand>/reports/` for operator/subagent triage. Reports are filtered to those with timestamp strictly less than `<before>`. By default, the `reviewed/` subdirectory is skipped (those have already been triaged).

**Usage:** `scripts/nerf-report-show [--include-reviewed] [--kind <kind>] [--tool <tool>] <before>`

**Switches:**

- `--include-reviewed`: Also include reports that have already been moved to the `reviewed/` subdirectory

**Options:**

- `--kind` (optional): Only include reports of this kind. one of `bug`, `bypass`, `complaint`, `request`
- `--tool` (optional): Only include reports whose `tool` frontmatter contains this substring

**Arguments:**

- `<before>` (required): Full ISO 8601 cutoff with explicit timezone designator (Z for UTC, or ±HH:MM offset). Only reports with timestamp strictly < this match. Must not be in the future. Bare dates and naive datetimes are rejected -- pass `2026-05-23T00:00:00Z` or `2026-05-23T16:00:00-08:00`, not `2026-05-23`.. must match `^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+-][0-9]{2}:[0-9]{2})$`

---

## nerf-report-archive

Move matching reports to `~/.nerftools/<brand>/reports/reviewed/` so they don't show up in future `report-show` runs by default. Uses the same `<before>` semantics as `report-show` (strict less-than; not in future).

**Usage:** `scripts/nerf-report-archive [--kind <kind>] [--tool <tool>] <before>`

**Options:**

- `--kind` (optional): Only archive reports of this kind. one of `bug`, `bypass`, `complaint`, `request`
- `--tool` (optional): Only archive reports whose `tool` frontmatter contains this substring

**Arguments:**

- `<before>` (required): Full ISO 8601 cutoff with explicit timezone designator (Z for UTC, or ±HH:MM offset). Only reports with timestamp strictly < this are archived. Must not be in the future. Same format rules as `report-show`.. must match `^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+-][0-9]{2}:[0-9]{2})$`

---

_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? Use the `nerf-report` skill._
