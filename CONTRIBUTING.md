# Contributing

This is designed to be an opinionated project with high standards for code quality, documentation,
and design. Contributions must meet these standards and follow the guidelines outlined in this
document. I highly recommend creating discussions or issues to propose and discuss changes before
putting in the work to implement them, especially for larger changes.

All that said, I'd love to see high-quality contributions of all sizes, from fixing typos to adding
major features.

## Conventional Commits

All commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/)
specification. This is not just a style preference -- commit types drive automated versioning
(see [Releases](#releases) below).

Commit types that trigger version bumps:

- `feat:` -> minor version bump
- `fix:` / `perf:` -> patch version bump
- `feat!:` / `fix!:` / any commit with `BREAKING CHANGE:` in the body -> major version bump

Other types (`docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`, `style:`, `revert:`) do not
trigger a release on their own but still appear in the changelog.

When squash-merging a PR, set the PR title to the desired conventional commit message -- GitHub
uses that as the squash commit message, which is what `release-please` reads.

## Code Quality

- **Python**: ruff (linting + formatting), mypy (type checking), pytest
- **Markdown**: markdownlint, prettier, cspell
- Custom dictionaries are maintained in `.cspell.json`

## Rebuilding the Claude Code Plugin Locally

After changing manifests or plugin generation code, you can rebuild the pre-built plugin locally
to preview the output:

```bash
uv run nerf generate --target claude-plugin --plugin-config nerf-plugin.yaml --outdir ./out/claude-plugin
```

You don't need to commit the regenerated `out/` -- CI regenerates it as part of the release PR.
But committing it can be useful so reviewers can see the exact generated output in your PR diff.

## Releases

Releases are fully automated via [`release-please`](https://github.com/googleapis/release-please)
and conventional commits. No one manually bumps versions or creates tags.

### How a release happens

1. Feature PRs land on `main` with conventional commit messages.
2. The `release-please` workflow keeps an open PR titled `chore(main): release X.Y.Z` that
   accumulates changes. On each push to `main` it:
   - Computes the next version from the conventional commits since the last release.
   - Updates the version in `pyproject.toml`, `nerf-plugin.yaml`, and `.release-please-manifest.json`.
   - Updates `CHANGELOG.md`.
   - Regenerates `out/claude-plugin/` with the new version baked into `plugin.json`.
3. When you're ready to release, merge the release PR.
4. On merge, `release-please` creates the git tag (`vX.Y.Z`) and a GitHub Release.
5. The tag push triggers the `release` workflow, which verifies the tag is on `main`, runs the
   test suite, and publishes to PyPI via trusted publishing.

### What you do as a maintainer

- Review and merge feature PRs normally.
- When you want to cut a release, review the release PR (check the version bump and the changelog)
  and merge it. That's it.

### What you *don't* do

- Don't edit version numbers by hand in any file. `release-please` owns them.
- Don't create tags by hand. `release-please` creates tags on merge of the release PR.
- Don't edit `CHANGELOG.md` by hand. It's regenerated from commit messages.
- Don't edit `out/claude-plugin/` by hand. Edit the source (`nerftools/`, manifests, or
  `nerf-plugin.yaml`) and the release PR will regenerate it.

### Breaking changes

To signal a breaking change, use `!` in the commit type or add a `BREAKING CHANGE:` footer:

```text
feat!: rename --embed-marketplace to --standalone

BREAKING CHANGE: the --embed-marketplace flag has been replaced with --standalone.
```

Either form bumps the major version.
