import os

from ofxstatement.ui import UI

from ofxstatement_fidelity.plugin import FidelityPlugin


def test_fidelity() -> None:
    plugin = FidelityPlugin(UI(), {})
    here = os.path.dirname(__file__)
    fidelity_filename = os.path.join(here, "fidelity-statement.csv")

    parser = plugin.get_parser(fidelity_filename)
    statement = parser.parse()

    assert statement is not None
