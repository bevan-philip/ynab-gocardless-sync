import click
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, UTC

from .logging_config import configure_logging
from .config import load_config, save_config
from .sync import sync_transactions
from .api import GoCardlessClient

@click.group()
@click.option('--verbose', '-v', count=True, help='Increase verbosity (can be used multiple times)')
def cli(verbose):
    """YNAB Bank Sync Tool - Sync transactions from your bank to YNAB.
    
    Usage flow:
    1. ynab-sync configure - Set up API keys
    2. ynab-sync add-connection - Connect to GoCardless and your bank
    3. ynab-sync map-accounts - Map bank accounts to YNAB accounts
    4. ynab-sync sync - Sync transactions from your bank to YNAB
    """
    # Configure logging based on verbosity
    if verbose == 0:
        configure_logging(logging.WARNING)
    elif verbose == 1:
        configure_logging(logging.INFO)
    else:
        configure_logging(logging.DEBUG)
    pass

@cli.command()
@click.option('--country', default='gb', help='Two-letter country code (e.g. gb, us)')
@click.option('--name', help='Filter institutions by name (case-insensitive partial match)')
def list_institutions(country, name):
    """List available banking institutions."""
    config = load_config()
    if not config.get("gocardless", {}).get("secret_id"):
        click.echo("Please configure GoCardless credentials first using 'ynab-sync configure'")
        return

    client = GoCardlessClient(
        secret_id=config["gocardless"]["secret_id"],
        secret_key=config["gocardless"]["secret_key"]
    )
    
    try:
        institutions = asyncio.run(client.get_institutions(country))
        if name:
            institutions = [
                inst for inst in institutions 
                if name.lower() in inst['name'].lower()
            ]
            
        if not institutions:
            click.echo(f"\nNo institutions found for {country.upper()}" + 
                      (f" matching '{name}'" if name else ""))
            return

        click.echo(f"\nAvailable institutions for {country.upper()}" + 
                  (f" matching '{name}'" if name else "") + ":")
        click.echo("-" * 80)
        for inst in institutions:
            click.echo(f"ID: {inst['id']}")
            click.echo(f"Name: {inst['name']}")
            click.echo(f"BIC: {inst['bic']}")
            click.echo(f"Transaction History: {inst['transaction_total_days']} days")
            click.echo("-" * 80)
    except Exception as e:
        click.echo(f"Error fetching institutions: {str(e)}", err=True)
        raise click.Abort()

@cli.command()
def configure():
    """Configure API keys and settings."""
    # Load existing config
    config = load_config()

    # YNAB Configuration
    click.echo("\n=== YNAB Configuration ===")
    ynab_api_key = click.prompt(
        "YNAB API Key",
        default=config.get("ynab", {}).get("api_key", ""),
    )
    ynab_budget_id = click.prompt(
        "YNAB Budget ID",
        default=config.get("ynab", {}).get("budget_id", "")
    )
    
    # GoCardless Configuration
    click.echo("\n=== GoCardless Configuration ===")
    gocardless_secret_id = click.prompt(
        "GoCardless Secret ID",
        default=config.get("gocardless", {}).get("secret_id", ""),
    )
    gocardless_secret_key = click.prompt(
        "GoCardless Secret Key",
        default=config.get("gocardless", {}).get("secret_key", ""),
    )
    
    # Last Sync Configuration
    click.echo("\n=== Sync Configuration ===")
    last_sync_str = click.prompt(
        "Last Sync Date (YYYY-MM-DD format, e.g. 2023-01-01)",
        default=config.get("last_sync", (datetime.now(UTC) - timedelta(days=7)).date().isoformat())
    )

    config["ynab"]["api_key"] = ynab_api_key
    config["ynab"]["budget_id"] = ynab_budget_id
    config["gocardless"]["secret_id"] = gocardless_secret_id
    config["gocardless"]["secret_key"] = gocardless_secret_key
    config["last_sync"] = last_sync_str
   
    # Save config
    save_config(config)
    click.echo("\nConfiguration saved successfully!")

