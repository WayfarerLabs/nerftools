"""Plugin and marketplace metadata used by the claude-plugin builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class PluginMetaError(ValueError):
    """Raised when plugin metadata is missing or malformed."""


@dataclass(frozen=True)
class Author:
    name: str
    email: str | None = None
    url: str | None = None

    def to_json(self) -> dict[str, Any]:
        data: dict[str, Any] = {"name": self.name}
        if self.email is not None:
            data["email"] = self.email
        if self.url is not None:
            data["url"] = self.url
        return data


@dataclass(frozen=True)
class PluginMetadata:
    """Metadata emitted into the plugin's `plugin.json`."""

    name: str
    version: str
    description: str
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "skills": "./skills/",
        }
        if self.author is not None:
            data["author"] = self.author.to_json()
        if self.homepage is not None:
            data["homepage"] = self.homepage
        if self.repository is not None:
            data["repository"] = self.repository
        if self.license is not None:
            data["license"] = self.license
        if self.keywords:
            data["keywords"] = list(self.keywords)
        return data


@dataclass(frozen=True)
class MarketplaceMetadata:
    """Metadata emitted into an embedded `marketplace.json`.

    Only used when `build_claude_plugin(..., embed_marketplace=True)`.
    """

    name: str
    description: str
    owner: Author
    category: str = "development"

    def to_json(self, plugin: PluginMetadata) -> dict[str, Any]:
        return {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": self.name,
            "description": self.description,
            "owner": self.owner.to_json(),
            "plugins": [
                {
                    "name": plugin.name,
                    "description": plugin.description,
                    "author": (plugin.author or self.owner).to_json(),
                    "source": "./",
                    "category": self.category,
                }
            ],
        }


def _parse_author(raw: Any, *, field_name: str) -> Author:
    if not isinstance(raw, dict):
        raise PluginMetaError(f"{field_name} must be a mapping with at least 'name'")
    if "name" not in raw or not isinstance(raw["name"], str):
        raise PluginMetaError(f"{field_name}.name is required and must be a string")
    unknown = set(raw) - {"name", "email", "url"}
    if unknown:
        raise PluginMetaError(f"{field_name} has unknown keys: {sorted(unknown)}")
    return Author(
        name=raw["name"],
        email=raw.get("email"),
        url=raw.get("url"),
    )


def _parse_plugin(raw: Any) -> PluginMetadata:
    if not isinstance(raw, dict):
        raise PluginMetaError("'plugin' section must be a mapping")

    for required in ("name", "version", "description"):
        if required not in raw:
            raise PluginMetaError(f"plugin.{required} is required")
        if not isinstance(raw[required], str) or not raw[required]:
            raise PluginMetaError(f"plugin.{required} must be a non-empty string")

    allowed = {"name", "version", "description", "author", "homepage", "repository", "license", "keywords"}
    unknown = set(raw) - allowed
    if unknown:
        raise PluginMetaError(f"plugin has unknown keys: {sorted(unknown)}")

    author = _parse_author(raw["author"], field_name="plugin.author") if "author" in raw else None

    keywords = raw.get("keywords", [])
    if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
        raise PluginMetaError("plugin.keywords must be a list of strings")

    for optional in ("homepage", "repository", "license"):
        if optional in raw and not isinstance(raw[optional], str):
            raise PluginMetaError(f"plugin.{optional} must be a string")

    return PluginMetadata(
        name=raw["name"],
        version=raw["version"],
        description=raw["description"],
        author=author,
        homepage=raw.get("homepage"),
        repository=raw.get("repository"),
        license=raw.get("license"),
        keywords=keywords,
    )


def _parse_marketplace(raw: Any) -> MarketplaceMetadata:
    if not isinstance(raw, dict):
        raise PluginMetaError("'marketplace' section must be a mapping")

    for required in ("name", "description", "owner"):
        if required not in raw:
            raise PluginMetaError(f"marketplace.{required} is required")

    for string_field in ("name", "description"):
        if not isinstance(raw[string_field], str) or not raw[string_field]:
            raise PluginMetaError(f"marketplace.{string_field} must be a non-empty string")

    allowed = {"name", "description", "owner", "category"}
    unknown = set(raw) - allowed
    if unknown:
        raise PluginMetaError(f"marketplace has unknown keys: {sorted(unknown)}")

    category = raw.get("category", "development")
    if not isinstance(category, str):
        raise PluginMetaError("marketplace.category must be a string")

    return MarketplaceMetadata(
        name=raw["name"],
        description=raw["description"],
        owner=_parse_author(raw["owner"], field_name="marketplace.owner"),
        category=category,
    )


def load_plugin_config(path: Path) -> tuple[PluginMetadata, MarketplaceMetadata | None]:
    """Load plugin metadata (and optional marketplace metadata) from a YAML file."""
    import yaml

    if not path.exists():
        raise PluginMetaError(f"plugin config not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise PluginMetaError(f"failed to parse {path}: {e}") from e

    if not isinstance(raw, dict):
        raise PluginMetaError(f"{path} must contain a mapping at the top level")

    if "plugin" not in raw:
        raise PluginMetaError(f"{path} must define a 'plugin' section")

    plugin = _parse_plugin(raw["plugin"])
    marketplace = _parse_marketplace(raw["marketplace"]) if "marketplace" in raw else None

    unknown = set(raw) - {"plugin", "marketplace"}
    if unknown:
        raise PluginMetaError(f"{path} has unknown top-level keys: {sorted(unknown)}")

    return plugin, marketplace
