---
name: nerf-git
description: "Git workflow tools for safe, scoped git operations"
targets: ["*"]
---

# nerf-git

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools wrap git operations with safety guardrails. Always stage changes
with git-add before committing. Commit subjects (git-commit, git-commit-amend)
and new local branch names (git-create-branch) must follow the Conventional
Commits type vocabulary (feat/, fix/, docs/, style/, refactor/, perf/, test/,
build/, ci/, chore/, revert/). Commit subject is a required positional capped
at 72 characters; longer explanations go in the optional second positional
"body" argument, which git renders as a separate paragraph. Tools that switch to or check out branches that
already exist (git-switch, git-branch-checkout-remote) do not enforce this
prefix. All remote operations take the remote name as the first positional
argument (typically origin). Every tool accepts an optional -C <directory>
to operate on a different repo subdirectory; the directory must be under
the workspace root. Several tools refuse operations on main or operations
that would require force-pushing already-pushed commits.

## nerf-git-add

Stage files or directories for commit.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-add [-C <directory>] <files...>`
**Maps to:** `git <directory> add <files>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<files...>` (required): Files or directories to stage

---

## nerf-git-commit

Create a git commit with a Conventional Commits subject and an optional body (changes must already be staged). Subject format: type[(scope)][!]: description. Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Subject must be at most 72 characters; put longer explanations in the body positional, which git renders as a separate paragraph. Must not contain Co-Authored-By trailers.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-commit [-C <directory>] <subject> [<body>]`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<subject>` (required): Commit subject line: type[(scope)][!]: description (max 72 chars). must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9._,-]+\))?!?: .+`
- `<body>` (optional): Optional commit body (rendered as a separate paragraph). Use for longer explanations.

---

## nerf-git-commit-amend

Amend the most recent commit with a new Conventional Commits subject and an optional body. Fails if the commit has already been pushed to any remote. Use only to fix the last local commit. Subject must be at most 72 characters; put longer explanations in the body positional. Must not contain Co-Authored-By trailers.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-commit-amend [-C <directory>] <subject> [<body>]`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<subject>` (required): Commit subject line: type[(scope)][!]: description (max 72 chars). must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9._,-]+\))?!?: .+`
- `<body>` (optional): Optional commit body (rendered as a separate paragraph). Use for longer explanations.

---

## nerf-git-revert

Create a new commit that undoes a previous commit. Does not rewrite history -- safe to use on pushed commits.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-revert [-C <directory>] <ref>`
**Maps to:** `git <directory> revert --no-edit <ref>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<ref>` (required): Commit to revert (e.g. HEAD, a commit SHA, or HEAD~2)

---

## nerf-git-reset-hard-last

