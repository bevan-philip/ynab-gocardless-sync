# YNAB Bank Sync Tool

A command-line tool to automatically sync bank transactions from Chase (via GoCardless) to YNAB (You Need a Budget).

## Features

- Secure credential storage using system keyring
- Automatic transaction syncing
- Duplicate transaction prevention
- Configurable sync settings

## Installation

1. Clone this repository
2. Install dependencies:

```bash
uv sync
```

## To run,
```bash
uv run -m ynab_sync --help
```

## Configuration

Run the following command to set up your credentials and configuration:

```bash
ynab-sync configure
```

You'll need:
- YNAB API Key (from YNAB settings)
- YNAB Budget ID
- YNAB Account ID
- GoCardless access token (will be obtained via OAuth flow)

## Usage

To sync transactions:

```bash
ynab-sync sync
```
