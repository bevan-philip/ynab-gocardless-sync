"""Tests for the config module."""

import os
import yaml
import pytest
import asyncio
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from ynab_sync.config import (
    load_config, 
    save_config, 
    update_last_sync, 
    ensure_config_dir, 
    CONFIG_DIR, 
    CONFIG_FILE
)


@pytest.mark.asyncio
@patch("ynab_sync.config.CONFIG_FILE")
@patch("ynab_sync.config.ensure_config_dir")
async def test_load_config_file_exists(mock_ensure_dir, mock_config_file):
    """Test load_config when config file exists."""
    # Arrange
    mock_config_file.exists.return_value = True
    mock_data = {
        "last_sync": "2023-01-01T00:00:00",
        "ynab": {
            "budget_id": "test_budget_id",
            "api_key": "test_api_key"
        },
        "gocardless": {
            "secret_id": "test_secret_id",
            "secret_key": "test_secret_key"
        }
    }
    
    # Mock the open function to return our test data
    m = mock_open(read_data=yaml.dump(mock_data))
    with patch("builtins.open", m):
        # Act
        if asyncio.iscoroutinefunction(load_config):
            result = await load_config()
        else:
            result = load_config()
        
        # Assert
        mock_ensure_dir.assert_called_once()
        assert result == mock_data


@pytest.mark.asyncio
@patch("ynab_sync.config.CONFIG_FILE")
@patch("ynab_sync.config.ensure_config_dir")
@patch("ynab_sync.config.datetime")
async def test_load_config_file_not_exists(mock_datetime, mock_ensure_dir, mock_config_file):
    """Test load_config when config file does not exist."""
    # Arrange
    mock_config_file.exists.return_value = False
    mock_now = datetime(2023, 1, 8, 0, 0, 0)
    mock_datetime.utcnow.return_value = mock_now
    mock_datetime.isoformat = datetime.isoformat
    
    # The expected default config with a date 7 days ago
    expected_config = {
        "last_sync": (mock_now - timedelta(days=7)).isoformat(),
        "ynab": {
            "budget_id": None,
            "account_id": None,
        }
    }
    
    # Act
    if asyncio.iscoroutinefunction(load_config):
        result = await load_config()
    else:
        result = load_config()
    
    # Assert
    mock_ensure_dir.assert_called_once()
    assert result == expected_config


@pytest.mark.asyncio
@patch("ynab_sync.config.CONFIG_FILE")
@patch("ynab_sync.config.ensure_config_dir")
async def test_save_config(mock_ensure_dir, mock_config_file):
    """Test save_config function."""
    # Arrange
    config = {
        "last_sync": "2023-01-01T00:00:00",
        "ynab": {
            "budget_id": "test_budget_id"
        }
    }
    
    # Mock the open function
    mock_file = mock_open()
    
    # Act
    with patch("builtins.open", mock_file):
        if asyncio.iscoroutinefunction(save_config):
            await save_config(config)
        else:
            save_config(config)
    
    # Assert
    mock_ensure_dir.assert_called_once()
    mock_file.assert_called_once_with(mock_config_file, "w")
    mock_file().write.assert_called()  # Check that something was written


@pytest.mark.asyncio
@patch("ynab_sync.config.load_config")
@patch("ynab_sync.config.save_config")
@patch("ynab_sync.config.datetime")
async def test_update_last_sync(mock_datetime, mock_save_config, mock_load_config):
    """Test update_last_sync function."""
    # Arrange
    mock_now = datetime(2023, 1, 1, 0, 0, 0)
    mock_datetime.utcnow.return_value = mock_now
    mock_datetime.isoformat = datetime.isoformat
    
    mock_config = {
        "last_sync": "2022-12-25T00:00:00",
        "ynab": {
            "budget_id": "test_budget_id"
        }
    }
    mock_load_config.return_value = mock_config
    
    # Act
    if asyncio.iscoroutinefunction(update_last_sync):
        await update_last_sync()
    else:
        update_last_sync()
    
    # Assert
    mock_load_config.assert_called_once()
    
    # Check that save_config was called with updated last_sync
    expected_config = mock_config.copy()
    expected_config["last_sync"] = mock_now.isoformat()
    mock_save_config.assert_called_once_with(expected_config)


@pytest.mark.asyncio
@patch("ynab_sync.config.CONFIG_DIR")
async def test_ensure_config_dir(mock_config_dir):
    """Test ensure_config_dir function."""
    # Act
    if asyncio.iscoroutinefunction(ensure_config_dir):
        await ensure_config_dir()
    else:
        ensure_config_dir()
    
    # Assert
    mock_config_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True) 