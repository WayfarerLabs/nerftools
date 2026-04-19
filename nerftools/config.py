"""Nerf config loader and plugin metadata resolution.

Loads an optional config file (passed explicitly via ``-c <path>``) that holds
shared package identity and per-target settings.  When no config is supplied,
built-in defaults produce installable output for every target.

Also houses the ``PluginMetadata``, ``MarketplaceMetadata``, and ``Author``
dataclasses (previously in ``plugin_meta.py``) that describe the JSON written
into ``plugin.json`` and ``marketplace.json``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

# -- Built-in defaults ---------------------------------------------------------

DEFAULT_PACKAGE_NAME = "nerftools"
DEFAULT_VERSION = "0.1.0"
DEFAULT_DESCRIPTION = "Nerf tools"
DEFAULT_MARKETPLACE_CATEGORY = "development"


# -- Errors --------------------------------------------------------------------


class ConfigError(ValueError):
    """Raised when config is missing, malformed, or has invalid fields."""


# -- Output dataclasses (JSON targets) ----------------------------------------


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
    """Metadata emitted into the plugin's ``plugin.json``."""

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
    """Metadata emitted into an embedded ``marketplace.json``."""

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


# -- Config dataclasses --------------------------------------------------------


@dataclass(frozen=True)
class MarketplaceConfig:
    """Per-target marketplace settings for ``claude-plugin``."""

    embed: bool = True
    name: str | None = None
    description: str | None = None
    owner: Author | None = None
    category: str = DEFAULT_MARKETPLACE_CATEGORY


@dataclass(frozen=True)
class ClaudePluginConfig:
    """Target-specific settings for ``claude-plugin``."""

    marketplace: MarketplaceConfig = field(default_factory=MarketplaceConfig)


@dataclass(frozen=True)
class Targets:
    """Per-target settings."""

    claude_plugin: ClaudePluginConfig = field(default_factory=ClaudePluginConfig)


@dataclass(frozen=True)
class PackageConfig:
    """Shared package identity."""

    name: str = DEFAULT_PACKAGE_NAME
    version: str = DEFAULT_VERSION
    description: str = DEFAULT_DESCRIPTION
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Defaults:
    """Stable project-level overrides for CLI defaults."""

    prefix: str = "nerf-"
    manifests: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NerfConfig:
    """Top-level config loaded from ``nerf.yaml`` (or built-in defaults)."""

    package: PackageConfig = field(default_factory=PackageConfig)
    defaults: Defaults = field(default_factory=Defaults)
    targets: Targets = field(default_factory=Targets)


# -- Loader --------------------------------------------------------------------


def load_config(path: Path | None) -> NerfConfig:
    """Load config from *path*, or return all-defaults if *path* is ``None``."""
    if path is None:
        return NerfConfig()

    import yaml

    if not path.exists():
        msg = f"config file not found: {path}"
        raise ConfigError(msg)

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ConfigError(f"failed to parse {path}: {e}") from e

    if raw is None:
        # Empty file — all defaults.
        return NerfConfig()

    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")

    unknown = set(raw) - {"package", "defaults", "targets"}
    if unknown:
        raise ConfigError(f"{path} has unknown top-level keys: {sorted(unknown)}")

    package = _parse_package(raw.get("package")) if "package" in raw else PackageConfig()
    defaults = _parse_defaults(raw.get("defaults")) if "defaults" in raw else Defaults()
    targets = _parse_targets(raw.get("targets")) if "targets" in raw else Targets()

    return NerfConfig(package=package, defaults=defaults, targets=targets)


# -- Section parsers -----------------------------------------------------------


def _parse_author(raw: Any, *, field_name: str) -> Author:
    if not isinstance(raw, dict):
        raise ConfigError(f"{field_name} must be a mapping with at least 'name'")
    if "name" not in raw or not isinstance(raw["name"], str):
        raise ConfigError(f"{field_name}.name is required and must be a string")
    unknown = set(raw) - {"name", "email", "url"}
    if unknown:
        raise ConfigError(f"{field_name} has unknown keys: {sorted(unknown)}")
    return Author(
        name=raw["name"],
        email=raw.get("email"),
        url=raw.get("url"),
    )


