# Changelog

## [1.1.0](https://github.com/WayfarerLabs/nerftools/compare/v1.0.0...v1.1.0) (2026-05-04)


### Features

* **az-devops:** new package with az-devops-set-default-project tool ([0fb4a15](https://github.com/WayfarerLabs/nerftools/commit/0fb4a15347edd279481f51a85506e3ad254a7479))
* **azdo:** --project everywhere, new pipelines/repos tools, area listing ([a42f7e7](https://github.com/WayfarerLabs/nerftools/commit/a42f7e71eab7e3d5dcc04de50377ef504c7fefaa))
* **azdo:** --project everywhere, new tools, set-default-project ([2dab02d](https://github.com/WayfarerLabs/nerftools/commit/2dab02df9d885d6636e37bfe718b57a3617dbded))
* **gh:** differentiate the four PR comment surfaces ([567b64d](https://github.com/WayfarerLabs/nerftools/commit/567b64dc18444ff3df17e2f0ee04e67d24469dfc))
* **gh:** differentiate the four PR comment surfaces; add reviews tool ([ca9ab91](https://github.com/WayfarerLabs/nerftools/commit/ca9ab910ebd7e426b4704b47994cbdc1b4518232))
* **manifest:** add path_tests for filesystem-typed parameters ([e035eac](https://github.com/WayfarerLabs/nerftools/commit/e035eac70eabf84a6b02ef508b7995fe943708ec))
* **manifest:** add path_tests for filesystem-typed parameters ([fdb64cd](https://github.com/WayfarerLabs/nerftools/commit/fdb64cde6201f3d567cdfb04ff8e1c955c08d0a7))
* massive add of az-related default tools ([818fe04](https://github.com/WayfarerLabs/nerftools/commit/818fe04326be536924de4e7450e202db759df362))


### Bug Fixes

* address PR review feedback on az and kubectl tools ([4395484](https://github.com/WayfarerLabs/nerftools/commit/4395484f4388f99ee760a774ae7be406d40d586b))
* address two minor PR review nits ([adad61d](https://github.com/WayfarerLabs/nerftools/commit/adad61d071fc325325e12148b8e58104def93b0e))
* **az-aks:** split admin credential fetch, mark command-invoke admin, fix variadic ([f152896](https://github.com/WayfarerLabs/nerftools/commit/f152896f4af595b235be0d3af1d5d1e1b7e1cd91))
* **az-keyvault:** drop secret fingerprint and tighten masked output ([242f8d7](https://github.com/WayfarerLabs/nerftools/commit/242f8d79e4c9a3d3a34a59dd6ab58d12476409b5))
* **az-monitor:** dry-run honors validation; --interval allows P1D and FULL ([c246266](https://github.com/WayfarerLabs/nerftools/commit/c2462661def1d26d9556925b359ef79d2fa43b88))
* **builder:** add hint lines to path_tests errors; doc symlink semantics ([a1e602b](https://github.com/WayfarerLabs/nerftools/commit/a1e602b691091c1b08f5017074467d397f3bb382))
* **builder:** preserve shell quoting in dry-run output via printf %q ([5ef4816](https://github.com/WayfarerLabs/nerftools/commit/5ef4816f086833445310674d4f9d157c609ad91d))
* **builder:** reject --nerf-dry-run tokens inside variadic+allow_flags args ([854519c](https://github.com/WayfarerLabs/nerftools/commit/854519c4070a35592b0f5358e223e270d812ad3d))
* **builder:** reject trailing tokens after declared positionals ([9580f8b](https://github.com/WayfarerLabs/nerftools/commit/9580f8b32dcc41332caca08d7bbebffd2a643409))
* **builder:** revert ineffective set -e in _nerf_pre, document the limitation ([7e6787a](https://github.com/WayfarerLabs/nerftools/commit/7e6787a788a58b37ae63bd5486c068af2238ea17))
* **builder:** under_cwd accepts paths under root when cwd is "/" ([3b05ccd](https://github.com/WayfarerLabs/nerftools/commit/3b05ccd02c0ffa8e91cefcad6a3112228b281d0a))
* cross-platform date in az-monitor, drop None aggregation, simplify timeout msg ([616385d](https://github.com/WayfarerLabs/nerftools/commit/616385d7f411cfc091c6c8ef81ecbcd94b33ca45))
* **gh-pr-reviews:** use --paginate; fix Changes-requested wording ([97e5f41](https://github.com/WayfarerLabs/nerftools/commit/97e5f412d9d37378e366b25b8044b2cd8274ec10))
* **gh:** add --slurp so paginated jq aggregates across pages ([8ebd3eb](https://github.com/WayfarerLabs/nerftools/commit/8ebd3eb00bcb3b7687306fdcdde5263599b8dac5))
* high-impact security and correctness from second-pass review ([022af82](https://github.com/WayfarerLabs/nerftools/commit/022af82533d88258680c7ca02b9d9b95302e35e1))
* **kubectl:** convert read-only tools from passthrough to template ([782b3a7](https://github.com/WayfarerLabs/nerftools/commit/782b3a7c0f97fd9feda09d6c363c66c0d93c2768))
* **kubectl:** kubectl-config-use-context is admin-threat, tighten pattern ([f1265ce](https://github.com/WayfarerLabs/nerftools/commit/f1265ce1b67f5396829879a3c39d75f23f389edf))
* more PR review feedback (rename misleading tool, guard external deps) ([6c101a4](https://github.com/WayfarerLabs/nerftools/commit/6c101a48b08560acc44342dc0c3d763ce2e72a20))
* paginate the remaining gh read tools; tighten cross-refs and doc ([8d48ed5](https://github.com/WayfarerLabs/nerftools/commit/8d48ed5d8c11abb5c72c73aee032ac1d23ef1a82))
* require 3+ word tool descriptions to catch trivial placeholders ([3433ffd](https://github.com/WayfarerLabs/nerftools/commit/3433ffd6a79c92a91743968639311be9b199a6a9))
* smaller hardening from second-pass review ([5079b21](https://github.com/WayfarerLabs/nerftools/commit/5079b21039265787dfc63721a47c6b3cf358c089))
* stop appending "." to descriptions; require terminal punctuation in manifest ([2ce0f11](https://github.com/WayfarerLabs/nerftools/commit/2ce0f11f514e57e4e0a029a786686cb5b54cdd04))


### Documentation

* address review feedback on coverage gap and template paragraph ([dec48de](https://github.com/WayfarerLabs/nerftools/commit/dec48def42011233452ed7b85d0e85697c78431a))
* **az-account:** document --subscription scope boundary ([b105f2b](https://github.com/WayfarerLabs/nerftools/commit/b105f2b008cafe9d548a743885c5fa93b2cf02b8))
* correct --nerf-dry-run position claim and warn against local in pre ([9231598](https://github.com/WayfarerLabs/nerftools/commit/923159816725486aa12c3f9f26442b75da5f04cb))
* document passthrough security limitations around alternative flag syntax ([44031d5](https://github.com/WayfarerLabs/nerftools/commit/44031d5a71864313a6dbc1362d547ac6ddb6ccca))

## [1.0.0](https://github.com/WayfarerLabs/nerftools/compare/v0.3.2...v1.0.0) (2026-04-19)


### ⚠ BREAKING CHANGES

* `--plugin-config` and `--prefix` flags are removed. Use `-c <path>` to pass a config file. `--prefix` is now configured via `defaults.prefix` in the config file.

### Features

* introduce optional config file, drop --plugin-config and install script ([f6a1ab9](https://github.com/WayfarerLabs/nerftools/commit/f6a1ab95f7f1e22fc84d6fea111390db38ef6ebb))


### Bug Fixes

* address review feedback from Copilot ([60f4bc5](https://github.com/WayfarerLabs/nerftools/commit/60f4bc53ca87607b40873554a48ba7984a7b6c9e))
* **ci:** sync uv.lock during release to prevent version drift ([6eef9b8](https://github.com/WayfarerLabs/nerftools/commit/6eef9b8d6dfd2ccc0646cca71bdcc95fff779f48))


### Documentation

* **sdd:** capture the refactor sdd as it defined the fundamental structure ([5c7cad4](https://github.com/WayfarerLabs/nerftools/commit/5c7cad4248c3320cd7d67848d4963376dd8f24ee))

## [0.3.2](https://github.com/WayfarerLabs/nerftools/compare/v0.3.1...v0.3.2) (2026-04-14)


### Documentation

* clean up pypi description ([d2b5f7f](https://github.com/WayfarerLabs/nerftools/commit/d2b5f7fef31e4ac0048a0a35059b2d24ea3e07ac))
* clean up pypi description ([d2ab29d](https://github.com/WayfarerLabs/nerftools/commit/d2ab29d03366f92e1e6660ba99745b7d2a0469f5))

## [0.3.1](https://github.com/WayfarerLabs/nerftools/compare/v0.3.0...v0.3.1) (2026-04-14)


### Bug Fixes

* use app token for regenerate-dist pushes so CI triggers on release PRs ([e78ae87](https://github.com/WayfarerLabs/nerftools/commit/e78ae875208a100d77cde6cb0881186e61b83e60))

## [0.3.0](https://github.com/WayfarerLabs/nerftools/compare/v0.2.0...v0.3.0) (2026-04-14)


### Features

* add --embed-marketplace option for standalone plugin deployment ([d00ae28](https://github.com/WayfarerLabs/nerftools/commit/d00ae28170857702a29141f24bec15c62e034c8b))
* initial nerftools repo with Python package and pre-built Claude Code plugin ([55eee79](https://github.com/WayfarerLabs/nerftools/commit/55eee79eb462dfb996568d42e05b86fe3a11ce3a))
* templatize plugin metadata via nerf-plugin.yaml config ([05086d6](https://github.com/WayfarerLabs/nerftools/commit/05086d63214351f2f9cef21fd4b6dc0679a52bd4))


### Bug Fixes

* doc update as fix to trigger release pipeline ([79ede3c](https://github.com/WayfarerLabs/nerftools/commit/79ede3c0f7fad1446e960bef3f943c5ca83e1a08))
* drop component prefix from release-please tags to match release … ([ac70693](https://github.com/WayfarerLabs/nerftools/commit/ac70693efa1e418348e5b7f10b964ebed82258db))
* drop component prefix from release-please tags to match release workflow ([6f92386](https://github.com/WayfarerLabs/nerftools/commit/6f92386f6fdc3dab9b63cc12ad9fcfead327382b))


### Documentation

* additional readme tweaks ([4f7267f](https://github.com/WayfarerLabs/nerftools/commit/4f7267f8112c215ffc0fd50d0cdd2a9d6430ea87))
* document the release process in CONTRIBUTING.md ([cfd29c8](https://github.com/WayfarerLabs/nerftools/commit/cfd29c8b144d17d58232c6b8677451c427627d8a))
* fix manifest spec link and split threat model content between README and spec ([60493c8](https://github.com/WayfarerLabs/nerftools/commit/60493c846bb9fbffde8875a576a4698e4ae2e461))
* move manifest guide and ref from readme ([6392c0b](https://github.com/WayfarerLabs/nerftools/commit/6392c0b716892080137b133487f3a536650590b3))
* polish README intro and update quick start with --plugin-config ([6cd3dde](https://github.com/WayfarerLabs/nerftools/commit/6cd3dde8c3b98dc8be7c57b1d0a3de84429bd9d0))
* update readme with additional context ([a93632d](https://github.com/WayfarerLabs/nerftools/commit/a93632dd217d5dad44ee4df3c86a31c282640636))

## [0.2.0](https://github.com/WayfarerLabs/nerftools/compare/nerftools-v0.1.0...nerftools-v0.2.0) (2026-04-14)


### Features

* add --embed-marketplace option for standalone plugin deployment ([d00ae28](https://github.com/WayfarerLabs/nerftools/commit/d00ae28170857702a29141f24bec15c62e034c8b))
* initial nerftools repo with Python package and pre-built Claude Code plugin ([55eee79](https://github.com/WayfarerLabs/nerftools/commit/55eee79eb462dfb996568d42e05b86fe3a11ce3a))
* templatize plugin metadata via nerf-plugin.yaml config ([05086d6](https://github.com/WayfarerLabs/nerftools/commit/05086d63214351f2f9cef21fd4b6dc0679a52bd4))


### Bug Fixes

* doc update as fix to trigger release pipeline ([79ede3c](https://github.com/WayfarerLabs/nerftools/commit/79ede3c0f7fad1446e960bef3f943c5ca83e1a08))


### Documentation

* additional readme tweaks ([4f7267f](https://github.com/WayfarerLabs/nerftools/commit/4f7267f8112c215ffc0fd50d0cdd2a9d6430ea87))
* document the release process in CONTRIBUTING.md ([cfd29c8](https://github.com/WayfarerLabs/nerftools/commit/cfd29c8b144d17d58232c6b8677451c427627d8a))
* fix manifest spec link and split threat model content between README and spec ([60493c8](https://github.com/WayfarerLabs/nerftools/commit/60493c846bb9fbffde8875a576a4698e4ae2e461))
* move manifest guide and ref from readme ([6392c0b](https://github.com/WayfarerLabs/nerftools/commit/6392c0b716892080137b133487f3a536650590b3))
* polish README intro and update quick start with --plugin-config ([6cd3dde](https://github.com/WayfarerLabs/nerftools/commit/6cd3dde8c3b98dc8be7c57b1d0a3de84429bd9d0))
* update readme with additional context ([a93632d](https://github.com/WayfarerLabs/nerftools/commit/a93632dd217d5dad44ee4df3c86a31c282640636))
