"""Shared rendering helpers for tool display across output formats.

Used by builder.py, skill.py, and formats.py to avoid triplicating
the maps-to, usage-line, and constraint rendering logic.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nerftools.manifest import ArgSpec, OptionSpec, SwitchSpec, ToolSpec


def md_code_span(text: str) -> str:
    """Wrap text as a markdown code span with a backtick fence that won't
    conflict with backticks or boundary whitespace inside the content.

    Per CommonMark:
      - A code span is delimited by N backticks and ends at the next run of
        exactly N backticks; a literal backtick inside requires a longer fence.
      - If the content both begins AND ends with a space character but is not
        entirely spaces, ONE space is stripped from each side. We work around
        that by padding both sides when there's boundary whitespace.
      - There is no valid empty code span: `` `` `` is parsed as two literal
        backticks. We render empty input as `""` (literal empty quotes wrapped
        in a code span) to keep the rendering pattern uniform.

    Control characters (newlines, NUL, etc.) are rejected at manifest load
    time, so this helper assumes printable input.
    """
    if not text:
        return '`""`'
    longest = 0
    current = 0
    for c in text:
        if c == "`":
            current += 1
            if current > longest:
                longest = current
        else:
            current = 0
    fence = "`" * (longest + 1)
    if text.strip() == "":
        # All-whitespace content: CommonMark preserves it as-is (the "entirely
        # of space characters" exemption from the trim rule). Padding would
        # silently grow the visible count.
        pad = ""
    elif text[0] in " `" or text[-1] in " `":
        pad = " "
    else:
        pad = ""
    return f"{fence}{pad}{text}{pad}{fence}"


def maps_to_text(tool_spec: ToolSpec) -> str | None:
    """Return the 'Maps to' string, or None for script mode."""
    if tool_spec.template is not None:
        parts: list[str] = []
        if tool_spec.template.npm_pkgrun:
            parts.append("<runner>")
        for token in tool_spec.template.command:
            parts.append(re.sub(r"\{\{(?:\w+\.)?(\w+)\}\}", r"<\1>", token))
        return " ".join(parts)
    if tool_spec.passthrough is not None:
        pt = tool_spec.passthrough
        parts = [pt.command]
        parts.extend(pt.prefix)
        parts.append('"$@"')
        parts.extend(pt.suffix)
        return " ".join(parts)
    return None


def usage_tokens(tool_spec: ToolSpec) -> list[str]:
    """Return the parameter portion of a usage line (everything after the command path).

    Each caller prepends its own command/path token and joins.
    """
    tokens: list[str] = []

    for _name, sw in tool_spec.switches.items():
        flag_display = f"{sw.flag}|{sw.short}" if sw.short else sw.flag
        tokens.append(f"[{flag_display}]")

    for name, opt in tool_spec.options.items():
        flag_display = f"{opt.flag}|{opt.short}" if opt.short else opt.flag
        token = f"{flag_display} <{name}>"
        tokens.append(token if opt.required else f"[{token}]")

    for name, spec in tool_spec.arguments.items():
        token = f"<{name}...>" if spec.variadic else f"<{name}>"
        tokens.append(token if spec.required else f"[{token}]")

    if tool_spec.passthrough is not None and not tool_spec.arguments:
        tokens.append("[tokens...]")

    return tokens


def switch_line(sw: SwitchSpec) -> str:
    """Render a switch as a markdown bullet for skill docs."""
    flag_display = f"{sw.flag}, {sw.short}" if sw.short else sw.flag
    return f"- `{flag_display}`: {sw.description}"


def option_line(name: str, opt: OptionSpec) -> str:
    """Render an option as a markdown bullet for skill docs."""
    flag_display = f"{opt.flag}|{opt.short}" if opt.short else opt.flag
    required = "required" if opt.required else "optional"
    suffix = _constraints_suffix(opt.pattern, opt.allow, opt.deny, default=opt.default)
    return f"- `{flag_display}` ({required}): {opt.description}{suffix}"


def arg_line(name: str, spec: ArgSpec) -> str:
    """Render an argument as a markdown bullet for skill docs."""
    required = "required" if spec.required else "optional"
    label = f"<{name}...>" if spec.variadic else f"<{name}>"
    suffix = _constraints_suffix(spec.pattern, spec.allow, spec.deny)
    return f"- `{label}` ({required}): {spec.description}{suffix}"


def _constraints_suffix(
    pattern: str | None,
    allow: tuple[str, ...],
    deny: tuple[str, ...],
    default: str | None = None,
) -> str:
    """Build a constraint suffix like '. must match ...; one of ...; default `x`'."""
    constraints: list[str] = []
    if pattern:
        constraints.append(f"must match {md_code_span(pattern)}")
    if allow:
        vals = ", ".join(md_code_span(v) for v in allow)
        constraints.append(f"one of {vals}")
    if deny:
        vals = ", ".join(md_code_span(v) for v in deny)
        constraints.append(f"not {vals}")
    if default is not None:
        constraints.append(f"default {md_code_span(default)}")
    return ". " + "; ".join(constraints) if constraints else ""