@cli.command()
def add_connection():
    """Connect to GoCardless and authenticate with your bank."""
    config = load_config()
    
    # Check if we have the necessary configuration
    if not config.get("gocardless", {}).get("secret_id") or not config.get("gocardless", {}).get("secret_key"):
        click.echo("GoCardless credentials not found. Please run 'ynab-sync configure' first.")
        return
    
    # Check if we already have a connection
    if config.get("gocardless", {}).get("requisition_id"):
        # Initialize GoCardless client
        client = GoCardlessClient(
            secret_id=config["gocardless"]["secret_id"],
            secret_key=config["gocardless"]["secret_key"]
        )
        
        # Check if the existing requisition is valid
        try:
            requisition = asyncio.run(client.get_requisition(config["gocardless"]["requisition_id"]))
            if requisition.get("accounts"):
                if click.confirm("You already have a bank connection. Do you want to create a new one?", default=False):
                    # Clear existing connection
                    if "requisition_id" in config["gocardless"]:
                        del config["gocardless"]["requisition_id"]
                    if "institution_id" in config["gocardless"]:
                        del config["gocardless"]["institution_id"]
                    if "account_mappings" in config:
                        del config["account_mappings"]
                    if "accounts_validated" in config:
                        del config["accounts_validated"]
                    save_config(config)
                else:
                    click.echo("Using existing bank connection.")
                    click.echo("You can run 'ynab-sync map-accounts' to update your account mappings.")
                    return
            # If no accounts, the requisition is invalid, so we'll create a new one
        except Exception:
            click.echo("Existing bank connection is invalid. Creating a new one.")
            # Clear existing connection
            if "requisition_id" in config["gocardless"]:
                del config["gocardless"]["requisition_id"]
    
    # Initialize GoCardless client
    client = GoCardlessClient(
        secret_id=config["gocardless"]["secret_id"],
        secret_key=config["gocardless"]["secret_key"]
    )
    
    try:
        # First, let the user select an institution
        country = click.prompt("Enter country code (e.g. gb, us)", default="gb")
        
        # Get institutions
        institutions = asyncio.run(client.get_institutions(country))
        
        if not institutions:
            click.echo(f"No institutions found for {country.upper()}")
            return
        
        # Display institutions
        click.echo("\n=== Available Institutions ===")
        for i, inst in enumerate(institutions, 1):
            click.echo(f"{i}. {inst['name']} ({inst['id']})")
        
        # Let user select an institution
        selection = click.prompt(
            "Select an institution by number",
            type=int,
            default=1
        )
        
        if selection < 1 or selection > len(institutions):
            click.echo("Invalid selection")
            return
        
        selected_institution = institutions[selection - 1]
        click.echo(f"Selected: {selected_institution['name']}")
        
        # Create a requisition
        requisition = asyncio.run(client.create_requisition(
            redirect_url="https://localhost",
            institution_id=selected_institution["id"]
        ))
        
        # Save the institution ID and requisition ID to config
        config["gocardless"]["institution_id"] = selected_institution["id"]
        config["gocardless"]["requisition_id"] = requisition["id"]
        save_config(config)
        
        # The user needs to complete authentication
        click.echo(f"\nPlease complete authentication by visiting: {requisition['link']}")
        click.echo("After authentication, run 'ynab-sync map-accounts' to map your accounts.")
        
    except Exception as e:
        click.echo(f"Error connecting to bank: {str(e)}", err=True)
        raise click.Abort()

@cli.command()
def map_accounts():
    """Configure mappings between bank accounts and YNAB accounts."""
    config = load_config()
    if not config.get("gocardless", {}).get("requisition_id"):
        click.echo("No bank connection found. Please run 'ynab-sync add-connection' first.")
        return

    client = GoCardlessClient(
        secret_id=config["gocardless"]["secret_id"],
        secret_key=config["gocardless"]["secret_key"]
    )
    
    try:
        # Get bank accounts
        requisition = asyncio.run(client.get_requisition(config["gocardless"]["requisition_id"]))
        if not requisition.get("accounts"):
            click.echo("No bank accounts found. Please complete authentication first by running 'ynab-sync add-connection'.")
            return

        # Get account details
        bank_accounts = []
        for account_id in requisition["accounts"]:
            account_details = asyncio.run(client.get_account_details(account_id))
            balances = asyncio.run(client.get_account_balances(account_id))
            
            # Get the most recent balance
            current_balance = None
            if balances.get("balances"):
                # Sort by reference date and get the most recent
                latest_balance = sorted(
                    balances["balances"],
                    key=lambda x: x.get("referenceDate", ""),
                    reverse=True
                )[0]
                current_balance = latest_balance["balanceAmount"]
            
            bank_accounts.append({
                "id": account_id,
                "name": account_details.get("ownerName", "Unknown Account"),
                "iban": account_details.get("iban", "No IBAN"),
                "currency": account_details.get("currency", "Unknown"),
                "status": account_details.get("status", "Unknown"),
                "balance": current_balance
            })

        # Initialize or get existing mappings
        account_mappings = config.get("account_mappings", {})
        
        click.echo("\n=== Account Mapping Configuration ===")
        for bank_account in bank_accounts:
            click.echo(f"\nBank Account:")
            click.echo(f"  Name: {bank_account['name']}")
            click.echo(f"  IBAN: {bank_account['iban']}")
            click.echo(f"  Currency: {bank_account['currency']}")
            click.echo(f"  Status: {bank_account['status']}")
            if bank_account['balance']:
                click.echo(f"  Balance: {bank_account['balance']['amount']} {bank_account['balance']['currency']}")
            ynab_account_id = click.prompt(
                "Enter YNAB Account ID for this bank account",
                type=str,
                default=account_mappings.get(bank_account["id"])
            )
            if ynab_account_id:
                account_mappings[bank_account["id"]] = ynab_account_id

        config["account_mappings"] = account_mappings
        
        # Mark accounts as validated since we just mapped them
        config["accounts_validated"] = True
        
        save_config(config)
        click.echo("\nAccount mappings saved successfully!")
        click.echo("You can now run 'ynab-sync sync' to sync transactions.")

    except Exception as e:
        click.echo(f"Error configuring account mappings: {str(e)}", err=True)
        raise click.Abort()

@cli.command()
def sync():
    """Sync transactions from your bank to YNAB."""
    config = load_config()
    
    # Check if we have the necessary configuration
    if not config.get("ynab", {}).get("api_key"):
        click.echo("YNAB API key not found. Please run 'ynab-sync configure' first.")
        return
        
    if not config.get("gocardless", {}).get("requisition_id"):
        click.echo("No bank connection found. Please run 'ynab-sync add-connection' first.")
        return
        
    if not config.get("account_mappings"):
        click.echo("No account mappings found. Please run 'ynab-sync map-accounts' first.")
        return
    
    try:
        result = asyncio.run(sync_transactions())
        click.echo(f"Successfully added {result['added']} transactions to YNAB.")
    except Exception as e:
        click.echo(f"Error during sync: {str(e)}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli() 