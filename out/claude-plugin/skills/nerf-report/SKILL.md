---
name: nerf-report
description: "Structured feedback loop for nerf tools (file bugs/bypass reasons/complaints/requests)"
targets: ["*"]
---

# nerf-report

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

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
`<before>` match. The cutoff itself must not be in the future. This forces
intentional time-window selection and prevents in-flight reports (those
just being written) from being accidentally pulled in.

## nerf-report

File a structured report about a nerf tool (bug / bypass reason / complaint / feature request). Writes a Markdown file with auto-captured frontmatter to `~/.nerftools/<brand>/reports/`.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report <kind> <tool> <body>`

**Arguments:**

- `<kind>` (required): Report kind. one of `bug`, `bypass`, `complaint`, `request`
- `<tool>` (required): Tool the report is about (e.g. nerf-az-repos-pr-edit), or "nerftools" for the package itself
- `<body>` (required): Free-form prose describing the issue/request. Quote it so it reaches the script as a single argument.

---

## nerf-report-show

Concatenate matching reports under `~/.nerftools/<brand>/reports/` for operator/subagent triage. Reports are filtered to those with timestamp strictly less than `<before>`. By default, the `reviewed/` subdirectory is skipped (those have already been triaged).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report-show [--include-reviewed] [--kind <kind>] [--tool <tool>] <before>`

**Switches:**

- `--include-reviewed`: Also include reports that have already been moved to the `reviewed/` subdirectory

**Options:**

- `--kind` (optional): Only include reports of this kind. one of `bug`, `bypass`, `complaint`, `request`
- `--tool` (optional): Only include reports whose `tool` frontmatter contains this substring

**Arguments:**

- `<before>` (required): ISO 8601 UTC cutoff; only reports with timestamp strictly < this match. Must not be in the future. Accepts `YYYY-MM-DD` (expands to `T00:00:00Z`) or `YYYY-MM-DDTHH:MM:SSZ`.. must match `^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)?$`

---

## nerf-report-archive

Move matching reports to `~/.nerftools/<brand>/reports/reviewed/` so they don't show up in future `report-show` runs by default. Uses the same `<before>` semantics as `report-show` (strict less-than; not in future).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-report/scripts/nerf-report-archive [--kind <kind>] [--tool <tool>] <before>`

**Options:**

- `--kind` (optional): Only archive reports of this kind. one of `bug`, `bypass`, `complaint`, `request`
- `--tool` (optional): Only archive reports whose `tool` frontmatter contains this substring

**Arguments:**

- `<before>` (required): ISO 8601 UTC cutoff; only reports with timestamp strictly < this are archived. Must not be in the future.. must match `^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)?$`

---

_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? Use the `nerf-report` skill._