Drop the most recent commit entirely, discarding its changes. Fails if the commit has already been pushed to any remote.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-reset-hard-last [-C <directory>]`
**Maps to:** `git <directory> reset --hard HEAD~1`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-fetch

Fetch all branches and tags from a remote.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-fetch [-C <directory>] <remote>`
**Maps to:** `git <directory> fetch <remote> --tags`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`

---

## nerf-git-ls-remote

List references (branches and tags) on a remote without fetching them locally. With no pattern, all refs are returned (can be large on busy repos). Optional <pattern> filters refs (e.g. `refs/tags/v1.*` or `feat/*`). Use --tags or --heads to restrict the listing to one ref type.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-ls-remote [--tags] [--heads] [-C <directory>] <remote> [<pattern>]`
**Maps to:** `git <directory> ls-remote <tags> <heads> <remote> <pattern>`

**Switches:**

- `--tags`: List only tag refs
- `--heads`: List only branch refs

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`
- `<pattern>` (optional): Optional ref pattern to filter results (e.g. refs/tags/v1.*, feat/*)

---

## nerf-git-pull

Pull the current branch from a remote.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-pull [-C <directory>] <remote>`
**Maps to:** `git <directory> pull <remote>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`

---

## nerf-git-push-main

Push the local main branch to a remote including annotated tags (no force push). Use only when the local main branch is ready to publish.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-push-main [-C <directory>] <remote>`
**Maps to:** `git <directory> push --follow-tags <remote> main`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`

---

## nerf-git-push-branch

Push the current branch to a remote including annotated tags (no force push) and set upstream tracking, so subsequent git-pull works without an extra ref. Fails if in detached HEAD state or on main. Do not use on main -- use git-push-main instead.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-push-branch [-C <directory>] <remote>`
**Maps to:** `git <directory> push --follow-tags --set-upstream <remote> HEAD`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`

---

## nerf-git-tag-push

Push a single tag to a remote. Does not allow force-pushing; tag is rejected by the remote if it already exists upstream.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-tag-push [-C <directory>] <remote> <tag_name>`
**Maps to:** `git <directory> push <remote> <tag_name>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`
- `<tag_name>` (required): Tag name to push. must match `^[a-zA-Z0-9_./-]+$`

---

## nerf-git-log

Show commit history. Accepts any combination of git-log flags, refs, and pathspecs (e.g. --oneline, -n 20, main..HEAD, --stat, -- src/). External diff and textconv drivers are disabled so the tool cannot be hijacked via gitconfig. With no extra args, prints the full history -- pass `-n <count>` (or `--oneline -20`) to bound output.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-log [-C <directory>] [<args...>]`
**Maps to:** `git <directory> log --no-ext-diff --no-textconv <args>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<args...>` (optional): Flags, refs, and paths forwarded to `git log` (e.g. --oneline, -n 20, main..HEAD, -- src/). --output / --output=<path> is also rejected (would write the log to an arbitrary file, violating `write: none`).. not `--ext-diff`, `--textconv`

---

## nerf-git-tag

Create a new annotated git tag at HEAD, or at a specific commit-ish if <ref> is given. Tag names may include `/` so subdirectory-style schemes (e.g. tf/aks/cluster/v2.0.0) are accepted. Fails if the tag already exists. Does not push; use git-tag-push afterward. No force, delete, or other destructive operations.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-tag [-C <directory>] <tag> [<ref>]`
**Maps to:** `git <directory> tag -a <tag> -m <tag> <ref>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<tag>` (required): Tag name to create (e.g. v1.2.3 or tf/aks/cluster/v2.0.0). must match `^[a-zA-Z0-9._/-]+$`
- `<ref>` (optional): Commit-ish to tag (default HEAD). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./~^-]*$`

---

## nerf-git-status

Show the working-tree status in short porcelain format.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-status [-C <directory>]`
**Maps to:** `git <directory> status --porcelain=v1`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-diff

Show diffs. Accepts any combination of git-diff flags, refs, and pathspecs (e.g. --staged, --stat, main..HEAD, main...HEAD, src/). With no extra args, shows unstaged working-tree changes. External diff and textconv drivers are disabled so the tool cannot be hijacked via gitconfig.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-diff [-C <directory>] [<args...>]`
**Maps to:** `git <directory> diff --no-ext-diff --no-textconv <args>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<args...>` (optional): Flags, refs, and paths forwarded to `git diff` (e.g. --staged, --stat, main..HEAD, src/). All positional arguments must resolve inside the workspace (paths outside cwd are rejected, which also blocks `git diff` from auto-engaging --no-index mode on two out-of-workspace paths). --output / --output=<path> is also rejected (would write the diff to an arbitrary file, violating `write: none`).. not `--ext-diff`, `--textconv`, `--no-index`

---

## nerf-git-branch-list-local

List local branches with the current-branch marker, short SHA, upstream tracking, and most-recent commit subject.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-branch-list-local [-C <directory>]`
**Maps to:** `git <directory> branch --list -vv`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-branch-list-remote

List remote-tracking branches with short SHA and most-recent commit subject. Run git-fetch first to refresh.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-branch-list-remote [-C <directory>]`
**Maps to:** `git <directory> branch --remotes -vv`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-switch

Switch to an existing branch. If no local branch with this name exists but a unique remote (typically origin) has one, git auto-creates a tracking branch. The auto-track path skips the Conventional-Commits prefix guard because the branch already exists upstream.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-switch [-C <directory>] <name>`
**Maps to:** `git <directory> switch <name>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<name>` (required): Branch name to switch to. must match `^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$`

---

## nerf-git-create-branch

Create a new branch from the current HEAD and switch to it. The name must start with a Conventional Commits type prefix (feat/, fix/, docs/, style/, refactor/, perf/, test/, build/, ci/, chore/, revert/) so branch names compose with the Conventional-Commits-formatted commit messages enforced by git-commit.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-create-branch [-C <directory>] <name>`
**Maps to:** `git <directory> switch -c <name>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<name>` (required): New branch name (must start with feat/, fix/, docs/, etc.). must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)/[a-zA-Z0-9._/-]+$`

---

## nerf-git-branch-checkout-remote

Create a local branch that explicitly tracks <remote>/<name>. Use git-switch for the simpler auto-track behavior; reach for this tool when you have multiple remotes with the same branch name (auto-track refuses the ambiguity) or want to be explicit about which remote you are tracking. Skips the Conventional-Commits prefix guard because the branch already exists upstream.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-branch-checkout-remote [-C <directory>] <remote> <name>`
**Maps to:** `git <directory> checkout --track <remote>/<name>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`
- `<name>` (required): Branch name (must exist as <remote>/<name>). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$`

---

## nerf-git-branch-delete-merged

Delete a local branch using "git branch -d", which refuses to delete a branch that has unmerged commits. Cannot delete main or the currently-checked-out branch.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-branch-delete-merged [-C <directory>] <name>`
**Maps to:** `git <directory> branch --delete <name>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<name>` (required): Branch name to delete (must be fully merged). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$`

---

## nerf-git-rebase-unpushed

Rebase the current branch onto a target ref. Refuses if the current branch is main or if any commit in target..HEAD is already reachable from a remote (which would require force-pushing). The intended use is replaying still-local commits onto a fresher upstream (e.g. git-rebase-unpushed origin/main).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-rebase-unpushed [-C <directory>] <target>`
**Maps to:** `git <directory> rebase <target>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<target>` (required): Ref to rebase onto (e.g. origin/main, main). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./~^-]*$`

---

## nerf-git-rebase-continue

Resume a rebase after conflicts have been resolved and staged. Pairs with git-rebase-unpushed when the rebase stops with conflicts.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-rebase-continue [-C <directory>]`
**Maps to:** `git <directory> rebase --continue`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-rebase-abort

Abort an in-progress rebase and restore the branch to the state before the rebase began.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-rebase-abort [-C <directory>]`
**Maps to:** `git <directory> rebase --abort`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-reset-unpushed

Reset HEAD to a target ref. Default mode is mixed (changes left unstaged); pass --soft to keep them staged. Refuses if the current branch is main or if any commit in target..HEAD is already reachable from a remote (which would orphan pushed commits). Hard reset is intentionally not exposed -- use git-reset-hard-last when you specifically want to discard the last commit.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-reset-unpushed [--soft|-s] [-C <directory>] <target>`
**Maps to:** `git <directory> reset <soft> <target>`

**Switches:**

- `--soft, -s`: Soft reset -- keep changes staged (default is mixed; changes unstaged)

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<target>` (required): Ref to reset to (e.g. HEAD~1, origin/main). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./~^-]*$`

---

## nerf-git-restore-staged

Unstage one or more files (move them from the index back to the working tree). Inverse of git-add. Does not modify working-tree contents.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-restore-staged [-C <directory>] <files...>`
**Maps to:** `git <directory> restore --staged <files>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<files...>` (required): Files or directories to unstage

---

## nerf-git-restore-worktree

Discard unstaged changes in the named files or pathspecs, reverting them to their staged content, or to HEAD if there are no staged changes for that path. DESTRUCTIVE on unstaged working-tree edits. Untracked files are not affected. Does not modify the index -- use git-restore-staged to unstage first.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-restore-worktree [-C <directory>] <files...>`
**Maps to:** `git <directory> restore <files>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<files...>` (required): Files, directories, or pathspecs to discard changes in

---

## nerf-git-rm

Remove tracked files from the working tree and the index. DESTRUCTIVE on the working tree (file is deleted). Does not commit.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-rm [-C <directory>] <files...>`
**Maps to:** `git <directory> rm <files>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<files...>` (required): Files to remove (must be tracked)

---

## nerf-git-mv

Rename or move a tracked file. Source must exist; destination must be inside the workspace.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-mv [-C <directory>] <source> <destination>`
**Maps to:** `git <directory> mv <source> <destination>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<source>` (required): File to move (must exist and be tracked)
- `<destination>` (required): New path (must be inside the workspace)

---

## nerf-git-show

Show a commit's message and unified diff. Accepts any commit-ish (SHA, HEAD, HEAD~1, ref name). External diff and textconv drivers are disabled. Defaults to HEAD if no ref is given.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-show [-C <directory>] [<ref>]`
**Maps to:** `git <directory> show --no-ext-diff --no-textconv <ref>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<ref>` (optional): Commit-ish to show (default HEAD). must match `^[a-zA-Z0-9_][a-zA-Z0-9_./~^-]*$`

---

## nerf-git-blame

Show line-by-line authorship for a file. Read-only.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-blame [-C <directory>] <file>`
**Maps to:** `git <directory> blame <file>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<file>` (required): File to blame

---

## nerf-git-reflog

Show the last 50 reflog entries -- a record of where HEAD and branch tips have pointed locally. Useful for recovering lost commits or undoing unintended branch movements.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-reflog [-C <directory>]`
**Maps to:** `git <directory> reflog -n 50`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-remote-list

List configured remotes with their fetch and push URLs.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-remote-list [-C <directory>]`
**Maps to:** `git <directory> remote -v`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-branch-current

Show the name of the currently checked-out branch.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-branch-current [-C <directory>]`
**Maps to:** `git <directory> branch --show-current`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-cherry-pick

Apply a single commit's changes onto the current branch as a new commit. Refuses on main and on detached HEAD. On conflicts, resolve manually and use the underlying `git cherry-pick --continue` / `--abort` (not yet exposed via nerf).

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-cherry-pick [-C <directory>] <ref>`
**Maps to:** `git <directory> cherry-pick <ref>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<ref>` (required): Commit-ish to cherry-pick. must match `^[a-zA-Z0-9_][a-zA-Z0-9_./~^-]*$`

---

## nerf-git-merge-no-ff

Merge a branch into the current branch with a merge commit (--no-ff, --no-edit). Refuses if the current branch is main; merges into main should go through a PR. Conflicts must be resolved manually.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-merge-no-ff [-C <directory>] <branch>`
**Maps to:** `git <directory> merge --no-ff --no-edit <branch>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<branch>` (required): Branch (or commit-ish) to merge into the current branch. must match `^[a-zA-Z0-9_][a-zA-Z0-9_./~^-]*$`

---

## nerf-git-stash-push

Save staged and unstaged changes to the stash and revert the working tree to HEAD. Untracked files are not stashed. Use git-stash-pop to restore.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-stash-push [-C <directory>] [-m <message>]`
**Maps to:** `git <directory> stash push <message>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)
- `-m` (optional): Description of the stash

---

## nerf-git-stash-pop

Pop a saved stash (default the most recent) and reapply its changes to the working tree. DESTRUCTIVE on conflicts -- the stash entry is removed from the stash list even if conflicts arise during reapply.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-stash-pop [-C <directory>] [<ref>]`
**Maps to:** `git <directory> stash pop <ref>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<ref>` (optional): Stash ref to pop (e.g. stash@{1}, default stash@{0}). must match `^stash@\{[0-9]+\}$`

---

## nerf-git-stash-list

List saved stashes with their descriptions.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-stash-list [-C <directory>]`
**Maps to:** `git <directory> stash list`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-stash-drop

Drop a saved stash without applying it.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-stash-drop [-C <directory>] <ref>`
**Maps to:** `git <directory> stash drop <ref>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<ref>` (required): Stash ref to drop (e.g. stash@{0}). must match `^stash@\{[0-9]+\}$`

---

## nerf-git-submodule-status

Show the status of each submodule (current SHA, configured path, and describe output). Read-only.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-submodule-status [-C <directory>]`
**Maps to:** `git <directory> submodule status`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

_Hit a bug, complaint, bypass-worthy guardrail, or want a feature? Use the `nerf-report` skill._
