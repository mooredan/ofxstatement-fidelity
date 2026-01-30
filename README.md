# ofxstatement-fidelity

A plugin for [ofxstatement](https://github.com/kedder/ofxstatement) that processes **Fidelity Investments** CSV files ("Activity & Orders") and converts them to OFX format. This allows you to import your Fidelity investment history into personal accounting software like **GnuCash**, **HomeBank**, or **MoneyWiz**.

## Features

- **Robust Parsing:** Handles standard Fidelity CSV exports, including US-style number formatting (e.g., `"1,234.56"`), Excel BOMs, and various date formats.
- **Stable IDs:** Generates unique transaction IDs based on the date and chronological sorting. This ensures that `20250101-1` is always the same transaction, preventing duplicates when you import the same date range twice.
- **Smart Mapping:** Supports a wide range of transaction types:
  - **Buys/Sells:** Stocks, ETFs, Mutual Funds.
  - **Income:** Dividends (Cash or Reinvested), Interest.
  - **Transfers:** EFT, Direct Deposit, Direct Debit.
  - **Fees:** Commissions, Foreign Tax, ADRA Fees.

## Installation

### For Users
If you simply want to use the plugin, install it directly from the source:

```bash
pip3 install --user .

```

### For Developers

To set up a development environment to modify the code or run tests:

```bash
# Install in editable mode
pip3 install --user -e .

# Install build/test dependencies
pip3 install build pytest mypy

```

*(Note: If you prefer `pipenv`, you can still use `pipenv sync --dev` and `pipenv shell` as configured in the Pipfile.)*

## Configuration

After installation, configure `ofxstatement` to use this plugin. Add the following section to your configuration file (usually located at `~/.config/ofxstatement/config.ini`):

```ini
[fidelity]
plugin = fidelity
currency = USD
account = fidelity

```

## Usage

### 1. Download CSV from Fidelity

1. Log in to [Fidelity.com](https://www.fidelity.com).
2. Navigate to **Accounts & Trade** > **Portfolio**.
3. Select the specific account you want to export.
4. Click on the **Activity & Orders** tab.
5. Select the **Time Period** (e.g., "Past 90 days" or "Custom").
6. Click the **Download** link (usually at the top right of the transaction list).
7. Save the file (e.g., `History_for_Account_123456789.csv`).

### 2. Convert to OFX

Run the `ofxstatement` tool:

```bash
ofxstatement convert -t fidelity History_for_Account_123456789.csv history.ofx

```

### 3. Import

Import the resulting `history.ofx` file into GnuCash or your preferred finance software.

## Known Limitations

### Splits and Spin-offs

Fidelity does not provide ratio information for stock splits in their CSV export, which is required for the OFX `<SPLIT>` element. Additionally, GnuCash has limited support for importing OFX `<SPLIT>` elements.

To ensure data is at least imported, this plugin generates `<TRANSFER>` transactions for splits and spin-offs. You will likely see a warning or a generic transfer in your ledger.

**Recommendation for GnuCash:**
A common approach is to manually edit the imported transaction:

1. Treat a split (e.g., 4:1 on 100 shares) as a net 300 share transfer.
2. Adjust the transaction to:
* **-100 shares** at a sale price of the remaining cost basis.
* **+400 shares** at a buy price of the remaining cost basis.



This preserves the per-share gain calculations, though the date may not perfectly align for long-term capital gain tax tracking.

## Development & Contributing

### Running Tests

This project uses `pytest` and a `Makefile` for convenience. The test suite includes an iterative runner that checks all CSV files found in the `tests/` directory.

```bash
make test

```

### Packaging

To build a distributable wheel:

```bash
python3 -m build

```

### Reporting Bugs & Missing Transactions

If you encounter a transaction type that causes a crash or is not parsed correctly:

1. **Obfuscate your data:** Do **not** upload raw financial statements to GitHub. Use the included tool to scrub personal data (Account IDs, Balances, Descriptions):
```bash
python3 tools/obfuscate.py ~/Downloads/History_for_Account_REAL.csv

```


This creates a safe version (e.g., `History_for_Account_TEST1234.csv`) with randomized values and sanitized strings.
2. **Verify:** Open the output file to ensure no PII remains.
3. **Submit:** Open an issue and attach the obfuscated CSV (or the specific line causing the error) so we can add the missing regex mapping.

## References

* [OFX Specification (v2.3)](https://financialdataexchange.org/common/Uploaded%20files/OFX%20files/OFX%20Banking%20Specification%20v2.3.pdf)
* [ofxstatement Documentation](https://github.com/kedder/ofxstatement)

```

