import os
import yaml
import keyring
from datetime import datetime, timedelta, UTC
from pathlib import Path

CONFIG_DIR = Path.home() / ".ynab_sync"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

def ensure_config_dir():
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    """Load configuration from file and keyring."""
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        return {
            "last_sync": (datetime.now(UTC) - timedelta(days=7)).date().isoformat(),
            "ynab": {
                "budget_id": None,
                "account_id": None,
            }
        }
    
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)

    # Load sensitive data from keyring
    # config["ynab"]["api_key"] = keyring.get_password("ynab", "api_key")
    # config["gocardless"] = {
    #     "token": keyring.get_password("gocardless", "token")
    # }

    return config

def save_config(config):
    """Save configuration to file and keyring."""
    ensure_config_dir()
    
    # Extract sensitive data before saving to file
    # ynab_api_key = config["ynab"].pop("api_key", None)
    # gocardless_token = config["gocardless"].pop("token", None)
    
    # Save non-sensitive data to file
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)
    
    # Save sensitive data to keyring
    # if ynab_api_key:
    #     keyring.set_password("ynab", "api_key", ynab_api_key)
    # if gocardless_token:
    #     keyring.set_password("gocardless", "token", gocardless_token)
    
    # # Restore sensitive data in config dict
    # if ynab_api_key:
    #     config["ynab"]["api_key"] = ynab_api_key
    # if gocardless_token:
    #     config["gocardless"]["token"] = gocardless_token

def update_last_sync():
    """Update the last sync time in the configuration."""
    config = load_config()
    config["last_sync"] = datetime.now(UTC).date().isoformat()
    save_config(config) 