---
name: nerf-git
description: "Git workflow tools for safe, scoped git operations"
targets: ["*"]
---

# nerf-git

These tools are available as scripts within this plugin. Call them using the absolute paths shown in each usage line.

These tools wrap git operations with safety guardrails. Always stage changes
with git-add before committing. Commit messages must follow the
Conventional Commits specification. All remote operations take the remote
name as the first positional argument (typically origin).

## nerf-git-add

Stage files or directories for commit.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-add <files...>`
**Maps to:** `git add <files>`

**Arguments:**

- `<files...>` (required): Files or directories to stage

---

## nerf-git-commit

Create a git commit with a Conventional Commits message (changes must already be staged). Format: type[(scope)][!]: description. Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Must not contain Co-Authored-By trailers..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-commit <message>`
**Maps to:** `git commit -m <message>`

**Arguments:**

- `<message>` (required): Commit message: type[(scope)][!]: description. must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9._-]+\))?!?: .+`

---

## nerf-git-commit-amend

Amend the most recent commit with a new message. Fails if the commit has already been pushed to any remote. Use only to fix the last local commit..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-commit-amend <message>`
**Maps to:** `git commit --amend -m <message>`

**Arguments:**

- `<message>` (required): Commit message: type[(scope)][!]: description. must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9._-]+\))?!?: .+`

---

## nerf-git-revert

Create a new commit that undoes a previous commit. Does not rewrite history -- safe to use on pushed commits..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-revert <ref>`
**Maps to:** `git revert --no-edit <ref>`

**Arguments:**

- `<ref>` (required): Commit to revert (e.g. HEAD, a commit SHA, or HEAD~2)

---

## nerf-git-reset-hard-last

Drop the most recent commit entirely, discarding its changes. Fails if the commit has already been pushed to any remote..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-reset-hard-last`
**Maps to:** `git reset --hard HEAD~1`

No arguments.

---

## nerf-git-fetch

Fetch all branches and tags from a remote.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-fetch <remote>`
**Maps to:** `git fetch <remote> --tags`

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-z0-9_-]+$`

---

## nerf-git-pull

Pull the current branch from a remote.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-pull <remote>`
**Maps to:** `git pull <remote>`

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-z0-9_-]+$`

---

## nerf-git-push-main

Push the local main branch to a remote including annotated tags (no force push). Use only when the local main branch is ready to publish..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-push-main <remote>`
**Maps to:** `git push --follow-tags <remote> main`

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-z0-9_-]+$`

---

## nerf-git-push-branch

Push the current branch to a remote including annotated tags (no force push). Fails if in detached HEAD state or on main. Do not use on main -- use git-push-main instead..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-push-branch <remote>`
**Maps to:** `git push --follow-tags <remote> HEAD`

**Arguments:**

- `<remote>` (required): Remote name (e.g. origin). must match `^[a-z0-9_-]+$`

---

## nerf-git-log

Show a short one-line log of recent commits.

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-log`
**Maps to:** `git log --oneline --no-decorate -20`

No arguments.

---

## nerf-git-tag

Create a new annotated git tag at HEAD. Fails if the tag already exists. No force, delete, or other destructive operations..

**Usage:** `${CLAUDE_PLUGIN_ROOT}/skills/nerf-git/scripts/nerf-git-tag <tag>`
**Maps to:** `git tag -a <tag> -m <tag>`

**Arguments:**

- `<tag>` (required): Tag name to create (e.g. v1.2.3). must match `^[a-zA-Z0-9._/-]+$`

---
