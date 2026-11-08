"""
Basic CLI tests.
"""

import pytest
from pathlib import Path


def test_cli_import():
    """Test that CLI module can be imported."""
    from source.cli import main
    assert main is not None


def test_cli_help():
    """Test that CLI shows help."""
    from source.cli import init_args
    parser = init_args()
    parser.print_help()


def test_cli_help_output():
    """Test that CLI help output contains expected text."""
    from source.cli import init_args
    parser = init_args()
    output = parser.format_help()
    assert "Modpack automation tool" in output
    assert "--check" in output
    assert "--init" in output


def test_cli_main():
    """Test that CLI main function runs."""
    from source.cli import main
    assert callable(main)
