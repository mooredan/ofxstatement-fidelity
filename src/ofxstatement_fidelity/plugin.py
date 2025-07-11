import sys
import csv

# from typing import Iterable

from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
# from ofxstatement.parser import StatementParser
# from ofxstatement.statement import Statement, StatementLine
# from ofxstatement.statement import StatementLine


class FidelityPlugin(Plugin):
    """Sample plugin (for developers only)"""

    def get_parser(self, filename) -> "FidelityParser":
        fh = open(filename, "r", encoding='utf-8')
        parser = FidelityParser(fh)
        return parser


# class FidelityParser(CsvStatementParser[str]):
# class FidelityParser(CsvStatementParser[str]):
class FidelityParser(CsvStatementParser):

    date_format = "%d/%m/%Y"
    mappings = {
            'date': 1,
            'memo': 2
    }



    def __init__(self, f):
        super().__init__(f)
    #     self.filename = filename
        # msg = f"__init__ : {filename}"
        msg = f"__init__ :"
        print(msg, file=sys.stderr)

    # def parse(self) -> Statement:
    #     """Main entry point for parsers

    #     super() implementation will call to split_records and parse_record to
    #     process the file.
    #     """
    #       
    #     with open(self.filename, "r") as f:
    #         return super().parse()


    # def split_records(self) -> Iterable[str]:
    def split_records(self):
        """Return iterable object consisting of a line per transaction"""
        msg = f"split_records"
        print(msg, file=sys.stderr)
        return []


    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object"""
        msg = f"parse_record"
        print(msg, file=sys.stderr)
        return StatementLine()
