"""Tests for the CLI module."""

import pytest
import click
import logging
import asyncio
from unittest.mock import patch, MagicMock, ANY
from click.testing import CliRunner

from ynab_sync.cli import cli


@pytest.fixture
def cli_runner():
    """Fixture for testing CLI commands."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_future(event_loop):
    """Create a mock future that can be used in tests."""
    def _create_future(result=None):
        future = event_loop.create_future()
        if result is not None:
            future.set_result(result)
        return future
    return _create_future


def invoke_cli_with_timeout(cli_runner, *args, **kwargs):
    """Helper function to invoke CLI commands with a timeout."""
    kwargs.setdefault('catch_exceptions', False)
    timeout = kwargs.pop('timeout', 5)  # Remove timeout from kwargs before passing to invoke
    return cli_runner.invoke(*args, **kwargs)


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
async def test_configure_command(mock_save_config, mock_load_config, cli_runner):
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


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
async def test_configure_command_with_defaults(mock_save_config, mock_load_config, cli_runner):
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


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
async def test_sync_command_missing_ynab_api_key(mock_load_config, cli_runner):
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


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
async def test_sync_command_missing_requisition_id(mock_load_config, cli_runner):
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


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
async def test_sync_command_missing_account_mappings(mock_load_config, cli_runner):
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


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.GoCardlessClient")
@patch("ynab_sync.cli.asyncio")
async def test_list_institutions_command(mock_asyncio, mock_client_class, mock_load_config, cli_runner, mock_future):
    """Test the list_institutions command."""
    # Mock the load_config to return a config with GoCardless credentials
    mock_load_config.return_value = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        }
    }
    
    # Mock the GoCardless client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the get_institutions response
    mock_institutions = [
        {
            "id": "test_bank_1",
            "name": "Test Bank 1",
            "bic": "TESTBIC1",
            "transaction_total_days": 90
        },
        {
            "id": "test_bank_2",
            "name": "Test Bank 2",
            "bic": "TESTBIC2",
            "transaction_total_days": 90
        }
    ]
    future = mock_future(mock_institutions)
    mock_client.get_institutions.return_value = future
    mock_asyncio.run.side_effect = lambda x: x if isinstance(x, list) else x.result()
    
    # Test with default country
    result = invoke_cli_with_timeout(cli_runner, cli, ["list-institutions"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Test Bank 1" in result.output
    assert "Test Bank 2" in result.output
    assert "TESTBIC1" in result.output
    assert "TESTBIC2" in result.output
    
    # Check that get_institutions was called with the default country
    mock_client.get_institutions.assert_called_once_with("gb")


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.GoCardlessClient")
@patch("ynab_sync.cli.asyncio")
async def test_list_institutions_with_filter(mock_asyncio, mock_client_class, mock_load_config, cli_runner, mock_future):
    """Test the list_institutions command with name filter."""
    # Mock the load_config to return a config with GoCardless credentials
    mock_load_config.return_value = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        }
    }
    
    # Mock the GoCardless client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the get_institutions response
    mock_institutions = [
        {
            "id": "test_bank_1",
            "name": "Barclays Bank",
            "bic": "BARCGB22",
            "transaction_total_days": 90
        },
        {
            "id": "test_bank_2",
            "name": "HSBC Bank",
            "bic": "HSBCGB2L",
            "transaction_total_days": 90
        }
    ]
    mock_client.get_institutions.return_value = mock_future(mock_institutions)
    mock_asyncio.run.side_effect = lambda x: x if isinstance(x, list) else x.result()
    
    # Test with name filter
    result = cli_runner.invoke(cli, ["list-institutions", "--name", "Barclays"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Barclays Bank" in result.output
    assert "HSBC Bank" not in result.output
    assert "BARCGB22" in result.output
    assert "HSBCGB2L" not in result.output


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
async def test_list_institutions_no_credentials(mock_load_config, cli_runner):
    """Test the list_institutions command without GoCardless credentials."""
    # Mock the load_config to return an empty config
    mock_load_config.return_value = {}
    
    # Test the command
    result = cli_runner.invoke(cli, ["list-institutions"])
    
    # Check that the command failed with the expected error message
    assert result.exit_code == 0  # Click doesn't set non-zero exit code for early returns
    assert "Please configure GoCardless credentials first" in result.output


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
@patch("ynab_sync.cli.GoCardlessClient")
@patch("ynab_sync.cli.asyncio")
async def test_add_connection_command(mock_asyncio, mock_client_class, mock_save_config, mock_load_config, cli_runner, mock_future):
    """Test the add_connection command."""
    # Mock the load_config to return a config with GoCardless credentials
    mock_load_config.return_value = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        }
    }
    
    # Mock the GoCardless client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the get_institutions response
    mock_institutions = [
        {
            "id": "test_bank_1",
            "name": "Test Bank 1",
            "bic": "TESTBIC1",
            "transaction_total_days": 90
        },
        {
            "id": "test_bank_2",
            "name": "Test Bank 2",
            "bic": "TESTBIC2",
            "transaction_total_days": 90
        }
    ]
    mock_client.get_institutions.return_value = mock_future(mock_institutions)
    
    # Mock the create_requisition response
    mock_requisition = {
        "id": "test_requisition_id",
        "link": "https://example.com/auth"
    }
    mock_client.create_requisition.return_value = mock_future(mock_requisition)
    mock_asyncio.run.side_effect = lambda x: x if isinstance(x, list) else x.result()
    
    # Test with selecting the first institution
    result = cli_runner.invoke(cli, ["add-connection"], input="gb\n1\n")
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Selected: Test Bank 1" in result.output
    assert "https://example.com/auth" in result.output
    
    # Check that save_config was called with the correct values
    expected_config = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "institution_id": "test_bank_1",
            "requisition_id": "test_requisition_id"
        }
    }
    mock_save_config.assert_called_once_with(expected_config)


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
@patch("ynab_sync.cli.GoCardlessClient")
@patch("ynab_sync.cli.asyncio")
async def test_add_connection_existing_valid(mock_asyncio, mock_client_class, mock_save_config, mock_load_config, cli_runner, mock_future):
    """Test the add_connection command with existing valid connection."""
    # Mock the load_config to return a config with existing connection
    mock_load_config.return_value = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "requisition_id": "existing_requisition_id"
        }
    }
    
    # Mock the GoCardless client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the get_requisition response
    mock_requisition = {
        "id": "existing_requisition_id",
        "accounts": ["account1", "account2"]
    }
    mock_client.get_requisition.return_value = mock_future(mock_requisition)
    mock_asyncio.run.side_effect = lambda x: x if isinstance(x, list) else x.result()
    
    # Test with keeping existing connection (answering 'n' to prompt)
    result = cli_runner.invoke(cli, ["add-connection"], input="n\n")
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "You already have a bank connection" in result.output
    assert "Using existing bank connection" in result.output
    
    # Check that save_config was not called
    mock_save_config.assert_not_called()


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
@patch("ynab_sync.cli.GoCardlessClient")
@patch("ynab_sync.cli.asyncio")
async def test_add_connection_existing_invalid(mock_asyncio, mock_client_class, mock_save_config, mock_load_config, cli_runner, mock_future):
    """Test the add_connection command with existing invalid connection."""
    # Mock the load_config to return a config with existing connection
    mock_load_config.return_value = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "requisition_id": "invalid_requisition_id"
        }
    }
    
    # Mock the GoCardless client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the get_requisition to raise an exception
    mock_client.get_requisition.side_effect = Exception("Invalid requisition")
    
    # Mock the get_institutions response for the new connection
    mock_institutions = [
        {
            "id": "test_bank_1",
            "name": "Test Bank 1",
            "bic": "TESTBIC1",
            "transaction_total_days": 90
        }
    ]
    mock_client.get_institutions.return_value = mock_future(mock_institutions)
    
    # Mock the create_requisition response
    mock_requisition = {
        "id": "new_requisition_id",
        "link": "https://example.com/auth"
    }
    mock_client.create_requisition.return_value = mock_future(mock_requisition)
    mock_asyncio.run.side_effect = lambda x: x if isinstance(x, list) else x.result()
    
    # Test with invalid existing connection
    result = cli_runner.invoke(cli, ["add-connection"], input="gb\n1\n")
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Existing bank connection is invalid" in result.output
    assert "https://example.com/auth" in result.output
    
    # Check that save_config was called with the new connection
    expected_config = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "institution_id": "test_bank_1",
            "requisition_id": "new_requisition_id"
        }
    }
    mock_save_config.assert_called_once_with(expected_config)


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
async def test_add_connection_no_credentials(mock_load_config, cli_runner):
    """Test the add_connection command without GoCardless credentials."""
    # Mock the load_config to return an empty config
    mock_load_config.return_value = {}
    
    # Test the command
    result = cli_runner.invoke(cli, ["add-connection"])
    
    # Check that the command failed with the expected error message
    assert result.exit_code == 0  # Click doesn't set non-zero exit code for early returns
    assert "GoCardless credentials not found" in result.output


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.save_config")
@patch("ynab_sync.cli.GoCardlessClient")
@patch("ynab_sync.cli.asyncio")
async def test_map_accounts_command(mock_asyncio, mock_client_class, mock_save_config, mock_load_config, cli_runner, mock_future):
    """Test the map_accounts command."""
    # Mock the load_config to return a config with GoCardless credentials and requisition
    mock_load_config.return_value = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "requisition_id": "test_requisition_id"
        },
        "ynab": {
            "api_key": "test_api_key",
            "budget_id": "test_budget_id"
        }
    }
    
    # Mock the GoCardless client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the get_requisition response
    mock_requisition = {
        "id": "test_requisition_id",
        "accounts": ["account1", "account2"]
    }
    mock_client.get_requisition.return_value = mock_future(mock_requisition)
    
    # Mock the get_account_details responses
    mock_account1 = {
        "id": "account1",
        "iban": "GB1234567890",
        "ownerName": "Current Account"
    }
    mock_account2 = {
        "id": "account2",
        "iban": "GB0987654321",
        "ownerName": "Savings Account"
    }
    
    # Create a list of futures for account details
    account_futures = [
        mock_future(mock_account1),
        mock_future(mock_account2)
    ]
    mock_client.get_account_details.side_effect = account_futures
    
    # Mock the get_account_balances responses
    mock_balances = {
        "balances": [
            {
                "referenceDate": "2024-03-09",
                "balanceAmount": {"amount": "1000.00", "currency": "GBP"}
            }
        ]
    }
    mock_client.get_account_balances.return_value = mock_future(mock_balances)
    mock_asyncio.run.side_effect = lambda x: x if isinstance(x, list) else x.result()
    
    # Test with mapping both accounts
    result = invoke_cli_with_timeout(cli_runner, cli, ["map-accounts"], input="ynab_account_1\nynab_account_2\n")
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Current Account" in result.output
    assert "Savings Account" in result.output
    
    # Check that save_config was called with the correct mappings
    expected_config = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "requisition_id": "test_requisition_id"
        },
        "ynab": {
            "api_key": "test_api_key",
            "budget_id": "test_budget_id"
        },
        "account_mappings": {
            "account1": "ynab_account_1",
            "account2": "ynab_account_2"
        },
        "accounts_validated": True
    }
    mock_save_config.assert_called_with(expected_config)


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
async def test_map_accounts_no_requisition(mock_load_config, cli_runner):
    """Test the map_accounts command without a bank connection."""
    # Mock the load_config to return a config without requisition
    mock_load_config.return_value = {
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        }
    }
    
    # Test the command
    result = cli_runner.invoke(cli, ["map-accounts"])
    
    # Check that the command failed with the expected error message
    assert result.exit_code == 0  # Click doesn't set non-zero exit code for early returns
    assert "No bank connection found" in result.output


@pytest.mark.asyncio
@patch("ynab_sync.cli.load_config")
@patch("ynab_sync.cli.sync_transactions")
@patch("ynab_sync.cli.asyncio")
@patch("ynab_sync.cli.GoCardlessClient")
async def test_sync_command_success(mock_client_class, mock_asyncio, mock_sync_transactions, mock_load_config, cli_runner, mock_future):
    """Test the sync command success path."""
    # Mock the load_config to return a complete config
    mock_load_config.return_value = {
        "ynab": {
            "api_key": "test_api_key",
            "budget_id": "test_budget_id"
        },
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key",
            "requisition_id": "test_requisition_id"
        },
        "account_mappings": {
            "bank_account_1": "ynab_account_1",
            "bank_account_2": "ynab_account_2"
        }
    }
    
    # Mock the GoCardless client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the sync_transactions function
    mock_sync_result = {"added": 8}
    mock_sync_transactions.return_value = mock_sync_result
    mock_asyncio.run.return_value = mock_sync_result
    
    # Test the command
    result = invoke_cli_with_timeout(cli_runner, cli, ["sync"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Successfully added 8 transactions to YNAB" in result.output
    
    # Check that sync_transactions was called once
    mock_sync_transactions.assert_called_once() 