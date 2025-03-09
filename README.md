# YNAB Chase Sync

A tool to sync transactions from Chase bank to YNAB (You Need A Budget) using the GoCardless API.

## Installation

```bash
pip install -r requirements.txt
```

For development:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

## Usage

```bash
python -m ynab_sync
```

## Testing

This project uses pytest for testing. To run the tests:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage reporting
python run_tests.py
```

## Test Structure

- `tests/conftest.py`: Common fixtures for tests
- `tests/test_api.py`: Tests for API clients
- `tests/test_config.py`: Tests for configuration handling
- `tests/test_sync.py`: Tests for transaction synchronization

## Coverage Reports

After running tests with coverage (using `run_tests.py`), you can view the HTML coverage report in the `coverage_html` directory.

## Configuration

Run the following command to set up your credentials and configuration:

```bash
ynab-sync configure
```