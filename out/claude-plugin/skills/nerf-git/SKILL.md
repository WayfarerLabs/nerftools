---
name: nerf-git
description: "Git workflow tools for safe, scoped git operations"
targets: ["*"]
---

# nerf-git

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools wrap git operations with safety guardrails. Always stage changes
with git-add before committing. Commit messages (git-commit) and new local
branch names (git-create-branch) must follow the Conventional Commits type
vocabulary (feat/, fix/, docs/, style/, refactor/, perf/, test/, build/,
ci/, chore/, revert/). Tools that switch to or check out branches that
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

Create a git commit with a Conventional Commits message (changes must already be staged). Format: type[(scope)][!]: description. Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Must not contain Co-Authored-By trailers.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-commit [-C <directory>] <message>`
**Maps to:** `git <directory> commit -m <message>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<message>` (required): Commit message: type[(scope)][!]: description. must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9._-]+\))?!?: .+`

---

## nerf-git-commit-amend

Amend the most recent commit with a new message. Fails if the commit has already been pushed to any remote. Use only to fix the last local commit.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-commit-amend [-C <directory>] <message>`
**Maps to:** `git <directory> commit --amend -m <message>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<message>` (required): Commit message: type[(scope)][!]: description. must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9._-]+\))?!?: .+`

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

Push the current branch to a remote including annotated tags (no force push). Fails if in detached HEAD state or on main. Do not use on main -- use git-push-main instead.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-push-branch [-C <directory>] <remote>`
**Maps to:** `git <directory> push --follow-tags <remote> HEAD`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-zA-Z0-9_.-]+$`

---

## nerf-git-log

Show a short one-line log of recent commits.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-log [-C <directory>]`
**Maps to:** `git <directory> log --oneline --no-decorate -20`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-tag

Create a new annotated git tag at HEAD. Fails if the tag already exists. No force, delete, or other destructive operations.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-tag [-C <directory>] <tag>`
**Maps to:** `git <directory> tag -a <tag> -m <tag>`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

**Arguments:**

- `<tag>` (required): Tag name to create (e.g. v1.2.3). must match `^[a-zA-Z0-9._/-]+$`

---

## nerf-git-status

Show the working-tree status in short porcelain format.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-status [-C <directory>]`
**Maps to:** `git <directory> status --porcelain=v1`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-diff

Show unstaged changes as a unified diff.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-diff [-C <directory>]`
**Maps to:** `git <directory> diff --no-ext-diff --no-textconv`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

---

## nerf-git-diff-staged

Show staged changes as a unified diff.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-diff-staged [-C <directory>]`
**Maps to:** `git <directory> diff --no-ext-diff --no-textconv --staged`

**Options:**

- `-C` (optional): Subdirectory of the workspace to run git in (must be under cwd)

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
