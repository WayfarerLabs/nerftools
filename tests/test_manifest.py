"""Tests for manifest loading and validation (v1)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from nerftools.manifest import (
    ManifestError,
    NerfManifest,
    PathTest,
    ThreatLevel,
    load_manifest,
    merge_manifests,
)

# -- Fixtures ------------------------------------------------------------------


def _write_manifest(tmp_path: Path, content: dict) -> Path:
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.dump(content))
    return p


def _minimal_manifest(tools: dict | None = None) -> dict:
    return {
        "version": 1,
        "package": {
            "name": "test-pkg",
            "description": "Test package",
            "skill_group": "test-pkg",
        },
        "tools": tools
        or {
            "test-tool": {
                "description": "A test tool.",
                "threat": {"read": "workspace", "write": "none"},
                "template": {"command": ["echo", "hello"]},
            },
        },
    }


# -- Version -------------------------------------------------------------------


def test_missing_version_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest()
    del raw["version"]
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="'version' is required"):
        load_manifest(p)


def test_unsupported_version_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest()
    raw["version"] = 99
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="unsupported manifest version"):
        load_manifest(p)


# -- Package loading -----------------------------------------------------------


def test_load_minimal_manifest(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _minimal_manifest())
    m = load_manifest(p)
    assert isinstance(m, NerfManifest)
    assert m.version == 1
    assert m.package.name == "test-pkg"
    assert m.package.skill_group == "test-pkg"
    assert "test-tool" in m.tools


def test_load_manifest_with_skill_intro(tmp_path: Path) -> None:
    raw = _minimal_manifest()
    raw["package"]["skill_intro"] = "Use these tools carefully."
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.package.skill_intro == "Use these tools carefully."


def test_missing_package_section_raises(tmp_path: Path) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text(
        "version: 1\ntools:\n  foo:\n    description: x\n"
        "    threat:\n      read: none\n      write: none\n"
        "    template:\n      command: [echo]\n"
    )
    with pytest.raises(ManifestError, match="'package' section is required"):
        load_manifest(p)


def test_missing_tools_section_raises(tmp_path: Path) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text("version: 1\npackage:\n  name: x\n  description: x\n  skill_group: x\n")
    with pytest.raises(ManifestError, match="'tools' section is required"):
        load_manifest(p)


def test_missing_required_package_field_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest()
    del raw["package"]["name"]
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="'name' is required"):
        load_manifest(p)


# -- Threat model --------------------------------------------------------------


def test_threat_level_ordering() -> None:
    assert ThreatLevel.NONE <= ThreatLevel.WORKSPACE
    assert ThreatLevel.WORKSPACE <= ThreatLevel.MACHINE
    assert ThreatLevel.MACHINE <= ThreatLevel.REMOTE
    assert ThreatLevel.REMOTE <= ThreatLevel.ADMIN
    assert not ThreatLevel.ADMIN <= ThreatLevel.NONE


def test_threat_level_comparison() -> None:
    assert ThreatLevel.WORKSPACE < ThreatLevel.REMOTE
    assert ThreatLevel.REMOTE > ThreatLevel.WORKSPACE
    assert ThreatLevel.NONE >= ThreatLevel.NONE


def test_tool_threat_loaded(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _minimal_manifest())
    m = load_manifest(p)
    tool = m.tools["test-tool"]
    assert tool.threat.read == ThreatLevel.WORKSPACE
    assert tool.threat.write == ThreatLevel.NONE


def test_missing_threat_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {"description": "A test tool.", "template": {"command": ["echo"]}},
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="'threat' is required"):
        load_manifest(p)


def test_invalid_threat_level_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "galaxy", "write": "none"},
            "template": {"command": ["echo"]},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="invalid read level"):
        load_manifest(p)


# -- Execution modes -----------------------------------------------------------


def test_template_mode(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "hello"]},
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].template is not None
    assert m.tools["t"].template.command == ("echo", "hello")
    assert m.tools["t"].mode == "template"


def test_passthrough_mode(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "workspace", "write": "none"},
            "passthrough": {"command": "find", "deny": ["-exec"], "prefix": ["."]},
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].passthrough is not None
    assert m.tools["t"].passthrough.command == "find"
    assert m.tools["t"].passthrough.deny == ("-exec",)
    assert m.tools["t"].passthrough.prefix == (".",)
    assert m.tools["t"].mode == "passthrough"


def test_script_mode(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "script": "echo hello",
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].script == "echo hello"
    assert m.tools["t"].mode == "script"


def test_no_mode_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="exactly one of"):
        load_manifest(p)


def test_multiple_modes_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo"]},
            "script": "echo hello",
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="only one of"):
        load_manifest(p)


def test_params_in_passthrough_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "passthrough": {"command": "find"},
            "switches": {"verbose": {"description": "Verbose"}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="not allowed in passthrough"):
        load_manifest(p)


# -- Switches ------------------------------------------------------------------


def test_switch_loaded(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{switches.verbose}}"]},
            "switches": {"verbose": {"description": "Enable verbose"}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    sw = m.tools["t"].switches["verbose"]
    assert sw.flag == "--verbose"
    assert sw.description == "Enable verbose"


def test_switch_short(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{switches.verbose}}"]},
            "switches": {"verbose": {"description": "Verbose", "short": "-v"}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].switches["verbose"].short == "-v"


def test_invalid_switch_short_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{switches.verbose}}"]},
            "switches": {"verbose": {"description": "Verbose", "short": "--vv"}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="single-character flag"):
        load_manifest(p)


# -- Options -------------------------------------------------------------------


def test_option_loaded(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{options.remote}}"]},
            "options": {
                "remote": {
                    "description": "Remote name",
                    "required": True,
                    "pattern": "^[a-z]+$",
                    "deny": ["origin"],
                },
            },
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    opt = m.tools["t"].options["remote"]
    assert opt.flag == "--remote"
    assert opt.required is True
    assert opt.pattern == "^[a-z]+$"
    assert opt.deny == ("origin",)


def test_option_allow_deny_conflict_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{options.x}}"]},
            "options": {"x": {"description": "A test tool.", "allow": ["a"], "deny": ["b"]}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="cannot both be set"):
        load_manifest(p)


def test_invalid_option_pattern_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{options.x}}"]},
            "options": {"x": {"description": "A test tool.", "pattern": "[invalid"}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="invalid 'pattern' regex"):
        load_manifest(p)


def _option_default_manifest(option_spec: dict) -> dict:
    return _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{options.remote}}"]},
            "options": {"remote": {"description": "Remote name.", **option_spec}},
        },
    })


def test_option_default_loaded(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _option_default_manifest({"default": "origin"}))
    m = load_manifest(p)
    assert m.tools["t"].options["remote"].default == "origin"


def test_option_default_absent_is_none(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _option_default_manifest({}))
    m = load_manifest(p)
    assert m.tools["t"].options["remote"].default is None


def test_option_default_with_required_raises(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _option_default_manifest({"default": "origin", "required": True}))
    with pytest.raises(ManifestError, match="'default' and 'required: true' are mutually exclusive"):
        load_manifest(p)


def test_option_default_with_repeatable_raises(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _option_default_manifest({"default": "origin", "repeatable": True}))
    with pytest.raises(ManifestError, match="'default' is not supported with 'repeatable: true'"):
        load_manifest(p)


def test_option_default_must_match_pattern(tmp_path: Path) -> None:
    p = _write_manifest(
        tmp_path,
        _option_default_manifest({"default": "BadValue", "pattern": "^[a-z]+$"}),
    )
    with pytest.raises(ManifestError, match="does not match 'pattern'"):
        load_manifest(p)


def test_option_default_must_be_in_allow(tmp_path: Path) -> None:
    p = _write_manifest(
        tmp_path,
        _option_default_manifest({"default": "github", "allow": ["origin", "upstream"]}),
    )
    with pytest.raises(ManifestError, match="is not in 'allow' list"):
        load_manifest(p)


def test_option_default_must_not_be_in_deny(tmp_path: Path) -> None:
    p = _write_manifest(
        tmp_path,
        _option_default_manifest({"default": "origin", "deny": ["origin"]}),
    )
    with pytest.raises(ManifestError, match="is in 'deny' list"):
        load_manifest(p)


def test_option_default_null_is_rejected(tmp_path: Path) -> None:
    """YAML null/~ must be rejected, not silently coerced to the string 'None'."""
    p = _write_manifest(tmp_path, _option_default_manifest({"default": None}))
    with pytest.raises(ManifestError, match="'default' must be a string, got NoneType"):
        load_manifest(p)


def test_option_default_int_is_rejected(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _option_default_manifest({"default": 0}))
    with pytest.raises(ManifestError, match="'default' must be a string, got int"):
        load_manifest(p)


def test_option_default_bool_is_rejected(tmp_path: Path) -> None:
    """YAML true/false would otherwise become the Python repr 'True'/'False'."""
    p = _write_manifest(tmp_path, _option_default_manifest({"default": True}))
    with pytest.raises(ManifestError, match="'default' must be a string, got bool"):
        load_manifest(p)


def test_option_default_empty_string_is_accepted(tmp_path: Path) -> None:
    """Empty string is a legitimate default distinct from absent."""
    p = _write_manifest(tmp_path, _option_default_manifest({"default": ""}))
    m = load_manifest(p)
    assert m.tools["t"].options["remote"].default == ""


def test_option_default_with_path_tests_raises(tmp_path: Path) -> None:
    """path_tests evaluate against runtime cwd, so a load-time default cannot be
    meaningfully validated against them. Reject the combination explicitly.
    """
    p = _write_manifest(tmp_path, _option_default_manifest({
        "default": ".", "path_tests": ["under_cwd"],
    }))
    with pytest.raises(ManifestError, match="'default' cannot be combined with 'path_tests'"):
        load_manifest(p)


# -- Arguments -----------------------------------------------------------------


def test_argument_loaded(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["git", "fetch", "{{arguments.remote}}"]},
            "arguments": {
                "remote": {"description": "Remote name", "required": True},
            },
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    arg = m.tools["t"].arguments["remote"]
    assert arg.required is True
    assert arg.variadic is False


def test_variadic_argument(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["git", "add", "{{arguments.files}}"]},
            "arguments": {"files": {"description": "Files", "variadic": True}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].arguments["files"].variadic is True


def test_argument_allow_deny_conflict_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{arguments.x}}"]},
            "arguments": {"x": {"description": "A test tool.", "allow": ["a"], "deny": ["b"]}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="cannot both be set"):
        load_manifest(p)


# -- Path tests ----------------------------------------------------------------


def _path_test_manifest(tests: list[str], *, kind: str = "options") -> dict:
    if kind == "options":
        return _minimal_manifest(tools={
            "t": {
                "description": "A test tool.",
                "threat": {"read": "workspace", "write": "none"},
                "template": {"command": ["echo", "{{options.dir}}"]},
                "options": {"dir": {"description": "d", "path_tests": tests}},
            },
        })
    return _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "workspace", "write": "none"},
            "template": {"command": ["echo", "{{arguments.target}}"]},
            "arguments": {
                "target": {"description": "t", "required": True, "path_tests": tests},
            },
        },
    })


def test_path_tests_loaded_on_option(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["under_cwd", "dir"]))
    m = load_manifest(p)
    opt = m.tools["t"].options["dir"]
    assert opt.path_tests == (PathTest.UNDER_CWD, PathTest.DIR)


def test_path_tests_loaded_on_argument(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["under_cwd", "exists"], kind="arguments"))
    m = load_manifest(p)
    arg = m.tools["t"].arguments["target"]
    assert arg.path_tests == (PathTest.UNDER_CWD, PathTest.EXISTS)


def test_path_tests_default_empty(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "{{options.dir}}"]},
            "options": {"dir": {"description": "d"}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].options["dir"].path_tests == ()


def test_path_tests_empty_list_rejected(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest([]))
    with pytest.raises(ManifestError, match="must contain at least one test"):
        load_manifest(p)


def test_path_tests_unknown_value_rejected(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["frobnicate"]))
    with pytest.raises(ManifestError, match="unknown path_test 'frobnicate'"):
        load_manifest(p)


def test_path_tests_must_be_list(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "{{options.dir}}"]},
            "options": {"dir": {"description": "d", "path_tests": "under_cwd"}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="'path_tests' must be a list"):
        load_manifest(p)


def test_path_tests_duplicate_rejected(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["under_cwd", "under_cwd"]))
    with pytest.raises(ManifestError, match="duplicate path_test 'under_cwd'"):
        load_manifest(p)


def test_path_tests_file_dir_mutex(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["file", "dir"]))
    with pytest.raises(ManifestError, match="mutually exclusive: file, dir"):
        load_manifest(p)


def test_path_tests_exists_not_exists_mutex(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["exists", "not_exists"]))
    with pytest.raises(ManifestError, match="mutually exclusive: exists, not_exists"):
        load_manifest(p)


def test_path_tests_symlink_not_symlink_mutex(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["symlink", "not_symlink"]))
    with pytest.raises(ManifestError, match="mutually exclusive: symlink, not_symlink"):
        load_manifest(p)


def test_path_tests_not_exists_forbids_attr_tests(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["not_exists", "readable"]))
    with pytest.raises(ManifestError, match="'not_exists' cannot be combined with: readable"):
        load_manifest(p)


def test_path_tests_not_exists_with_under_cwd_ok(tmp_path: Path) -> None:
    p = _write_manifest(tmp_path, _path_test_manifest(["under_cwd", "not_exists"]))
    m = load_manifest(p)
    assert m.tools["t"].options["dir"].path_tests == (PathTest.UNDER_CWD, PathTest.NOT_EXISTS)


# -- Guards and pre hooks ------------------------------------------------------


def test_guard_loaded(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["git", "push", "{{arguments.remote}}", "HEAD"]},
            "arguments": {"remote": {"description": "Remote", "required": True}},
            "guards": [
                {"command": ["git", "remote", "get-url", "{{arguments.remote}}"], "fail_message": "Remote not found"},
            ],
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert len(m.tools["t"].guards) == 1
    assert m.tools["t"].guards[0].command == ("git", "remote", "get-url", "{{arguments.remote}}")


def test_pre_hook_loaded(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo"]},
            "pre": "echo setup",
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].pre == "echo setup"


# -- Cross-reference validation ------------------------------------------------


def test_undefined_placeholder_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "{{arguments.x}}"]},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="cannot be resolved"):
        load_manifest(p)


def test_unreferenced_param_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "hello"]},
            "arguments": {"x": {"description": "A test tool."}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="not referenced in template command"):
        load_manifest(p)


def test_name_overlap_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["cmd", "{{arguments.x}}"]},
            "switches": {"x": {"description": "A test tool."}},
            "arguments": {"x": {"description": "A test tool."}},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="names overlap"):
        load_manifest(p)


def test_tool_description_must_end_with_terminal_punctuation(tmp_path: Path) -> None:
    """Tool descriptions are rendered verbatim into usage/help and SKILL output,
    so they must read as complete sentences with terminal punctuation. Catches
    the no-period drift we cleaned up; prevents new tools from regressing.
    """
    raw = _minimal_manifest(tools={
        "t": {
            "description": "Show foo",  # no period
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo"]},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="must end with terminal punctuation"):
        load_manifest(p)


def test_tool_description_must_have_at_least_three_words(tmp_path: Path) -> None:
    """Trivial descriptions like "x.", "TODO.", or "Run cspell." don't tell an
    agent what the tool does beyond its name. Rule: at least 3 whitespace-
    separated words after stripping terminal punctuation.
    """
    raw = _minimal_manifest(tools={
        "t": {
            "description": "Run cspell.",  # 2 words; trivial
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo"]},
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="at least 3 words"):
        load_manifest(p)


def test_tool_description_question_mark_is_accepted(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "Is foo bar?",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo"]},
        },
    })
    p = _write_manifest(tmp_path, raw)
    m = load_manifest(p)
    assert m.tools["t"].description.endswith("?")


def test_variadic_not_last_raises(tmp_path: Path) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text(
        "version: 1\n"
        "package:\n"
        "  name: test-pkg\n"
        "  description: Test package\n"
        "  skill_group: test-pkg\n"
        "tools:\n"
        "  t:\n"
        "    description: A test tool.\n"
        "    threat:\n"
        "      read: none\n"
        "      write: none\n"
        "    template:\n"
        "      command: [echo, '{{arguments.files}}', '{{arguments.extra}}']\n"
        "    arguments:\n"
        "      files:\n"
        "        description: Files\n"
        "        variadic: true\n"
        "      extra:\n"
        "        description: Extra\n"
    )
    with pytest.raises(ManifestError, match="variadic but is not the last"):
        load_manifest(p)


def test_guard_undefined_placeholder_raises(tmp_path: Path) -> None:
    raw = _minimal_manifest(tools={
        "t": {
            "description": "A test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "{{arguments.x}}"]},
            "arguments": {"x": {"description": "A test tool."}},
            "guards": [{"command": ["check", "{{arguments.y}}"], "fail_message": "fail"}],
        },
    })
    p = _write_manifest(tmp_path, raw)
    with pytest.raises(ManifestError, match="cannot be resolved"):
        load_manifest(p)


# -- Merging -------------------------------------------------------------------


def test_merge_last_wins(tmp_path: Path) -> None:
    first = tmp_path / "first.yaml"
    first.write_text(yaml.dump(_minimal_manifest(tools={
        "t": {
            "description": "First version of the test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "first"]},
        },
    })))
    second = tmp_path / "second.yaml"
    second.write_text(yaml.dump(_minimal_manifest(tools={
        "t": {
            "description": "Second version of the test tool.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "second"]},
        },
    })))

    merged = merge_manifests([load_manifest(first), load_manifest(second)])
    assert len(merged) == 1
    assert merged[0].tools["t"].description == "Second version of the test tool."


def test_merge_different_packages(tmp_path: Path) -> None:
    a = tmp_path / "a.yaml"
    a.write_text(yaml.dump({
        "version": 1,
        "package": {"name": "pkg-a", "description": "A", "skill_group": "pkg-a"},
        "tools": {"t": {
            "description": "Test tool A.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "a"]},
        }},
    }))
    b = tmp_path / "b.yaml"
    b.write_text(yaml.dump({
        "version": 1,
        "package": {"name": "pkg-b", "description": "B", "skill_group": "pkg-b"},
        "tools": {"t": {
            "description": "Test tool B.",
            "threat": {"read": "none", "write": "none"},
            "template": {"command": ["echo", "b"]},
        }},
    }))

    merged = merge_manifests([load_manifest(a), load_manifest(b)])
    assert len(merged) == 2
    names = {m.package.name for m in merged}
    assert names == {"pkg-a", "pkg-b"}


# -- Built-in manifest ---------------------------------------------------------


def test_builtin_git_loads() -> None:
    from nerftools.cli import _DEFAULT_MANIFESTS_DIR

    manifest_path = _DEFAULT_MANIFESTS_DIR / "git.yaml"
    assert manifest_path.exists(), f"Built-in manifest not found: {manifest_path}"
    m = load_manifest(manifest_path)
    assert m.version == 1
    assert m.package.name == "git"
    assert "git-add" in m.tools
    assert "git-commit" in m.tools
    assert "git-fetch" in m.tools
    assert "git-push-main" in m.tools
    assert "git-push-branch" in m.tools
    assert "git-tag" in m.tools
    # Verify threat profiles
    assert m.tools["git-log"].threat.read == ThreatLevel.WORKSPACE
    assert m.tools["git-log"].threat.write == ThreatLevel.NONE
    assert m.tools["git-push-branch"].threat.write == ThreatLevel.REMOTE


def test_builtin_git_branch_delete_merged_main_guard_is_case_insensitive() -> None:
    """The 'cannot delete main' guard must reject Main/MAIN/etc. on case-insensitive
    filesystems (macOS APFS, Windows NTFS), where git resolves any casing to the
    same ref. Without lowercasing, `git-branch-delete-merged Main` would bypass
    the guard.
    """
    from nerftools.cli import _DEFAULT_MANIFESTS_DIR

    m = load_manifest(_DEFAULT_MANIFESTS_DIR / "git.yaml")
    pre = m.tools["git-branch-delete-merged"].pre or ""
    assert "tr '[:upper:]' '[:lower:]'" in pre, (
        "git-branch-delete-merged pre-hook should lowercase NAME before comparing to 'main'"
    )


def _builtin_manifest_paths() -> list[Path]:
    """Mirror the CLI's built-in manifest discovery (cli.py): .yaml files only."""
    from nerftools.cli import _DEFAULT_MANIFESTS_DIR

    if not _DEFAULT_MANIFESTS_DIR.exists():
        return []
    return sorted(
        p for p in _DEFAULT_MANIFESTS_DIR.iterdir() if p.suffix == ".yaml" and p.is_file()
    )


@pytest.mark.parametrize(
    "manifest_path",
    _builtin_manifest_paths(),
    ids=lambda p: p.name,
)
def test_builtin_manifest_parses(manifest_path: Path) -> None:
    """Every built-in manifest must parse cleanly. Catches schema/typo regressions."""
    m = load_manifest(manifest_path)
    assert m.version == 1
    assert m.package.name, f"{manifest_path.name} has empty package.name"
    assert m.tools, f"{manifest_path.name} has no tools"


def test_builtin_manifests_directory_not_empty() -> None:
    """Guard against the parametrized test silently passing zero cases."""
    assert _builtin_manifest_paths(), "no built-in manifests discovered"
