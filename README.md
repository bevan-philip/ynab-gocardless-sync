# YNAB Bank Sync Tool

A command-line tool to sync bank transactions from Chase (via GoCardless) to YNAB (You Need a Budget).

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

## Security note
Your API keys are stored on disk at  ~/.ynab_sync/config.yaml.

## FAQ
### Can I sync multiple banks?
Not at the moment. You could probably manually swap out the needed entries in the config.yaml file to make it work.

### Using Chase Bank UK
- Chase Bank UK is the one bank this tool has been actually tested on.
- You need to perform the actual linking process on your phone: so send the GoCardless link to your phone, somehow.

### Does this link transactions between accounts?
No, you'll have to manually link those transactions in YNAB. This sadly also means it'll duplicate transactions between accounts on both ends.

### How often can I do this?
[The GoCardless API documentation](https://bankaccountdata.zendesk.com/hc/en-gb/articles/11528933493916-Bank-Account-Data-API-Usage-how-is-your-usage-number-calculated).