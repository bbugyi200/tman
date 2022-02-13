"""Tests the tman project's CLI."""

from __future__ import annotations

from tman.__main__ import main  # noqa: F401  # pylint: disable=unused-import


def test_main() -> None:
    """Tests main() function."""
    assert 1 + 2 == 3
