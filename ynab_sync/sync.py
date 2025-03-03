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
        amount = float(txn["transactionAmount"]["amount"])
        if amount < 0:
            amount = abs(amount)  # YNAB expects positive amounts for expenses
            
        ynab_transactions.append({
            "account_id": account_id,
            "date": txn["bookingDate"],  # Already in YYYY-MM-DD format
            "amount": int(amount * 1000),  # Convert to milliunits
            "payee_name": txn.get("debtorName", txn.get("remittanceInformationUnstructured", "Unknown")),
            "import_id": f"gc:{txn['transactionId']}"
        })
    
    return ynab_transactions

async def sync_transactions() -> Dict[str, int]:
    """Sync transactions from GoCardless to YNAB."""
    config = load_config()
    
    # Initialize API clients
    ynab_client = YNABClient(config["ynab"]["api_key"])
    gocardless_client = GoCardlessClient(
        secret_id=config["gocardless"]["secret_id"],
        secret_key=config["gocardless"]["secret_key"]
    )
    
    # Get last sync time
    last_sync = datetime.fromisoformat(config["last_sync"])
    
    # Create a requisition if we don't have one
    if "requisition_id" not in config["gocardless"]:
        requisition = await gocardless_client.create_requisition(
            redirect_url=config["gocardless"]["redirect_url"],
            institution_id=config["gocardless"]["institution_id"]
        )
        config["gocardless"]["requisition_id"] = requisition["id"]
        # Save the requisition ID to config
        save_config(config)
        
        # The user needs to complete authentication
        click.echo(f"\nPlease complete authentication by visiting: {requisition['link']}")
        click.echo("After authentication, run this command again to sync transactions.")
        return {"added": 0}
    
    # Get requisition details to check status and get accounts
    requisition = await gocardless_client.get_requisition(config["gocardless"]["requisition_id"])
    
    if not requisition.get("accounts"):
        click.echo("No accounts found. Please complete authentication first.")
        return {"added": 0}
    
    # Check if we have account mappings
    account_mappings = config.get("account_mappings", {})
    if not account_mappings:
        click.echo("No account mappings found. Please run 'ynab-sync map-accounts' first.")
        return {"added": 0}
    
    # Fetch and process transactions for each mapped account
    total_added = 0
    for bank_account_id, ynab_account_id in account_mappings.items():
        if bank_account_id not in requisition["accounts"]:
            click.echo(f"Warning: Bank account {bank_account_id} not found in current session")
            continue
            
        transactions = await gocardless_client.get_account_transactions(bank_account_id)
        if not transactions:
            continue
            
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