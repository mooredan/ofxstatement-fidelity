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
