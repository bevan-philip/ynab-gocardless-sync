import click
import asyncio
from typing import Optional, Dict, Any

from .config import load_config, save_config
from .sync import sync_transactions
from .api import GoCardlessClient

@click.group()
def cli():
    """YNAB Bank Sync Tool - Sync transactions from Chase to YNAB."""
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
    """Configure YNAB and GoCardless credentials."""
    config = load_config()
    
    # Get YNAB credentials
    click.echo("\n=== YNAB Configuration ===")
    config["ynab"] = config.get("ynab", {})
    config["ynab"]["api_key"] = click.prompt(
        "Enter your YNAB API key",
        type=str,
        default=config["ynab"].get("api_key")
    )
    config["ynab"]["budget_id"] = click.prompt(
        "Enter your YNAB Budget ID",
        type=str,
        default=config["ynab"].get("budget_id")
    )
    
    # Get GoCardless credentials
    click.echo("\n=== GoCardless Configuration ===")
    config["gocardless"] = {
        "secret_id": click.prompt(
            "Enter your GoCardless Secret ID",
            type=str,
            default=config.get("gocardless", {}).get("secret_id")
        ),
        "secret_key": click.prompt(
            "Enter your GoCardless Secret Key",
            type=str,
            default=config.get("gocardless", {}).get("secret_key")
        ),
        "institution_id": click.prompt(
            "Enter your GoCardless Institution ID (e.g. REVOLUT_REVOGB21)",
            type=str,
            default=config.get("gocardless", {}).get("institution_id")
        ),
        "redirect_url": "https://localhost:8000",
    }
    
    # Initialize account mappings if not present
    config["account_mappings"] = config.get("account_mappings", {})
    
    save_config(config)
    click.echo("\nConfiguration saved successfully!")
    click.echo("\nNext steps:")
    click.echo("1. Run 'ynab-sync sync' to authenticate with your bank")
    click.echo("2. Run 'ynab-sync map-accounts' to set up account mappings")

@cli.command()
def map_accounts():
    """Configure mappings between bank accounts and YNAB accounts."""
    config = load_config()
    if not config.get("gocardless", {}).get("requisition_id"):
        click.echo("Please run 'ynab-sync sync' first to authenticate with your bank")
        return

    client = GoCardlessClient(
        secret_id=config["gocardless"]["secret_id"],
        secret_key=config["gocardless"]["secret_key"]
    )
    
    try:
        # Get bank accounts
        requisition = asyncio.run(client.get_requisition(config["gocardless"]["requisition_id"]))
        if not requisition.get("accounts"):
            click.echo("No bank accounts found. Please complete authentication first.")
            return

        # Get account details
        bank_accounts = []
        for account_id in requisition["accounts"]:
            account_details = asyncio.run(client.get_account_details(account_id))
            bank_accounts.append({
                "id": account_id,
                "name": account_details.get("name", "Unknown Account"),
                "iban": account_details.get("iban", "No IBAN")
            })

        # Initialize or get existing mappings
        account_mappings = config.get("account_mappings", {})
        
        click.echo("\n=== Account Mapping Configuration ===")
        for bank_account in bank_accounts:
            click.echo(f"\nBank Account: {bank_account['name']} ({bank_account['iban']})")
            ynab_account_id = click.prompt(
                "Enter YNAB Account ID for this bank account",
                type=str,
                default=account_mappings.get(bank_account["id"])
            )
            if ynab_account_id:
                account_mappings[bank_account["id"]] = ynab_account_id

        config["account_mappings"] = account_mappings
        save_config(config)
        click.echo("\nAccount mappings saved successfully!")

    except Exception as e:
        click.echo(f"Error configuring account mappings: {str(e)}", err=True)
        raise click.Abort()

@cli.command()
def sync():
    """Sync transactions from Chase to YNAB."""
    try:
        result = asyncio.run(sync_transactions())
        click.echo(f"Successfully added {result['added']} transactions to YNAB.")
    except Exception as e:
        click.echo(f"Error during sync: {str(e)}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli() 