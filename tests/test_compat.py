"""Tests for the Unicode-safe print compatibility layer."""

from __future__ import annotations

from umos_py._compat import _EMOJI_MAP, safe_print


def test_safe_print_no_crash():
    safe_print("[test] hello world")


def test_emoji_map_contains_common():
    for emoji in ("\U0001f310", "\U0001f680", "\u2705"):
        assert emoji in _EMOJI_MAP
