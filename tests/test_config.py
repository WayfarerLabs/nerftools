"""Tests for config loading, validation, and resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from nerftools.config import (
    Author,
    ConfigError,
    MarketplaceMetadata,
    NerfConfig,
    PluginMetadata,
    load_config,
    resolve_claude_plugin_meta,
)


def _write(tmp_path: Path, content: str, name: str = "nerf.yaml") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# -- Author / PluginMetadata / MarketplaceMetadata serialization ---------------


def test_plugin_to_json_minimal() -> None:
    meta = PluginMetadata(name="x", version="1.0.0", description="desc")
    data = meta.to_json()
    assert data == {
        "name": "x",
        "version": "1.0.0",
        "description": "desc",
        "skills": "./skills/",
    }


def test_plugin_to_json_with_author_and_keywords() -> None:
    meta = PluginMetadata(
        name="x",
        version="1.0.0",
        description="desc",
        author=Author(name="Me", email="me@e.com"),
        keywords=["a", "b"],
    )
    data = meta.to_json()
    assert data["author"] == {"name": "Me", "email": "me@e.com"}
    assert data["keywords"] == ["a", "b"]


def test_marketplace_to_json_uses_plugin_fields() -> None:
    plugin = PluginMetadata(name="p", version="1.0.0", description="plugin desc")
    marketplace = MarketplaceMetadata(
        name="m",
        description="market desc",
        owner=Author(name="Org"),
    )
    data = marketplace.to_json(plugin)
    assert data["name"] == "m"
    assert data["owner"] == {"name": "Org"}
    assert data["plugins"][0]["name"] == "p"
    assert data["plugins"][0]["description"] == "plugin desc"
    assert data["plugins"][0]["source"] == "./"
    assert data["plugins"][0]["author"] == {"name": "Org"}  # falls back to owner


def test_marketplace_to_json_prefers_plugin_author() -> None:
    plugin = PluginMetadata(
        name="p",
        version="1.0.0",
        description="d",
        author=Author(name="PluginAuthor"),
    )
    marketplace = MarketplaceMetadata(name="m", description="d", owner=Author(name="Owner"))
    data = marketplace.to_json(plugin)
    assert data["plugins"][0]["author"] == {"name": "PluginAuthor"}


# -- load_config ---------------------------------------------------------------


def test_load_config_none_returns_defaults() -> None:
    config = load_config(None)
    assert config.package.name == "nerftools"
    assert config.package.version == "0.1.0"
    assert config.defaults.prefix == "nerf-"
    assert config.targets.claude_plugin.marketplace.embed is True


def test_load_config_empty_file_returns_defaults(tmp_path: Path) -> None:
    path = _write(tmp_path, "")
    config = load_config(path)
    assert config.package.name == "nerftools"


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "missing.yaml")


def test_load_config_malformed_yaml(tmp_path: Path) -> None:
    path = _write(tmp_path, "{{invalid yaml")
    with pytest.raises(ConfigError, match="failed to parse"):
        load_config(path)


def test_load_config_not_a_mapping(tmp_path: Path) -> None:
    path = _write(tmp_path, "- a list")
    with pytest.raises(ConfigError, match="mapping"):
        load_config(path)


def test_load_config_unknown_top_level_key(tmp_path: Path) -> None:
    path = _write(tmp_path, "bogus: true\npackage:\n  name: x\n")
    with pytest.raises(ConfigError, match="unknown top-level keys"):
        load_config(path)


def test_load_config_full(tmp_path: Path) -> None:
    path = _write(tmp_path, """
package:
  name: my-tools
  version: 1.2.3
  description: My tools
  author:
    name: Me
    email: me@x.com
  homepage: https://example.com
  repository: https://github.com/x/y
  license: MIT
  keywords: [a, b]

defaults:
  prefix: my-
  manifests:
    - extra.yaml

targets:
  claude-plugin:
    marketplace:
      embed: true
      name: my-marketplace
      description: My marketplace
      owner:
        name: OrgName
      category: tools
