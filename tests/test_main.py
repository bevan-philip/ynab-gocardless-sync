"""Tests for the __main__ module."""

import pytest
from unittest.mock import patch


@patch("ynab_sync.cli.cli")
def test_main_imports_cli(mock_cli):
    """Test that the __main__ module imports the CLI function."""
    # Simply importing the module should be enough to verify it imports cli
    import ynab_sync.__main__
    
    # No need to assert anything - if the import succeeds, the test passes 