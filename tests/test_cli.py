"""Tests for the CLI module."""

import pytest
import click
import logging
import asyncio
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from ynab_sync.cli import cli


@pytest.fixture
def cli_runner():
    """Fixture for testing CLI commands."""
    return CliRunner()


@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
def test_configure_command(mock_save_config, mock_load_config, cli_runner):
    """Test the configure command."""
    # Mock the load_config to return an empty config
    mock_load_config.return_value = {}
    
    # Test with input values
    inputs = "\n".join([
        "test_ynab_api_key",
        "test_budget_id",
        "test_secret_id",
        "test_secret_key"
    ])
    
    result = cli_runner.invoke(cli, ["configure"], input=inputs)
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Configuration saved successfully!" in result.output
    
    # Check that save_config was called with the correct values
    expected_config = {
        "ynab": {
            "api_key": "test_ynab_api_key",
            "budget_id": "test_budget_id"
        },
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        }
    }
    mock_save_config.assert_called_once_with(expected_config)


@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
def test_configure_command_with_defaults(mock_save_config, mock_load_config, cli_runner):
    """Test the configure command with existing values as defaults."""
    # Mock the load_config to return an existing config
    mock_load_config.return_value = {
        "ynab": {
            "api_key": "existing_api_key",
            "budget_id": "existing_budget_id"
        },
        "gocardless": {
            "secret_id": "existing_secret_id",
            "secret_key": "existing_secret_key"
        }
    }
    
    # Test with empty inputs (accepting defaults)
    inputs = "\n\n\n\n"
    
    result = cli_runner.invoke(cli, ["configure"], input=inputs)
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Configuration saved successfully!" in result.output
    
    # Check that save_config was called with the existing values
    expected_config = {
        "ynab": {
            "api_key": "existing_api_key",
            "budget_id": "existing_budget_id"
        },
        "gocardless": {
            "secret_id": "existing_secret_id",
            "secret_key": "existing_secret_key"
        }
    }
    mock_save_config.assert_called_once_with(expected_config)


@patch("ynab_sync.cli.load_config")
def test_sync_command_missing_ynab_api_key(mock_load_config, cli_runner):
    """Test the sync command with missing YNAB API key."""
    # Mock the load_config to return a config without YNAB API key
    mock_load_config.return_value = {
        "ynab": {
            "budget_id": "test_budget_id"
        },
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "requisition_id": "test_requisition_id"
        },
        "account_mappings": {
            "bank_account_1": "ynab_account_1"
        }
    }
    
    # Run the command
    result = cli_runner.invoke(cli, ["sync"])
    
    # Check that the command failed with the expected error message
    assert result.exit_code == 0  # Click doesn't set non-zero exit code for early returns
    assert "YNAB API key not found" in result.output


@patch("ynab_sync.cli.load_config")
def test_sync_command_missing_requisition_id(mock_load_config, cli_runner):
    """Test the sync command with missing requisition ID."""
    # Mock the load_config to return a config without requisition ID
    mock_load_config.return_value = {
        "ynab": {
            "api_key": "test_api_key",
            "budget_id": "test_budget_id"
        },
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        },
        "account_mappings": {
            "bank_account_1": "ynab_account_1"
        }
    }
    
    # Run the command
    result = cli_runner.invoke(cli, ["sync"])
    
    # Check that the command failed with the expected error message
    assert result.exit_code == 0  # Click doesn't set non-zero exit code for early returns
    assert "No bank connection found" in result.output


@patch("ynab_sync.cli.load_config")
def test_sync_command_missing_account_mappings(mock_load_config, cli_runner):
    """Test the sync command with missing account mappings."""
    # Mock the load_config to return a config without account mappings
    mock_load_config.return_value = {
        "ynab": {
            "api_key": "test_api_key",
            "budget_id": "test_budget_id"
        },
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "requisition_id": "test_requisition_id"
        }
    }
    
    # Run the command
    result = cli_runner.invoke(cli, ["sync"])
    
    # Check that the command failed with the expected error message
    assert result.exit_code == 0  # Click doesn't set non-zero exit code for early returns
    assert "No account mappings found" in result.output 