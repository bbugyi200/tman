"""Tests the tman project's CLI."""

from __future__ import annotations

from tman.__main__ import main


def test_main() -> None:
    """Tests main() function."""
    assert main([""]) == 0
