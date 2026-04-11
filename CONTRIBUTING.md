# Contributing

This is designed to be an opinionated project with high standards for code quality, documentation,
and design. Contributions must meet these standards and follow the guidelines outlined in this
document. I highly recommend creating discussions or issues to propose and discuss changes before
putting in the work to implement them, especially for larger changes.

All that said, I'd love to see high-quality contributions of all sizes, from fixing typos to adding
major features.

## Conventional Commits

All commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/)
specification.

## Code Quality

- **Python**: ruff (linting + formatting), mypy (type checking), pytest
- **Markdown**: markdownlint, prettier, cspell
- Custom dictionaries are maintained in `.cspell.json`

## Rebuilding the Claude Code Plugin

After changing manifests or plugin generation code, rebuild the pre-built plugin:

```bash
uv run nerf generate --target claude-plugin --outdir ./dist/claude-plugin
```

This is also done automatically by CI on merge to main.
