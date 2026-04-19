# Changelog

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
