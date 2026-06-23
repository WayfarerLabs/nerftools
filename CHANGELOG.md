# Changelog

## [4.2.0](https://github.com/WayfarerLabs/nerftools/compare/v4.1.0...v4.2.0) (2026-06-23)


### Features

* **nerfctl:** require scope positional; add project + reset-others ([cd7ad96](https://github.com/WayfarerLabs/nerftools/commit/cd7ad96a7d1704a0f8e928b9dd5564520e67d09d))
* **nerfctl:** require scope positional; add project + reset-others ([edd3a6a](https://github.com/WayfarerLabs/nerftools/commit/edd3a6a9ece2053428e7abc52e24c385d0b647d7))
* **stdutils:** add print-range tools and sed/awk line-range hints ([2ecd119](https://github.com/WayfarerLabs/nerftools/commit/2ecd11906805cc477495ff32e82d179e7ce54b3c))
* **stdutils:** add print-range, print-range-cwd, sed/awk hints ([129bd2f](https://github.com/WayfarerLabs/nerftools/commit/129bd2f10f1085f0da223638f1a1bf0072b8a2a5))


### Bug Fixes

* **stdutils:** awk var=val handling, NR&gt;5 hint coverage, perf ([6c7b922](https://github.com/WayfarerLabs/nerftools/commit/6c7b92290412686db599c7981673eafeb1a56dd3))
* **stdutils:** print-range reviewer follow-ups (sed impl, hint regex, doc note) ([54ce4ad](https://github.com/WayfarerLabs/nerftools/commit/54ce4ad1cdb66d412b408e0ac87548a4b5bff3a5))


### Documentation

* **readme:** document bash 4+ prerequisite and macOS brew workaround ([3bde73c](https://github.com/WayfarerLabs/nerftools/commit/3bde73c0926fb0b8a59e8d0a7830f215dc085767))
* **test:** update var=val docstrings post-sed-pivot ([1e98f26](https://github.com/WayfarerLabs/nerftools/commit/1e98f269f37206828d2f9c6c2a79f83841837c74))

## [4.1.0](https://github.com/WayfarerLabs/nerftools/compare/v4.0.0...v4.1.0) (2026-06-15)


### Features

* **gh:** add gh-pr-edit and gh-issue-edit ([1a93f85](https://github.com/WayfarerLabs/nerftools/commit/1a93f8595962358fe721b4b50e3b2290e2dbc942))
* **gh:** add gh-pr-edit and gh-issue-edit ([6ed122a](https://github.com/WayfarerLabs/nerftools/commit/6ed122ad3a617378b20258c0c23e02d74177e490))
* **manifest:** add requires field for binary preflight checks ([6940d87](https://github.com/WayfarerLabs/nerftools/commit/6940d87c1a91f5608e6838e60c29bc8e4059046e))
* **manifest:** add requires field for binary preflight checks ([32baf5a](https://github.com/WayfarerLabs/nerftools/commit/32baf5a4a16f6c1717f661915024b651803e3df2))


### Bug Fixes

* **hook:** peek past command runners (timeout, nice, time, etc.) to find wrapper invocations ([deece58](https://github.com/WayfarerLabs/nerftools/commit/deece58655b9751c9ae7176bb391b9301d3bef09))
* **hook:** peek past timeout/nice/time/env/ionice/chrt to find wrapper invocations ([9da07f8](https://github.com/WayfarerLabs/nerftools/commit/9da07f85b5865513551aa538acdd505200c96ce7))
* **manifests:** drop no-op guards; add --base warning to gh-pr-edit ([6fe4a0b](https://github.com/WayfarerLabs/nerftools/commit/6fe4a0b4d0972f2f6b14c7603229350aefa1b263))
* **requires:** address review feedback ([23a0002](https://github.com/WayfarerLabs/nerftools/commit/23a000288a58e04bef429b9f5b41a5f531707ab0))


### Documentation

* **hook:** reframe wrapper-detection as UX nudge; pin lenient-scan cases ([3cdfe9c](https://github.com/WayfarerLabs/nerftools/commit/3cdfe9c2eb85c751125f0eb10f3e8d885125053f))
* **reviewer:** teach manifest reviewer to enforce requires ([b000466](https://github.com/WayfarerLabs/nerftools/commit/b0004664d18b564b0d7a2503fde8663dfa7d341b))

## [4.0.0](https://github.com/WayfarerLabs/nerftools/compare/v3.0.0...v4.0.0) (2026-06-10)


### ⚠ BREAKING CHANGES

* reports now live at ~/.nerftools/<brand>/reports/ (e.g. ~/.nerftools/nerf/reports/ for the default brand). Existing reports at ~/.nerftools/reports/ are not migrated automatically; mv them to the new location if you want them visible to report-show/report-archive.

### Features

* migrate nerf-report to manifest, add show/archive, brand-namespace reports ([b940e81](https://github.com/WayfarerLabs/nerftools/commit/b940e81841d55abf892c8d503050e6b9f3720dcf))


### Bug Fixes

* **nerf-report:** address review (BRAND guard, find depth, awk robustness, bash_hint) ([bd3e336](https://github.com/WayfarerLabs/nerftools/commit/bd3e336084c57a2ed3857c182254cf0bbb4ac313))
* **nerf-report:** chmod 0700 on archive dir; tighten bash_hint; cover no-GNU-date error path ([05e4d2c](https://github.com/WayfarerLabs/nerftools/commit/05e4d2cee4123be2885a3de91253b584f483d6ee))
* **nerf-report:** require full ISO 8601 with explicit timezone in &lt;before&gt; ([f33198c](https://github.com/WayfarerLabs/nerftools/commit/f33198c8cdc97f5285d90c209577f82ac9144377))

## [3.0.0](https://github.com/WayfarerLabs/nerftools/compare/v2.2.0...v3.0.0) (2026-06-07)


### ⚠ BREAKING CHANGES

* **hook:** hook file renamed from hooks/nerf-bash-hint to hooks/nerf-pre-tool-use; bypass sentinel renamed from \`# <brand>:bypass <reason>\` to \`# <brand>:bypass-bash-hint <reason>\`.
* PreToolUse multi-check dispatcher with new current-version check

### Features

* **nerfctl:** --create-scope-dir and --prune-older for grant scripts ([e5aec37](https://github.com/WayfarerLabs/nerftools/commit/e5aec37a505ac2ef3b3056cbec5d82419875a41c))
* **nerfctl:** add --create-scope-dir and --prune-older to grant scripts ([f087274](https://github.com/WayfarerLabs/nerftools/commit/f08727464a1fbe4c0ad4805809eb172f11ceed6c))
* PreToolUse multi-check dispatcher with new current-version check ([4889d66](https://github.com/WayfarerLabs/nerftools/commit/4889d66e85e8e1ebca3f3ad028da633371bff868))


### Bug Fixes

* **hook:** address reviewer feedback on version check ([5a65c72](https://github.com/WayfarerLabs/nerftools/commit/5a65c72ea6102bb48eef02b74e871fe0021d2ec4))
* **nerfctl:** clear error when .claude exists but is not a directory ([58f93e9](https://github.com/WayfarerLabs/nerftools/commit/58f93e97a672ea4bbe045960d618bcf740333005))
* **nerfctl:** probe for sort -V (try gsort fallback); cover grant-reset in scope-dir tests ([8b11638](https://github.com/WayfarerLabs/nerftools/commit/8b11638034501b365dab62a5e395e50113b9e5db))
* **nerfctl:** suppress capture() errors on non-Bash permission entries ([51565c5](https://github.com/WayfarerLabs/nerftools/commit/51565c5c92c05dfcc0b0562a307e3e76bb6faf79))
* **nerfctl:** warn (not silent) when version sort unavailable without --prune-older ([210100d](https://github.com/WayfarerLabs/nerftools/commit/210100ddc642de0afc0480f6c198a0642c8077ad))


### Documentation

* **nerfctl:** align help text with no-sort behavior; fix stale stub comment ([c7a52a4](https://github.com/WayfarerLabs/nerftools/commit/c7a52a471e3d47e231e5e43b015fdcd4d97cdfe4))

## [2.2.0](https://github.com/WayfarerLabs/nerftools/compare/v2.1.0...v2.2.0) (2026-06-05)


### Features

* bash-hint hook opt-in via brand-namespaced env var ([aa2288e](https://github.com/WayfarerLabs/nerftools/commit/aa2288e5f15c37f3c439698f9457f923786301f5))
* gate bash-hint hook behind brand-namespaced opt-in env var ([ee2801d](https://github.com/WayfarerLabs/nerftools/commit/ee2801d6bb5b641becdb623785729d029aad4f77))


### Documentation

* clarify claude code output ([d2094a9](https://github.com/WayfarerLabs/nerftools/commit/d2094a9b047dcfac56d90bf5cb77725abdf1fd32))
* further readme updates ([e147e84](https://github.com/WayfarerLabs/nerftools/commit/e147e842d6281e25ed05bd8c8b28ccb830db47dc))
* refresh README -- add Codex plugin, soften default-manifests section, update structure ([76cc678](https://github.com/WayfarerLabs/nerftools/commit/76cc6781269539463237c9aedacfbd3549aa2b54))
* refresh README for Codex plugin and softened default-manifests section ([63d2f5b](https://github.com/WayfarerLabs/nerftools/commit/63d2f5ba93806bbbb2fed4e521c17199e1dbced4))

## [2.1.0](https://github.com/WayfarerLabs/nerftools/compare/v2.0.0...v2.1.0) (2026-06-03)


### Features

* add gh-pr-ready and az-repos-pr-edit --draft ([8175732](https://github.com/WayfarerLabs/nerftools/commit/817573274f6032f2605792c00f91d79aad43bdda))
* add gh-pr-ready and az-repos-pr-edit --draft for draft&lt;-&gt;ready transitions ([b70c334](https://github.com/WayfarerLabs/nerftools/commit/b70c334e51132dff5041997b927311a99c0e398f))
* add nerf-report skill for structured agent feedback ([3dd9b68](https://github.com/WayfarerLabs/nerftools/commit/3dd9b682d7fa0978b324940d43136d976af5d722))
* add nerf-report skill for structured agent feedback to maintainer ([da00790](https://github.com/WayfarerLabs/nerftools/commit/da00790da206935f585121dc6b0038122030e449))
* **az:** add -C &lt;directory&gt; for project resolution across 24 azdo tools ([9bc5885](https://github.com/WayfarerLabs/nerftools/commit/9bc5885883c824183edb0caee923beb4a4847393))
* **az:** add -C &lt;directory&gt; for project resolution across azdo tools ([b99d12f](https://github.com/WayfarerLabs/nerftools/commit/b99d12f0f506b4ca38c71719b4321f7f9a402a93))
* **gh:** add gh-pr-copilot-review-status; add --log-failed switch to gh-run-view ([e23ecf3](https://github.com/WayfarerLabs/nerftools/commit/e23ecf36dd93aa1c3e2ca3c1828aa30ed7f96277))
* **gh:** add gh-pr-request-copilot-review for requesting Copilot reviews via gh CLI ([31534c1](https://github.com/WayfarerLabs/nerftools/commit/31534c11367f1292f91b8ef88b5a7342e8155931))
* **gh:** Copilot review tooling + --log-failed for gh-run-view ([67b1b6c](https://github.com/WayfarerLabs/nerftools/commit/67b1b6c35a294a4a16d1b77f041052212ab21655))
* surface nerf-report in skill footers/overview and bypass hook ([4513904](https://github.com/WayfarerLabs/nerftools/commit/45139041fe49ca736dabd1df0c640e8377be93df))
* **tf,tg:** add validate tools, --diff for hcl fmt, fix -all flag parsing ([86b56b4](https://github.com/WayfarerLabs/nerftools/commit/86b56b45a7dbc6f8108d583aac122e3494140e4f))
* **tg:** add tf-validate, tg-hcl-validate, --diff for tg-fmt ([fe1dc99](https://github.com/WayfarerLabs/nerftools/commit/fe1dc993d49ac9c0322adc72e7bd74926af009d9))


### Bug Fixes

* **az:** apply sentinel-gate contract to script-mode argv forwarders ([6700150](https://github.com/WayfarerLabs/nerftools/commit/6700150d314471b3bba1234194bd80814e88b99c))
* **az:** gate -C pre-hooks on presence sentinels, not value strings ([f9315e2](https://github.com/WayfarerLabs/nerftools/commit/f9315e21c1f3eeb5b3c8b51fdc6244e42ddedd1f))
* **az:** move -C resolution from script body into pre so dry-run validates it ([5f0ecdd](https://github.com/WayfarerLabs/nerftools/commit/5f0ecddc3599f871a42e5244176b3c964cc6a3d3))
* **az:** set _PROJECT_SET after -C detection in script-mode tools ([378e43d](https://github.com/WayfarerLabs/nerftools/commit/378e43dd16c35cdea632bc06668305df7a14d8b7))
* **generate:** gate marker write on managed-ness; reject marker symlinks; drop .git check ([bdee657](https://github.com/WayfarerLabs/nerftools/commit/bdee6576e07e53ed417376c49ca0156084947a25))
* **generate:** per-target outdir default + refuse-to-clobber guard ([33d71d4](https://github.com/WayfarerLabs/nerftools/commit/33d71d45482dd8fe4a7d9d71768f0f84c584b127))
* **generate:** per-target outdir default, refuse-to-clobber guard, --force escape hatch ([f49b483](https://github.com/WayfarerLabs/nerftools/commit/f49b483a2471d3cf11f5650974a77326994dd50e))
* **generate:** restore .git guard, propagate --keep-existing to plugins, two-pass symlink check ([ae5442e](https://github.com/WayfarerLabs/nerftools/commit/ae5442ecd4842f11a7c9f92a50a8b7a1b392999e))
* **gh:** narrow copilot-review-status filters to bot + submitted-only ([3a32998](https://github.com/WayfarerLabs/nerftools/commit/3a3299805f43bea149ec31c9c6ca35d6653f349b))
* **nerf-report:** drop random suffix and append on filename collision; fail fast on chmod ([f86ecc7](https://github.com/WayfarerLabs/nerftools/commit/f86ecc70aae5934043f91c906f10190850640499))
* **nerf-report:** validate version against safe charset, restrict report perms to user-only ([b887e4d](https://github.com/WayfarerLabs/nerftools/commit/b887e4d44ea957b852c090bae578a9e3c5b7772f))
* **nerf-report:** validate version placeholder, guard unset HOME, escape control chars ([a5b9f61](https://github.com/WayfarerLabs/nerftools/commit/a5b9f6146c18d4273701a05d5e9aa6d1163b562f))


### Documentation

* **az-repos:** mention draft-state edit in skill_intro ([95116e8](https://github.com/WayfarerLabs/nerftools/commit/95116e8e23902c260b7d787cf7f5f10a51c30862))
* fix cspell error (regen -&gt; regeneration) ([ba5ed57](https://github.com/WayfarerLabs/nerftools/commit/ba5ed579579809d47160d9411474a8e97ccced02))
* **nerf-report:** broaden bypass wording -- not only guards trigger bypass ([ee2c942](https://github.com/WayfarerLabs/nerftools/commit/ee2c94259b3d5209dc00070ad9f8eb7ce357c416))

## [2.0.0](https://github.com/WayfarerLabs/nerftools/compare/v1.4.0...v2.0.0) (2026-05-23)


### ⚠ BREAKING CHANGES

* **git:** drop git-diff-staged in favor of relaxed git-diff
* **git:** split commit message into required subject + optional body

### Features

* add bash_hints package field with cross-manifest merge ([569ace3](https://github.com/WayfarerLabs/nerftools/commit/569ace3105dd4ff71b8ff3ebec6909584b6d71f1))
* generate configurable redirect and intro hooks for claude-plugin ([e412b11](https://github.com/WayfarerLabs/nerftools/commit/e412b11f85ee10e06a1c98da689933daca5432cc))
* **git:** add restore/show/blame/stash/cherry-pick tools and relax log ([ce00f28](https://github.com/WayfarerLabs/nerftools/commit/ce00f283ccb49f862601552ca00075aec57e8799))
* **git:** drop git-diff-staged in favor of relaxed git-diff ([69372d1](https://github.com/WayfarerLabs/nerftools/commit/69372d1baca2f7ac84491278c29da56aad2deb94))
* **git:** split commit message into required subject + optional body ([49c9543](https://github.com/WayfarerLabs/nerftools/commit/49c954336afeb0ae2e046c0fca35bf836bdeedf6))
* require bash 4+ in generated scripts and nerfctl helpers ([2d086b6](https://github.com/WayfarerLabs/nerftools/commit/2d086b64460c28d480391ce8ef87679f1175da9a))


### Bug Fixes

* block git-diff --no-index, document disallowed flags, fix gh-pr-reviews ([0a70058](https://github.com/WayfarerLabs/nerftools/commit/0a70058f0579e62bc594646b2adbf480f6212126))
* clarify targets use in local rulesync config ([181a46b](https://github.com/WayfarerLabs/nerftools/commit/181a46b5dd3eb42e26c181a04c93b2b9f5f687b2))
* **gh:** add jq guard on gh-pr-reviews ([da375d6](https://github.com/WayfarerLabs/nerftools/commit/da375d696fb8b6f63f5fa8d7346a3ea20f5ae598))
* **git:** allow comma-separated scopes in commit subject pattern ([db434a5](https://github.com/WayfarerLabs/nerftools/commit/db434a57e842ff3b4d11f99979241617d074312c))
* **git:** block git diff --no-index auto-engagement via path_tests ([af2d05d](https://github.com/WayfarerLabs/nerftools/commit/af2d05d48d287dc20a3f9d2ea834b497bc315a62))
* **git:** correct -C quoting and add git-log driver re-enable denies ([888be4f](https://github.com/WayfarerLabs/nerftools/commit/888be4fba28e8d43e35d7a99b28d78c7b78cb417))
* **git:** drop pathspec guard from git-restore-worktree ([239fb3a](https://github.com/WayfarerLabs/nerftools/commit/239fb3a06c85c8b98ff6626d3ad640e204eb3241))
* **git:** trim redundant help text and pre-hook error prefixes ([3cdeeea](https://github.com/WayfarerLabs/nerftools/commit/3cdeeea433bc2fc6b52484e1b89470686c5dcdfe))
* **git:** use pre-hook for --output, clarify variadic deny docs ([ef98fa0](https://github.com/WayfarerLabs/nerftools/commit/ef98fa015ddbadcb63d4a180978eb3ca170f4d6d))
* harden bash hint hook and tighten SessionStart intro ([abb986d](https://github.com/WayfarerLabs/nerftools/commit/abb986dfd9af2b074e866cb35bca6d33dd7af0a5))
* propagate read_version_file failures and note schema drift risk ([42fa3a2](https://github.com/WayfarerLabs/nerftools/commit/42fa3a2c26c0f1f684cd1daf442a05c8f48081c5))
* regenerate agent and address copilot bash review feedback ([72275a0](https://github.com/WayfarerLabs/nerftools/commit/72275a05f8c9d5d8e0bd941ea9bdf7f52e102adc))
* script path in remediation output ([7283fa6](https://github.com/WayfarerLabs/nerftools/commit/7283fa6682591a8fbbc285ef43fa925e3338496d))
* soften SessionStart wording for opt-out configurations ([321e4f7](https://github.com/WayfarerLabs/nerftools/commit/321e4f75fd10216199fd985390aabb83ccd37eba))
* tighten bypass regex; require explicit space-then-reason ([42b25a7](https://github.com/WayfarerLabs/nerftools/commit/42b25a77e5f089b6220beec1dcc80b8479a7e0df))
* tighten wrapper-skip and align docs with current behavior ([3b84674](https://github.com/WayfarerLabs/nerftools/commit/3b84674d4769468add3073679e5e655af00ccb67))


### Documentation

* clarify how to get more info on config ([64e73ab](https://github.com/WayfarerLabs/nerftools/commit/64e73abb46dc89bc80b67438097284c27d6a8785))
* **manifest:** document variadic flag injection and safe patterns ([68e04e9](https://github.com/WayfarerLabs/nerftools/commit/68e04e96dad37bf3d2b3ee1151e261f307cb8a49))
* **manifest:** fix sentinel pattern vs allow_flags framing ([8aeae18](https://github.com/WayfarerLabs/nerftools/commit/8aeae18c70d8b05075f2bfa83b18dc3c06e129a6))
* **manifest:** use underscore emphasis to satisfy markdownlint MD049 ([14776de](https://github.com/WayfarerLabs/nerftools/commit/14776de53b9bccba2fd47c4a61983e4342caaea5))

## [1.4.0](https://github.com/WayfarerLabs/nerftools/compare/v1.3.0...v1.4.0) (2026-05-10)


### Features

* **az-boards:** enforce assignee on mywi-* tools and add mywi-list/update ([76c7af6](https://github.com/WayfarerLabs/nerftools/commit/76c7af61ce8eba60843a73111f30880acdb6c7af))
* **az-pipelines:** add timeline and log tools for run debugging ([0a20e5e](https://github.com/WayfarerLabs/nerftools/commit/0a20e5e8f94453aeab634f83b28d9656f95e3071))
* **git:** add git-rebase-continue and git-rebase-abort ([0879574](https://github.com/WayfarerLabs/nerftools/commit/0879574f48b0cc5bc52ddc1967b36bca09c04c49))
* new tools from prod standup work ([f71278f](https://github.com/WayfarerLabs/nerftools/commit/f71278f58ae8940251c50278567edd5412599102))
* pipeline debugging tools and mywi-* enforcement ([805f30e](https://github.com/WayfarerLabs/nerftools/commit/805f30ef03a1929cae5ff06d446c2c57d4afb5c7))
* prod standup tools (pipelines, repos, git, tf) ([2deb2ac](https://github.com/WayfarerLabs/nerftools/commit/2deb2ac97f264aaa5137e838aba58d1dcc65c74d))


### Bug Fixes

* align git-tag ref pattern, give tf-fmt a target dir arg, drop unenforced claim from git-tag-push ([8aea729](https://github.com/WayfarerLabs/nerftools/commit/8aea729e2e8ceb89ee9da434224017c0cec6e2ba))
* **az-boards:** quote WIQL in mywi-list and use tr for bash 3 case folding ([f2831be](https://github.com/WayfarerLabs/nerftools/commit/f2831be4fb059955035d967ef9d4d2b54fa7fa6b))
* **az-pipelines:** pipe JSON to python via process substitution and reject conflicting log modes ([4b6601e](https://github.com/WayfarerLabs/nerftools/commit/4b6601e408039491a66cfd7ab1e4f6e5d6b66822))
* reject --tail 0 and correct mywi-show description ([1c82a69](https://github.com/WayfarerLabs/nerftools/commit/1c82a6982424f86743576686eb1eea4c64b00f9b))

## [1.3.0](https://github.com/WayfarerLabs/nerftools/compare/v1.2.0...v1.3.0) (2026-05-09)


### Features

* add codex marketplace registration ([dedd5f4](https://github.com/WayfarerLabs/nerftools/commit/dedd5f49b9d7ef303e92baaf6a3a1e87cc6c28be))
* add codex-plugin target for OpenAI Codex agent support ([8b7e655](https://github.com/WayfarerLabs/nerftools/commit/8b7e6555b73a635cc890e4ab753de874983a8db4))
* add codex-plugin target for OpenAI Codex support ([85cf792](https://github.com/WayfarerLabs/nerftools/commit/85cf792477234354537e7ec25c393c0b5c771086))


### Bug Fixes

* guard codex cleanup against symlinked directories ([ebdf2fd](https://github.com/WayfarerLabs/nerftools/commit/ebdf2fd41c1ac251d776ab41180284ba391a675a))

## [1.2.0](https://github.com/WayfarerLabs/nerftools/compare/v1.1.0...v1.2.0) (2026-05-06)


### Features

* rename plugin to indicate default tools ([a4b1271](https://github.com/WayfarerLabs/nerftools/commit/a4b127171cd352eab167b7358d7ea9044663c1b0))
* rename plugin to indicate default tools ([48fac3b](https://github.com/WayfarerLabs/nerftools/commit/48fac3b3da996ef2815bcbd0216c6ad1775c36c3))

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
