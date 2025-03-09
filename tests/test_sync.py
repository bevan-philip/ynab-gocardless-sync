"""Tests for the sync module."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from ynab_sync.sync import prepare_ynab_transactions, sync_transactions


def test_prepare_ynab_transactions(sample_bank_transactions):
    """Test the prepare_ynab_transactions function."""
    # Arrange
    account_id = "test_account_id"
    
    # Act
    result = prepare_ynab_transactions(sample_bank_transactions, account_id)
    
    # Assert
    assert len(result) == 2
    
    # Check first transaction (positive amount)
    assert result[0]["account_id"] == account_id
    assert result[0]["date"] == "2023-01-01"
    assert result[0]["amount"] == 100500  # 100.50 converted to milliunits
    assert result[0]["payee_name"] == "John Doe"
    
    # Check second transaction (negative amount)
    assert result[1]["account_id"] == account_id
    assert result[1]["date"] == "2023-01-02"
    assert result[1]["amount"] == -50250  # -50.25 converted to milliunits
    assert result[1]["payee_name"] == "Grocery Store"


def test_prepare_ynab_transactions_empty():
    """Test prepare_ynab_transactions with empty input."""
    # Arrange
    empty_transactions = {"transactions": {"booked": []}}
    account_id = "test_account_id"
    
    # Act
    result = prepare_ynab_transactions(empty_transactions, account_id)
    
    # Assert
    assert result == []


@pytest.mark.asyncio
@patch("ynab_sync.sync.load_config")
@patch("ynab_sync.sync.update_last_sync")
@patch("ynab_sync.sync.YNABClient")
@patch("ynab_sync.sync.GoCardlessClient.create")
async def test_sync_transactions_success(
    mock_gocardless_create, 
    mock_ynab_client_class, 
    mock_update_last_sync, 
    mock_load_config,
    mock_config,
    sample_bank_transactions,
    mock_ynab_client,
    mock_gocardless_client
):
    """Test successful transaction sync."""
    # Arrange
    mock_load_config.return_value = mock_config
    mock_ynab_client_class.return_value = mock_ynab_client
    mock_gocardless_create.return_value = mock_gocardless_client
    
    # Set up the mock to return sample transactions
    mock_gocardless_client.get_account_transactions.return_value = sample_bank_transactions
    
    # Act
    result = await sync_transactions()
    
    # Assert
    # Check that the API clients were created with correct parameters
    mock_ynab_client_class.assert_called_once_with(mock_config["ynab"]["api_key"])
    mock_gocardless_create.assert_called_once_with(
        secret_id=mock_config["gocardless"]["secret_id"],
        secret_key=mock_config["gocardless"]["secret_key"]
    )
    
    # Check that transactions were fetched for the mapped account
    mock_gocardless_client.get_account_transactions.assert_called_once()
    
    # Check that transactions were created in YNAB
    mock_ynab_client.create_transactions.assert_called_once()
    
    # Check that last sync time was updated
    mock_update_last_sync.assert_called_once()
    
    # Check the result
    assert result["added"] == 2


@pytest.mark.asyncio
@patch("ynab_sync.sync.load_config")
@patch("ynab_sync.sync.update_last_sync")
@patch("ynab_sync.sync.YNABClient")
@patch("ynab_sync.sync.GoCardlessClient.create")
async def test_sync_transactions_no_new_transactions(
    mock_gocardless_create, 
    mock_ynab_client_class, 
    mock_update_last_sync, 
    mock_load_config,
    mock_config,
    mock_ynab_client,
    mock_gocardless_client
):
    """Test sync when there are no new transactions."""
    # Arrange
    mock_load_config.return_value = mock_config
    mock_ynab_client_class.return_value = mock_ynab_client
    mock_gocardless_create.return_value = mock_gocardless_client
    
    # Set up the mock to return empty transactions
    mock_gocardless_client.get_account_transactions.return_value = {"transactions": {"booked": []}}
    
    # Act
    result = await sync_transactions()
    
    # Assert
    # Check that transactions were fetched
    mock_gocardless_client.get_account_transactions.assert_called_once()
    
    # Check that no transactions were created in YNAB
    mock_ynab_client.create_transactions.assert_not_called()
    
    # Check that last sync time was still updated
    mock_update_last_sync.assert_called_once()
    
    # Check the result
    assert result["added"] == 0


@pytest.mark.asyncio
@patch("ynab_sync.sync.load_config")
@patch("ynab_sync.sync.update_last_sync")
@patch("ynab_sync.sync.YNABClient")
@patch("ynab_sync.sync.GoCardlessClient.create")
async def test_sync_transactions_unmapped_account(
    mock_gocardless_create, 
    mock_ynab_client_class, 
    mock_update_last_sync, 
    mock_load_config,
    mock_config,
    mock_ynab_client,
    mock_gocardless_client
):
    """Test that unmapped accounts are skipped."""
    # Arrange
    mock_load_config.return_value = mock_config
    mock_ynab_client_class.return_value = mock_ynab_client
    mock_gocardless_create.return_value = mock_gocardless_client
    
    # Set up the mock to return empty transactions for the mapped account
    mock_gocardless_client.get_account_transactions.return_value = {"transactions": {"booked": []}}
    
    # Act
    result = await sync_transactions()
    
    # Assert
    # Check that get_account_transactions was only called for mapped accounts
    # (bank_account_2 is unmapped in the mock_config)
    assert mock_gocardless_client.get_account_transactions.call_count == 1
    
    # Check that last sync time was updated
    mock_update_last_sync.assert_called_once() 