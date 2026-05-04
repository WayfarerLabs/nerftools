---
name: nerf-gh
description: "GitHub CLI tools for pull requests, issues, and workflow runs"
targets: ["*"]
---

# nerf-gh

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools wrap the GitHub CLI (gh) for safe interaction with pull
requests, issues, and workflow runs. The repository is auto-detected
from the current git remote.

A pull request has four distinct comment surfaces, each with its own
tool:
- "thread comments" -- top-level conversation in the main PR view.
  Read via gh-pr-thread-comments, written via gh-pr-thread-comment.
- "reviews" -- the high-level Approved / Changes requested /
  Commented wrappers, each with a body summary. List the latest
  via gh-pr-reviews.
- "review comments" -- inline comments scoped to one review. Fetch
  with gh-pr-review-comments using a review id from gh-pr-reviews.
- "inline comments" -- all inline review comments across every
  review on the PR. Use gh-pr-inline-comments when you want a
  flat list of all line-level comments without iterating reviews.

Note: inline-comment thread resolution state (resolved /
unresolved, set via the "Resolve conversation" button in the UI)
is a GraphQL-only field on the GitHub API and is not exposed by
this manifest. Use the GitHub UI to verify resolution state.

## nerf-gh-pr-list

List open pull requests in the current repository.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-list [--web|-w] [--state|-s <state>] [--author <author>] [--base|-B <base>] [--limit|-L <limit>]`
**Maps to:** `gh pr list <web> <state> <author> <base> <limit>`

**Switches:**

- `--web, -w`: Open the list in the browser

**Options:**

- `--state|-s` (optional): Filter by state (default: open). one of `open`, `closed`, `merged`, `all`
- `--author` (optional): Filter by author (GitHub username or @me)
- `--base|-B` (optional): Filter by base branch
- `--limit|-L` (optional): Maximum number of PRs to list (default 30). must match `^[0-9]+$`

---

## nerf-gh-pr-view

View full details of a pull request as JSON, including metadata, comments, reviews, and file list.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-view <pr>`
**Maps to:** `gh pr view <pr> --json title,body,state,author,baseRefName,headRefName,comments,reviews,reviewDecision,labels,isDraft,additions,deletions,files,mergedAt,mergedBy`

**Arguments:**

- `<pr>` (required): PR number, URL, or branch name

---

## nerf-gh-pr-diff

Show the diff for a pull request.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-diff <pr>`
**Maps to:** `gh pr diff <pr>`

**Arguments:**

- `<pr>` (required): PR number, URL, or branch name

---

## nerf-gh-pr-thread-comments

List top-level conversation comments on a pull request (the issue-style comments shown in the main PR thread, NOT inline review comments). Returns the raw GitHub API response; pipe through jq to project the fields you want.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-thread-comments <pr>`
**Maps to:** `gh api --paginate --slurp repos/{owner}/{repo}/issues/<pr>/comments`

**Arguments:**

- `<pr>` (required): PR number. must match `^[0-9]+$`

---

## nerf-gh-pr-reviews

