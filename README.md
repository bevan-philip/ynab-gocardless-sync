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
- GoCardless Secret ID
- GoCardless Secret Key

```bash
ynab-sync add-connection
```
Will perform the actual connection with GoCardless.

```bash
ynab-sync map-accounts
```

Map your bank accounts with the relevant YNAB account ID (the account ID can be found by looking at the URL when viewing an account in the browser).

## Usage

To sync transactions:

```bash
ynab-sync sync
```

## Running tests
This project uses pytest.
```bash
uv run -m pytest --cov=ynab-sync
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

(It might be better to only link your current accounts.)

### How often can I do this?
[The GoCardless API documentation](https://bankaccountdata.zendesk.com/hc/en-gb/articles/11528933493916-Bank-Account-Data-API-Usage-how-is-your-usage-number-calculated).


### Renewing API access
Unclear as I haven't gone through this, but you should be able to run `add-connection` again, and you'll be able to create a new requisition (connection).

