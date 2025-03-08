import asyncio
from datetime import datetime
from typing import List, Dict, Any

from .config import load_config, update_last_sync, save_config
from .api import YNABClient, GoCardlessClient
import click

def prepare_ynab_transactions(
    bank_transactions: Dict[str, List[Dict[str, Any]]],
    account_id: str
) -> List[Dict[str, Any]]:
    """Convert bank transactions to YNAB format."""
    ynab_transactions = []
    
    # Process booked transactions
    for txn in bank_transactions.get("transactions", {}).get("booked", []):
        # Convert amount from string to float and handle negative amounts
        ynab_transactions.append({
            "account_id": account_id,
            "date": txn["bookingDate"],  # Already in YYYY-MM-DD format
            "amount": int(float(txn["transactionAmount"]["amount"]) * 1000),  # Convert to milliunits
            "payee_name": txn.get("debtorName", txn.get("remittanceInformationUnstructured", "Unknown")),
        })
    
    return ynab_transactions

async def sync_transactions() -> Dict[str, int]:
    """Sync transactions from GoCardless to YNAB."""
    config = load_config()
    
    # Initialize API clients
    ynab_client = YNABClient(config["ynab"]["api_key"])
    gocardless_client = await GoCardlessClient.create(
        secret_id=config["gocardless"]["secret_id"],
        secret_key=config["gocardless"]["secret_key"]
    )
    
    # Get last sync time
    last_sync = datetime.fromisoformat(config["last_sync"])
    last_sync_iso = last_sync.date().isoformat()  # Format as YYYY-MM-DD for the API
    
    # Get account mappings
    account_mappings = config.get("account_mappings", {})
    
    # Fetch and process transactions for each mapped account
    total_added = 0
    for bank_account_id, ynab_account_id in account_mappings.items():
        if ynab_account_id == "unmapped":
            continue

        click.echo(f"Fetching transactions for account {bank_account_id} since {last_sync_iso}")
        
        transactions = await gocardless_client.get_account_transactions(
            bank_account_id,
            date_from=last_sync_iso
        )
        
        if not transactions:
            continue
            
        click.echo(f"Fetched transactions since {last_sync_iso} for account {bank_account_id}")
        
        ynab_transactions = prepare_ynab_transactions(
            transactions,
            ynab_account_id
        )

        if not ynab_transactions:
            continue
            
        result = await ynab_client.create_transactions(
            config["ynab"]["budget_id"],
            ynab_transactions
        )

        total_added += len(result.get("transaction_ids", []))
    
    # Update last sync time on success
    update_last_sync()
    
    return {
        "added": total_added
    } 
