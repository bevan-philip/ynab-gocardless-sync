"""Tests for the API module."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from ynab_sync.api import YNABClient, GoCardlessClient, log_and_raise_for_status


@pytest.mark.asyncio
async def test_ynab_client_create_transactions():
    """Test YNABClient.create_transactions method."""
    # Arrange
    api_key = "test_api_key"
    budget_id = "test_budget_id"
    transactions = [
        {
            "account_id": "account1",
            "date": "2023-01-01",
            "amount": 10000,
            "payee_name": "Test Payee"
        }
    ]
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"transaction_ids": ["id1"]}
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response
    
    # Create client with mocked httpx client
    ynab_client = YNABClient(api_key)
    ynab_client.client = mock_client
    
    # Act
    result = await ynab_client.create_transactions(budget_id, transactions)
    
    # Assert
    mock_client.post.assert_called_once_with(
        f"{ynab_client.BASE_URL}/budgets/{budget_id}/transactions",
        headers=ynab_client.headers,
        json={"transactions": transactions}
    )
    assert result == {"transaction_ids": ["id1"]}


@pytest.mark.asyncio
async def test_gocardless_client_create():
    """Test GoCardlessClient.create class method."""
    # Arrange
    secret_id = "test_secret_id"
    secret_key = "test_secret_key"
    
    # Mock the get_access_token method
    with patch.object(GoCardlessClient, "get_access_token", AsyncMock()) as mock_get_token:
        # Act
        client = await GoCardlessClient.create(secret_id, secret_key)
        
        # Assert
        assert client.secret_id == secret_id
        assert client.secret_key == secret_key
        mock_get_token.assert_called_once()


@pytest.mark.asyncio
async def test_gocardless_client_get_access_token():
    """Test GoCardlessClient.get_access_token method."""
    # Arrange
    secret_id = "test_secret_id"
    secret_key = "test_secret_key"
    access_token = "test_access_token"
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"access": access_token}
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response
    
    # Create client with mocked httpx client
    client = GoCardlessClient(secret_id, secret_key)
    client.client = mock_client
    
    # Act
    await client.get_access_token()
    
    # Assert
    mock_client.post.assert_called_once_with(
        f"{client.BASE_URL}/token/new/",
        headers=client.headers,
        json={
            "secret_id": secret_id,
            "secret_key": secret_key
        }
    )
    assert client.headers["Authorization"] == f"Bearer {access_token}"


@pytest.mark.asyncio
async def test_gocardless_client_get_account_transactions():
    """Test GoCardlessClient.get_account_transactions method."""
    # Arrange
    account_id = "test_account_id"
    date_from = "2023-01-01"
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"transactions": {"booked": []}}
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    
    # Create client with mocked httpx client
    client = GoCardlessClient("test_id", "test_key")
    client.client = mock_client
    
    # Act
    result = await client.get_account_transactions(account_id, date_from)
    
    # Assert
    mock_client.get.assert_called_once_with(
        f"{client.BASE_URL}/accounts/{account_id}/transactions/",
        headers=client.headers,
        params={"date_from": date_from}
    )
    assert result == {"transactions": {"booked": []}}


def test_log_and_raise_for_status_success():
    """Test log_and_raise_for_status with a successful response."""
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    
    # Act & Assert - should not raise an exception
    log_and_raise_for_status(mock_response)
    mock_response.raise_for_status.assert_called_once()


@patch("ynab_sync.api.logger")
def test_log_and_raise_for_status_error(mock_logger):
    """Test log_and_raise_for_status with an error response."""
    # Arrange
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.headers = {"Content-Type": "application/json"}
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.reason_phrase = "Bad Request"
    mock_response.text = "Error details"
    mock_response.url = "https://api.example.com/endpoint"
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.request = mock_request
    
    # Create a proper HTTPStatusError
    error = httpx.HTTPStatusError(
        "Error",
        request=mock_request,
        response=mock_response
    )
    mock_response.raise_for_status.side_effect = error
    
    # Act & Assert - should raise the exception
    with pytest.raises(httpx.HTTPStatusError):
        log_and_raise_for_status(mock_response)
    
    # Verify that the logger was called
    mock_logger.error.assert_called_once() 