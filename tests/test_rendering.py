"""Unit tests for the rendering helpers in nerftools.rendering."""

from __future__ import annotations

from nerftools.rendering import md_code_span


def test_simple_value() -> None:
    assert md_code_span("origin") == "`origin`"


def test_empty_renders_as_quoted_empty_string() -> None:
    """Empty content has no valid CommonMark code span; render as `\"\"`
    (literal empty quotes inside a code span) so the meaning is unambiguous
    and the rendering pattern stays uniform."""
    assert md_code_span("") == '`""`'


def test_all_whitespace_is_preserved_without_padding() -> None:
    """CommonMark preserves all-whitespace content (the entirely-of-spaces
    exemption from the trim rule). Padding would silently grow the count."""
    assert md_code_span("   ") == "`   `"


def test_leading_space_is_padded() -> None:
    """Pad both sides; CommonMark trims one each side, leaving the original
    leading space intact."""
    assert md_code_span(" foo") == "`  foo `"


def test_trailing_space_is_padded() -> None:
    assert md_code_span("foo ") == "` foo  `"


def test_both_sides_space_is_padded() -> None:
    """The classic CommonMark trim case: both ends space, not entirely spaces.
    Without padding, both spaces would be stripped."""
    assert md_code_span(" foo ") == "`  foo  `"


def test_single_backtick_in_content_uses_double_fence() -> None:
    assert md_code_span("foo`bar") == "``foo`bar``"


def test_double_backtick_in_content_uses_triple_fence() -> None:
    assert md_code_span("foo``bar") == "```foo``bar```"


def test_leading_backtick_is_padded() -> None:
    assert md_code_span("`tilted") == "`` `tilted ``"


def test_trailing_backtick_is_padded() -> None:
    assert md_code_span("tilted`") == "`` tilted` ``"


def test_only_backtick_is_padded() -> None:
    """Single backtick alone: needs longer fence AND padding."""
    assert md_code_span("`") == "`` ` ``"
