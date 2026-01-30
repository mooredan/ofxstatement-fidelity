from unittest.mock import patch, mock_open
from decimal import Decimal
from ofxstatement_fidelity.plugin import FidelityCSVParser

def test_parse_decimal_us_format():
    """
    Ensure the parser handles US-style numbers with thousands separators.
    Input: "1,234.56" -> Expected: Decimal("1234.56")
    """
    parser = FidelityCSVParser("dummy_filename")
    
    # This input mimics a Fidelity CSV column with a comma
    raw_value = "1,234.56"
    
    expected = Decimal("1234.56")
    actual = parser.parse_decimal(raw_value)
    
    assert actual == expected


def test_parse_decimal_negative_us_format():
    """
    Ensure the parser handles negative US-style numbers with thousands separators.
    Input: "-1,234.56" -> Expected: Decimal("-1234.56")
    """
    parser = FidelityCSVParser("dummy_filename")
    
    # Input mimicking a negative value in Fidelity CSV
    raw_value = "-1,234.56"
    
    expected = Decimal("-1234.56")
    actual = parser.parse_decimal(raw_value)
    
    assert actual == expected



def test_parse_record_filters_invalid_rows():
    """
    Ensure the parser consistently skips headers, footers, and garbage lines
    by validating the date column, rather than relying on brittle string checks.
    """
    parser = FidelityCSVParser("dummy.csv")
    
    # A standard 13-column row helper
    def make_row(col0):
        return [col0] + [""] * 12

    # Case 1: The standard Header row
    # Old logic caught this with: if line[0] == "Run Date"
    assert parser.parse_record(make_row("Run Date")) is None

    # Case 2: A comment/disclaimer line (often starts with quote in raw text)
    # Old logic caught this with: if line[0][:1] == '"'
    assert parser.parse_record(make_row("The information provided...")) is None

    # Case 3: A valid date (Should NOT return None)
    # We need a mostly valid row to avoid crashing later in the function
    valid_row = ["01/01/2023", "Action", "Sym", "Desc", "Type", "1", "10.00", "0", "0", "0", "10.00", "100", ""]
    result = parser.parse_record(valid_row)
    assert result is not None
    assert result.date.year == 2023


def test_parse_opens_file_correctly():
    """
    Ensure the file is opened with 'utf-8-sig' (to handle BOM)
    and newline='' (required by the csv module).
    """
    # We need at least one valid row so the parser doesn't crash 
    # when calculating min/max dates at the end.
    csv_content = (
        "Run Date,Action,Symbol,Description,Type,Quantity,Price,Commission,Fees,Accrued Interest,Amount,Cash Balance,Settlement Date\n"
        "01/01/2023,YOU BOUGHT AAPL,SYM,Desc,Cash,1,10,0,0,0,10,100,\n"
    )
    
    with patch("builtins.open", mock_open(read_data=csv_content)) as mock_file:
        parser = FidelityCSVParser("dummy.csv")
        parser.parse()
        
        # Verify open was called with specific arguments
        mock_file.assert_called_with("dummy.csv", "r", encoding="utf-8-sig", newline="")