""")
    config = load_config(path)
    assert config.package.name == "my-tools"
    assert config.package.version == "1.2.3"
    assert config.package.author == Author(name="Me", email="me@x.com")
    assert config.package.homepage == "https://example.com"
    assert config.package.license == "MIT"
    assert config.package.keywords == ["a", "b"]
    assert config.defaults.prefix == "my-"
    assert config.defaults.manifests == ["extra.yaml"]
    assert config.targets.claude_plugin.marketplace.embed is True
    assert config.targets.claude_plugin.marketplace.name == "my-marketplace"
    assert config.targets.claude_plugin.marketplace.owner == Author(name="OrgName")
    assert config.targets.claude_plugin.marketplace.category == "tools"


def test_load_config_package_only(tmp_path: Path) -> None:
    path = _write(tmp_path, "package:\n  name: just-a-name\n")
    config = load_config(path)
    assert config.package.name == "just-a-name"
    assert config.package.version == "0.1.0"  # default
    assert config.defaults.prefix == "nerf-"  # default


def test_load_config_rejects_unknown_package_key(tmp_path: Path) -> None:
    path = _write(tmp_path, "package:\n  name: x\n  bogus: true\n")
    with pytest.raises(ConfigError, match="unknown keys"):
        load_config(path)


def test_load_config_rejects_unknown_defaults_key(tmp_path: Path) -> None:
    path = _write(tmp_path, "defaults:\n  bogus: true\n")
    with pytest.raises(ConfigError, match="unknown keys"):
        load_config(path)


def test_load_config_rejects_unknown_targets_key(tmp_path: Path) -> None:
    path = _write(tmp_path, "targets:\n  bogus: {}\n")
    with pytest.raises(ConfigError, match="unknown keys"):
        load_config(path)


def test_load_config_rejects_unknown_marketplace_key(tmp_path: Path) -> None:
    path = _write(tmp_path, """
targets:
  claude-plugin:
    marketplace:
      bogus: true
""")
    with pytest.raises(ConfigError, match="unknown keys"):
        load_config(path)


def test_load_config_embed_must_be_bool(tmp_path: Path) -> None:
    path = _write(tmp_path, """
targets:
  claude-plugin:
    marketplace:
      embed: "yes"
""")
    with pytest.raises(ConfigError, match="boolean"):
        load_config(path)


def test_load_config_keywords_must_be_strings(tmp_path: Path) -> None:
    path = _write(tmp_path, "package:\n  keywords: [1, 2]\n")
    with pytest.raises(ConfigError, match="keywords must be a list of strings"):
        load_config(path)


def test_load_config_marketplace_embed_false(tmp_path: Path) -> None:
    path = _write(tmp_path, """
targets:
  claude-plugin:
    marketplace:
      embed: false
""")
    config = load_config(path)
    assert config.targets.claude_plugin.marketplace.embed is False


# -- resolve_claude_plugin_meta ------------------------------------------------


def test_resolve_zero_config() -> None:
    config = NerfConfig()
    plugin, marketplace = resolve_claude_plugin_meta(config)
    assert plugin.name == "nerftools"
    assert plugin.version == "0.1.0"
    assert plugin.description == "Nerf tools"
    assert marketplace is not None
    assert marketplace.name == "nerftools"
    assert marketplace.description == "Nerf tools"
    assert marketplace.owner.name == "nerftools"  # cascades from package name
    assert marketplace.category == "development"


def test_resolve_cascades_from_package(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, """
package:
  name: my-tools
  version: 2.0.0
  description: Custom tools
  author:
    name: TeamName
"""))
    plugin, marketplace = resolve_claude_plugin_meta(config)
    assert plugin.name == "my-tools"
    assert plugin.version == "2.0.0"
    assert marketplace is not None
    assert marketplace.name == "my-tools"  # cascaded
    assert marketplace.description == "Custom tools"  # cascaded
    assert marketplace.owner.name == "TeamName"  # cascaded from author


def test_resolve_marketplace_overrides(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, """
package:
  name: pkg
  description: pkg desc
targets:
  claude-plugin:
    marketplace:
      name: mkt-name
      description: mkt desc
      owner:
        name: MktOwner
"""))
    plugin, marketplace = resolve_claude_plugin_meta(config)
    assert plugin.name == "pkg"
    assert marketplace is not None
    assert marketplace.name == "mkt-name"
    assert marketplace.description == "mkt desc"
    assert marketplace.owner.name == "MktOwner"


def test_resolve_embed_false_returns_none() -> None:
    config = load_config(None)
    # Manually set embed false via a loaded config
    from nerftools.config import ClaudePluginConfig, MarketplaceConfig, Targets

    config = NerfConfig(
        targets=Targets(
            claude_plugin=ClaudePluginConfig(
                marketplace=MarketplaceConfig(embed=False)
            )
        )
    )
    plugin, marketplace = resolve_claude_plugin_meta(config)
    assert plugin.name == "nerftools"
    assert marketplace is None
