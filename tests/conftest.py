"""Common test fixtures for ynab_sync tests."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, UTC

from ynab_sync.api import YNABClient, GoCardlessClient


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "last_sync": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
        "ynab": {
            "api_key": "test_api_key",
            "budget_id": "test_budget_id",
        },
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        },
        "account_mappings": {
            "bank_account_1": "ynab_account_1",
            "bank_account_2": "unmapped"
        }
    }


@pytest.fixture
def mock_ynab_client():
    """Mock YNABClient for testing."""
    client = AsyncMock(spec=YNABClient)
    client.create_transactions = AsyncMock(return_value={"transaction_ids": ["id1", "id2"]})
    return client


@pytest.fixture
def mock_gocardless_client():
    """Mock GoCardlessClient for testing."""
    client = AsyncMock(spec=GoCardlessClient)
    client.get_account_transactions = AsyncMock()
    return client


@pytest.fixture
def sample_bank_transactions():
    """Sample bank transactions for testing."""
    return {
        "transactions": {
            "booked": [
                {
                    "bookingDate": "2023-01-01",
                    "transactionAmount": {"amount": "100.50", "currency": "GBP"},
                    "debtorName": "John Doe",
                    "remittanceInformationUnstructured": "Payment for services"
                },
                {
                    "bookingDate": "2023-01-02",
                    "transactionAmount": {"amount": "-50.25", "currency": "GBP"},
                    "remittanceInformationUnstructured": "Grocery Store"
                }
            ],
            "pending": []
        }
    } 