List reviews on a pull request, latest first. Each entry includes id (numeric), author, state, commit (short SHA), submitted_at, and body (the reviewer's summary text). Pass an entry's id to gh-pr-review-comments to fetch the inline comments for that specific review.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-reviews [--limit|-L <limit>] <pr>`

**Options:**

- `--limit|-L` (optional): Maximum number of reviews to return (default 10, latest first). must match `^[1-9][0-9]*$`

**Arguments:**

- `<pr>` (required): PR number. must match `^[0-9]+$`

---

## nerf-gh-pr-review-comments

List inline review comments for a single review (by numeric review ID). Use gh-pr-reviews to find review IDs. Returns the raw GitHub API response; pipe through jq to project the fields you want.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-review-comments <pr> <review_id>`
**Maps to:** `gh api --paginate --slurp repos/{owner}/{repo}/pulls/<pr>/reviews/<review_id>/comments`

**Arguments:**

- `<pr>` (required): PR number. must match `^[0-9]+$`
- `<review_id>` (required): Numeric review ID (from gh-pr-reviews). must match `^[0-9]+$`

---

## nerf-gh-pr-inline-comments

List ALL inline review comments on a pull request, across all reviews. Each comment is tied to a specific line of code. Use gh-pr-review-comments instead when you have a specific review ID and only want that review's comments. Returns the raw GitHub API response; pipe through jq to project the fields you want.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-inline-comments <pr>`
**Maps to:** `gh api --paginate --slurp repos/{owner}/{repo}/pulls/<pr>/comments`

**Arguments:**

- `<pr>` (required): PR number. must match `^[0-9]+$`

---

## nerf-gh-pr-create

Create a pull request from the current branch. Pushes the branch if needed.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-create [--draft|-d] [--body|-b <body>] [--base|-B <base>] [--reviewer|-r <reviewer>] <title>`
**Maps to:** `gh pr create <draft> --title <title> <body> <base> <reviewer>`

**Switches:**

- `--draft, -d`: Create as a draft PR

**Options:**

- `--body|-b` (optional): PR body/description
- `--base|-B` (optional): Base branch (default is the repo default branch)
- `--reviewer|-r` (optional): Request review from this user

**Arguments:**

- `<title>` (required): PR title

---

## nerf-gh-pr-thread-comment

Add a top-level conversation comment to a pull request (the issue-style comments shown in the main PR thread). For inline review comments, see gh-pr-review-comments (one review) or gh-pr-inline-comments (across all reviews).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-pr-thread-comment <pr> <body>`
**Maps to:** `gh pr comment <pr> --body <body>`

**Arguments:**

- `<pr>` (required): PR number, URL, or branch name
- `<body>` (required): Comment text

---

## nerf-gh-issue-list

List open issues in the current repository.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-issue-list [--state|-s <state>] [--assignee|-a <assignee>] [--label|-l <label>] [--limit|-L <limit>]`
**Maps to:** `gh issue list <state> <assignee> <label> <limit>`

**Options:**

- `--state|-s` (optional): Filter by state (default: open). one of `open`, `closed`, `all`
- `--assignee|-a` (optional): Filter by assignee (GitHub username or @me)
- `--label|-l` (optional): Filter by label
- `--limit|-L` (optional): Maximum number of issues to list (default 30). must match `^[0-9]+$`

---

## nerf-gh-issue-view

View full details of an issue as JSON, including metadata, comments, and labels.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-issue-view <issue>`
**Maps to:** `gh issue view <issue> --json title,body,state,author,comments,labels,assignees,milestone,createdAt,updatedAt,closedAt`

**Arguments:**

- `<issue>` (required): Issue number or URL

---

## nerf-gh-issue-create

Create a new issue.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-issue-create [--body|-b <body>] [--label|-l <label>] [--assignee|-a <assignee>] <title>`
**Maps to:** `gh issue create --title <title> <body> <label> <assignee>`

**Options:**

- `--body|-b` (optional): Issue body/description
- `--label|-l` (optional): Label to add
- `--assignee|-a` (optional): User to assign

**Arguments:**

- `<title>` (required): Issue title

---

## nerf-gh-issue-comment

Add a comment to an issue.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-issue-comment <issue> <body>`
**Maps to:** `gh issue comment <issue> --body <body>`

**Arguments:**

- `<issue>` (required): Issue number or URL
- `<body>` (required): Comment text

---

## nerf-gh-run-list

List recent workflow runs.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-run-list [--workflow|-w <workflow>] [--branch|-b <branch>] [--status|-s <status>] [--limit|-L <limit>]`
**Maps to:** `gh run list <workflow> <branch> <status> <limit>`

**Options:**

- `--workflow|-w` (optional): Filter by workflow name or filename
- `--branch|-b` (optional): Filter by branch
- `--status|-s` (optional): Filter by status. one of `queued`, `in_progress`, `completed`, `waiting`, `requested`, `action_required`, `cancelled`, `failure`, `neutral`, `skipped`, `stale`, `startup_failure`, `success`, `timed_out`
- `--limit|-L` (optional): Maximum number of runs to list (default 20). must match `^[0-9]+$`

---

## nerf-gh-run-view

View details of a workflow run.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-gh/scripts/nerf-gh-run-view <run_id>`
**Maps to:** `gh run view <run_id>`

**Arguments:**

- `<run_id>` (required): Workflow run ID. must match `^[0-9]+$`

---
