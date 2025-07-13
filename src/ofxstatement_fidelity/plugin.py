import sys

from os import path

from decimal import Decimal, Decimal as D
from datetime import datetime
import re
from typing import Dict, Optional, Any, Iterable, List, TextIO, TypeVar, Generic

from ofxstatement.plugin import Plugin
from ofxstatement.parser import StatementParser

# from ofxstatement.parser import CsvStatementParser
from ofxstatement.parser import AbstractStatementParser
from ofxstatement.statement import Statement, InvestStatementLine, StatementLine

import logging

LOGGER = logging.getLogger(__name__)

import csv


class FidelityPlugin(Plugin):
    """Sample plugin (for developers only)"""

    def get_parser(self, filename: str) -> "FidelityParser":
        parser = FidelityParser(filename)
        return parser


class FidelityCsvStatementParser(StatementParser[List[str]]):
    """Generic csv statement parser"""

    fin: TextIO  # file input stream

    # 0-based csv column mapping to StatementLine field
    mappings: Dict[str, int] = {}

    def __init__(self, fin: TextIO) -> None:
        super().__init__()
        self.fin = fin

    # def split_records(self) -> Iterable[List[str]]:
    #     return csv.reader(self.fin)

    def parse_record(self, line: List[str]) -> Optional[InvestStatementLine]:
        invest_stmt_line = InvestStatementLine()
        for field, col in self.mappings.items():
            if col >= len(line):
                raise ValueError(
                    "Cannot find column %s in line of %s items " % (col, len(line))
                )
            rawvalue = line[col]
            value = self.parse_value(rawvalue, field)
            setattr(invest_stmt_line, field, value)
        return invest_stmt_line


