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
   pip install -e .
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

## Development

This project uses Python 3.13+ and the following key dependencies:
- httpx: For HTTP API calls
- keyring: For secure credential storage
- pyyaml: For configuration files
- click: For CLI interface

## License

MIT License
