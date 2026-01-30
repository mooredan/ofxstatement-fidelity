import os
import glob
import pytest
from ofxstatement.ui import UI
from ofxstatement_fidelity.plugin import FidelityPlugin

# Dynamically find all CSV files in the tests directory
HERE = os.path.dirname(__file__)
CSV_FILES = glob.glob(os.path.join(HERE, "*.csv"))

@pytest.mark.parametrize("filename", CSV_FILES)
def test_fidelity_csv_parsing(filename):
    """
    Run the parser against every CSV file found in the tests/ directory.
    """
    # SKIP empty files (like the ghost file if you didn't delete it)
    # to prevent the "min() arg is empty" crash
    if os.path.getsize(filename) == 0:
        pytest.skip(f"Skipping empty file: {filename}")

    plugin = FidelityPlugin(UI(), {})
    parser = plugin.get_parser(filename)
    
    statement = parser.parse()

    # Basic Validations
    assert statement is not None
    assert statement.broker_id == "Fidelity"
    assert statement.currency == "USD"
    
    # Ensure we actually parsed some lines (assuming test files aren't empty)
    assert len(statement.invest_lines) > 0, f"No transactions found in {filename}"

    # Verify every line has the critical fields required by OFX
    for line in statement.invest_lines:
        line.assert_valid()
        assert line.id is not None
        assert line.date is not None
        assert line.amount is not None