def _parse_package(raw: Any) -> PackageConfig:
    if not isinstance(raw, dict):
        raise ConfigError("'package' section must be a mapping")

    allowed = {"name", "version", "description", "author", "homepage", "repository", "license", "keywords"}
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigError(f"package has unknown keys: {sorted(unknown)}")

    for string_field in ("name", "version", "description", "homepage", "repository", "license"):
        if string_field in raw and (not isinstance(raw[string_field], str) or not raw[string_field]):
            raise ConfigError(f"package.{string_field} must be a non-empty string")

    author = _parse_author(raw["author"], field_name="package.author") if "author" in raw else None

    keywords = raw.get("keywords", [])
    if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
        raise ConfigError("package.keywords must be a list of strings")

    return PackageConfig(
        name=raw.get("name", DEFAULT_PACKAGE_NAME),
        version=raw.get("version", DEFAULT_VERSION),
        description=raw.get("description", DEFAULT_DESCRIPTION),
        author=author,
        homepage=raw.get("homepage"),
        repository=raw.get("repository"),
        license=raw.get("license"),
        keywords=keywords,
    )


def _parse_defaults(raw: Any) -> Defaults:
    if not isinstance(raw, dict):
        raise ConfigError("'defaults' section must be a mapping")

    allowed = {"prefix", "manifests"}
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigError(f"defaults has unknown keys: {sorted(unknown)}")

    prefix = raw.get("prefix", "nerf-")
    if not isinstance(prefix, str):
        raise ConfigError("defaults.prefix must be a string")

    manifests = raw.get("manifests", [])
    if not isinstance(manifests, list) or not all(isinstance(m, str) for m in manifests):
        raise ConfigError("defaults.manifests must be a list of strings")

    return Defaults(prefix=prefix, manifests=manifests)


def _parse_targets(raw: Any) -> Targets:
    if not isinstance(raw, dict):
        raise ConfigError("'targets' section must be a mapping")

    allowed = {"claude-plugin"}
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigError(f"targets has unknown keys: {sorted(unknown)}")

    claude_plugin = (
        _parse_claude_plugin(raw["claude-plugin"])
        if "claude-plugin" in raw
        else ClaudePluginConfig()
    )
    return Targets(claude_plugin=claude_plugin)


def _parse_claude_plugin(raw: Any) -> ClaudePluginConfig:
    if not isinstance(raw, dict):
        raise ConfigError("'targets.claude-plugin' must be a mapping")

    allowed = {"marketplace"}
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigError(f"targets.claude-plugin has unknown keys: {sorted(unknown)}")

    marketplace = (
        _parse_marketplace_config(raw["marketplace"])
        if "marketplace" in raw
        else MarketplaceConfig()
    )
    return ClaudePluginConfig(marketplace=marketplace)


def _parse_marketplace_config(raw: Any) -> MarketplaceConfig:
    if not isinstance(raw, dict):
        raise ConfigError("'targets.claude-plugin.marketplace' must be a mapping")

    allowed = {"embed", "name", "description", "owner", "category"}
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigError(f"targets.claude-plugin.marketplace has unknown keys: {sorted(unknown)}")

    embed = raw.get("embed", True)
    if not isinstance(embed, bool):
        raise ConfigError("targets.claude-plugin.marketplace.embed must be a boolean")

    for string_field in ("name", "description", "category"):
        if string_field in raw and (not isinstance(raw[string_field], str) or not raw[string_field]):
            raise ConfigError(
                f"targets.claude-plugin.marketplace.{string_field} must be a non-empty string"
            )

    owner = (
        _parse_author(raw["owner"], field_name="targets.claude-plugin.marketplace.owner")
        if "owner" in raw
        else None
    )

    return MarketplaceConfig(
        embed=embed,
        name=raw.get("name"),
        description=raw.get("description"),
        owner=owner,
        category=raw.get("category", DEFAULT_MARKETPLACE_CATEGORY),
    )


# -- Defaults resolution -------------------------------------------------------


def resolve_claude_plugin_meta(
    config: NerfConfig,
) -> tuple[PluginMetadata, MarketplaceMetadata | None]:
    """Build ``PluginMetadata`` and optional ``MarketplaceMetadata`` from config.

    Applies defaults cascade:
    - marketplace.name ← package.name
    - marketplace.description ← package.description
    - marketplace.owner.name ← package.author.name if present, else package.name
    """
    pkg = config.package
    mkt = config.targets.claude_plugin.marketplace

    plugin = PluginMetadata(
        name=pkg.name,
        version=pkg.version,
        description=pkg.description,
        author=pkg.author,
        homepage=pkg.homepage,
        repository=pkg.repository,
        license=pkg.license,
        keywords=list(pkg.keywords),
    )

    if not mkt.embed:
        return plugin, None

    # Cascade marketplace fields from package.
    mp_name = mkt.name or pkg.name
    mp_description = mkt.description or pkg.description
    mp_owner = mkt.owner
    if mp_owner is None:
        owner_name = pkg.author.name if pkg.author is not None else pkg.name
        mp_owner = Author(name=owner_name)

    marketplace = MarketplaceMetadata(
        name=mp_name,
        description=mp_description,
        owner=mp_owner,
        category=mkt.category,
    )

    return plugin, marketplace
