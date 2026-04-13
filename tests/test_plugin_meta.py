"""Tests for plugin metadata parsing and serialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from nerftools.plugin_meta import (
    Author,
    MarketplaceMetadata,
    PluginMetadata,
    PluginMetaError,
    load_plugin_config,
)


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "nerf-plugin.yaml"
    p.write_text(content)
    return p


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


def test_load_plugin_config_minimal(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  name: p
  version: 1.0.0
  description: d
""")
    plugin, marketplace = load_plugin_config(path)
    assert plugin.name == "p"
    assert plugin.version == "1.0.0"
    assert plugin.description == "d"
    assert marketplace is None


def test_load_plugin_config_with_marketplace(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  name: p
  version: 1.0.0
  description: d
  author:
    name: Me
  license: MIT
  keywords: [a, b]
marketplace:
  name: m
  description: md
  owner:
    name: Org
""")
    plugin, marketplace = load_plugin_config(path)
    assert plugin.author == Author(name="Me")
    assert plugin.license == "MIT"
    assert plugin.keywords == ["a", "b"]
    assert marketplace is not None
    assert marketplace.name == "m"
    assert marketplace.owner.name == "Org"


def test_load_plugin_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PluginMetaError, match="not found"):
        load_plugin_config(tmp_path / "missing.yaml")


def test_load_plugin_config_requires_name(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  version: 1.0.0
  description: d
""")
    with pytest.raises(PluginMetaError, match="plugin.name is required"):
        load_plugin_config(path)


def test_load_plugin_config_requires_description(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  name: p
  version: 1.0.0
""")
    with pytest.raises(PluginMetaError, match="plugin.description is required"):
        load_plugin_config(path)


def test_load_plugin_config_rejects_unknown_plugin_key(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  name: p
  version: 1.0.0
  description: d
  bogus: true
""")
    with pytest.raises(PluginMetaError, match="unknown keys"):
        load_plugin_config(path)


def test_load_plugin_config_rejects_unknown_top_level_key(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  name: p
  version: 1.0.0
  description: d
bogus: true
""")
    with pytest.raises(PluginMetaError, match="unknown top-level keys"):
        load_plugin_config(path)


def test_load_plugin_config_marketplace_requires_owner(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  name: p
  version: 1.0.0
  description: d
marketplace:
  name: m
  description: d
""")
    with pytest.raises(PluginMetaError, match="marketplace.owner is required"):
        load_plugin_config(path)


def test_load_plugin_config_keywords_must_be_strings(tmp_path: Path) -> None:
    path = _write(tmp_path, """
plugin:
  name: p
  version: 1.0.0
  description: d
  keywords: [1, 2]
""")
    with pytest.raises(PluginMetaError, match="keywords must be a list of strings"):
        load_plugin_config(path)