class FidelityCSVParser(FidelityCsvStatementParser):
    statement: Statement
    # id_generator: IdGenerator

    # date_format = "%m/%d/%Y"
    # mappings = {"date": 0, "memo": 1, "fees": 8, "amount": 10}
    mappings = {"memo": 1, "fees": 8, "amount": 10}

    # def __init__(self, filename: str) -> None:
    #     super().__init__()
    #     self.filename = filename
    #     self.statement = Statement()
    #     self.statement.broker_id = "Fidelity"
    #     self.statement.currency = "USD"
    #     self.id_generator = IdGenerator()

    def __init__(self, f):
        super().__init__(f)
        #     self.filename = filename
        # msg = f"__init__ : {filename}"
        # msg = f"__init__ :"
        # print(msg, file=sys.stderr)
        self.statement = Statement()
        self.statement.broker_id = "Fidelity"
        self.statement.currency = "USD"
        self.id_generator = IdGenerator()

    # def split_records(self) -> Iterable[str]:
    def split_records(self):
        """Return iterable object consisting of a line per transaction"""
        # msg = f"split_records"
        # print(msg, file=sys.stderr)
        reader = csv.reader(self.fin)
        return reader

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object"""

        # line[0 ] : Run Date
        # line[1 ] : Action
        # line[2 ] : Symbol
        # line[3 ] : Description
        # line[4 ] : Type
        # line[5 ] : Quantity
        # line[6 ] : Price ($)
        # line[7 ] : Commission ($)
        # line[8 ] : Fees ($)
        # line[9 ] : Accrued Interest ($)
        # line[10] : Amount ($)
        # line[11] : Cash Balance ($)
        # line[12] : Settlement Date

        # msg = f"parse_record"
        # print(msg, file=sys.stderr)

        # msg = f"self.cur_record: {self.cur_record}"
        # print(msg, file=sys.stderr)

        line_length = len(line)

        # there must be exactly 13 fields
        if line_length != 13:
            return None

        # skip blank lines
        if not line[0]:
            return None

        # skip the header
        if line[0] == "Run Date":
            return None

        # skip lines which are comments
        if line[0][:1] == '"':
            return None

        # skip any line that does not begin with a digit
        if not line[0][:1].isdigit():
            return None

        # # # print({list}, file=sys.stderr)
        for idx in range(13):
           msg = f"line[{idx}]: {line[idx]}"
           print(msg, file=sys.stderr)

        invest_stmt_line = super(FidelityCSVParser, self).parse_record(line)
        date = datetime.strptime(line[0][0:10], "%m/%d/%Y")
        invest_stmt_line.date = date
        id = self.id_generator.create_id(date)
        invest_stmt_line.id = id

        if line[12]:
            date_user = datetime.strptime(line[12][0:10], "%m/%d/%Y")
        else:
            date_user = date

        invest_stmt_line.date_user = date_user

        # if not line[8]:
        #    invest_stmt_line.fees = Decimal(line[8])

        match_result = re.match(r"^REINVESTMENT ", line[1])
        if match_result:
            invest_stmt_line.trntype = "BUYSTOCK"
            invest_stmt_line.trntype_detailed = "BUY"
            invest_stmt_line.security_id = line[2]
            invest_stmt_line.units = Decimal(line[5])
            invest_stmt_line.unit_price = Decimal(line[6])

        match_result = re.match(r"^DIVIDEND RECEIVED ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INCOME"
            invest_stmt_line.trntype_detailed = "DIV"
            invest_stmt_line.security_id = line[2]
            # invest_stmt_line.units = line[5]
            # invest_stmt_line.unit_price = line[6]

        match_result = re.match(r"^YOU BOUGHT ", line[1])
        if match_result:
            invest_stmt_line.trntype = "BUYSTOCK"
            invest_stmt_line.trntype_detailed = "BUY"
            invest_stmt_line.security_id = line[2]
            invest_stmt_line.units = Decimal(line[5])
            invest_stmt_line.unit_price = Decimal(line[6])

        match_result = re.match(r"^YOU SOLD ", line[1])
        if match_result:
            invest_stmt_line.trntype = "SELLSTOCK"
            invest_stmt_line.trntype_detailed = "SELL"
            invest_stmt_line.security_id = line[2]
            invest_stmt_line.units = Decimal(line[5])
            invest_stmt_line.unit_price = Decimal(line[6])

        print(f"{invest_stmt_line}")

        return invest_stmt_line


class FidelityParser(AbstractStatementParser):
    statement: Statement
    csvparser: FidelityCSVParser

    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename
        self.statement = Statement()
        self.statement.broker_id = "Fidelity"
        self.statement.currency = "USD"
        self.id_generator = IdGenerator()

    def parse(self) -> Statement:
        """Main entry point for parsers"""
        with open(self.filename, "r") as f:
            # a bit tricky here, Let's use the CSVStatementParser
            # first to conveniently read the Fidelity .csv file
            # then move things over to a statement in which
            # lines are invest_lines
            self.csvparser = FidelityCSVParser(f)
            csvstatement = self.csvparser.parse()

            # derive account id from file name
            match = re.search(
                r".*History_for_Account_(.*)\.csv", path.basename(self.filename)
            )
            if match:
                self.statement.account_id = match[1]


            # # translate and move records from lines to invest_lines 
            # # can we reverse these as we go
            # for line in self.statement.lines:
            #    invest_line = InvestStatementLine()
            #    invest_line.id     =   line.id
            #    invest_line.date   =   line.date
            #    invest_line.memo   =   line.memo
                  

            self.statement.invest_lines = csvstatement.lines



            # reverse the lines
            self.statement.invest_lines.reverse()


            # after reversing the lines in the list, update the id

            for line in self.statement.invest_lines:
                date = line.date
                new_id = self.id_generator.create_id(date)
                line.id = new_id

            # figure out start_date and end_date for the statement
            self.statement.start_date = min(sl.date for sl in self.statement.invest_lines if sl.date is not None)
            self.statement.end_date   = max(sl.date for sl in self.statement.invest_lines if sl.date is not None)

            print(f"self.statement.start_date : {self.statement.start_date}")
            print(f"self.statement.end_date : {self.statement.end_date}")

            print(f"{self.statement}")
            return self.statement


##########################################################################
class IdGenerator:
    """Generates a unique ID based on the date

    Hopefully any JSON file that we get will have all the transactions for a
    given date, and hopefully in the same order each time so that these IDs
    will match up across exports.
    """

    def __init__(self) -> None:
        self.date_count: Dict[datetime, int] = {}

    def create_id(self, date) -> str:
        self.date_count[date] = self.date_count.get(date, 0) + 1
        return f'{datetime.strftime(date, "%Y%m%d")}-{self.date_count[date]}'
