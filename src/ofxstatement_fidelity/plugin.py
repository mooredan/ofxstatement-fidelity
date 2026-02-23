import csv
import re

from os import path

from datetime import datetime, date
from decimal import Decimal, Decimal as D
from typing import Any, Dict, Optional, TextIO

from ofxstatement.parser import AbstractStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import InvestStatementLine, Statement, StatementLine

# import logging
# LOGGER = logging.getLogger(__name__)


class FidelityPlugin(Plugin):
    """Sample plugin (for developers only)"""

    def get_parser(self, filename: str) -> "FidelityCSVParser":
        parser = FidelityCSVParser(filename)
        return parser


class FidelityCSVParser(AbstractStatementParser):
    statement: Statement
    fin: TextIO  # file input stream
    # 0-based csv column mapping to StatementLine field

    date_format: str = "%Y-%m-%d"
    cur_record: int = 0

    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename
        self.statement = Statement()
        self.statement.broker_id = "Fidelity"
        self.statement.currency = "USD"
        self.id_generator = IdGenerator()

    def parse_datetime(self, value: str) -> datetime:
        return datetime.strptime(value, self.date_format)

    def parse_decimal(self, value: str) -> D:
        # some plugins pass localised numbers, clean them up
        return D(value.replace(",", ".").replace(" ", ""))

    def parse_value(self, value: Optional[str], field: str) -> Any:
        tp = StatementLine.__annotations__.get(field)
        if value is None:
            return None

        if tp in (datetime, Optional[datetime]):
            return self.parse_datetime(value)
        elif tp in (Decimal, Optional[Decimal]):
            return self.parse_decimal(value)
        else:
            return value

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object"""

        invest_stmt_line = InvestStatementLine()

        # line[0 ] : Run Date
        # line[1 ] : Action
        # line[2 ] : Symbol
        # line[3 ] : Description
        # line[4 ] : Type
        # line[5 ] : Price ($)
        # line[6 ] : Quantity
        # line[7 ] : Commission ($)
        # line[8 ] : Fees ($)
        # line[9 ] : Accrued Interest ($)
        # line[10] : Amount ($)
        # line[11] : Cash Balance ($)
        # line[12] : Settlement Date

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

        # for idx in range(13):
        #     msg = f"line[{idx}]: {line[idx]}"
        #     print(msg, file=sys.stderr)

        invest_stmt_line.memo = line[1]

        # fees
        field = "fees"
        rawvalue = line[8]
        if rawvalue != "":
            value = self.parse_value(rawvalue, field)
            setattr(invest_stmt_line, field, value)
        # invest_stmt_line.fees = Decimal(line[8])

        # amount
        field = "amount"
        rawvalue = line[10]
        value = self.parse_value(rawvalue, field)
        setattr(invest_stmt_line, field, value)
        # invest_stmt_line.amount = Decimal(line[10])

        date = datetime.strptime(line[0][0:10], "%m/%d/%Y")
        invest_stmt_line.date = date
        id = self.id_generator.create_id(date)
        invest_stmt_line.id = id

        match_result = re.match(r"^REINVESTMENT ", line[1])
        if match_result:
            invest_stmt_line.trntype = "BUYSTOCK"
            invest_stmt_line.trntype_detailed = "BUY"
            invest_stmt_line.security_id = line[2]
            invest_stmt_line.unit_price = Decimal(line[5])
            invest_stmt_line.units = Decimal(line[6])
            return invest_stmt_line

        match_result = re.match(r"^DIVIDEND RECEIVED ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INCOME"
            invest_stmt_line.trntype_detailed = "DIV"
            invest_stmt_line.security_id = line[2]
            return invest_stmt_line

        match_result = re.match(r"^DIRECT DEBIT ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INVBANKTRAN"
            invest_stmt_line.trntype_detailed = "DEBIT"
            return invest_stmt_line

        match_result = re.match(r"^Electronic Funds Transfer Paid ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INVBANKTRAN"
            invest_stmt_line.trntype_detailed = "DEBIT"
            return invest_stmt_line

        match_result = re.match(r"^TRANSFERRED FROM ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INVBANKTRAN"
            invest_stmt_line.trntype_detailed = "CREDIT"
            return invest_stmt_line

        match_result = re.match(r"^TRANSFERRED TO ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INVBANKTRAN"
            invest_stmt_line.trntype_detailed = "DEBIT"
            return invest_stmt_line

        match_result = re.match(r"^DIRECT DEPOSIT ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INVBANKTRAN"
            invest_stmt_line.trntype_detailed = "CREDIT"
            return invest_stmt_line

        match_result = re.match(r"^INTEREST EARNED ", line[1])
        if match_result:
            invest_stmt_line.trntype = "INVBANKTRAN"
            invest_stmt_line.trntype_detailed = "CREDIT"
            return invest_stmt_line

        match_result = re.match(r"^ROLLOVER CASH", line[1])
        if match_result:
            invest_stmt_line.trntype = "INVBANKTRAN"
            invest_stmt_line.trntype_detailed = "CREDIT"
            return invest_stmt_line

        # Transfer of Assets: could be cash or securities
        toa_common_str = r"TRANSFER OF ASSETS ACAT "
        match_result = re.match(r"^" + toa_common_str, line[1])
        if match_result:
            remaining = line[1][len(toa_common_str) :]
            if remaining == "RECEIVE (Cash)" or remaining == "RES.CREDIT (Cash)":
                # Transfer of Assets: cash. Two forms: RECEIVE or RES.CREDIT
                invest_stmt_line.trntype = "INVBANKTRAN"
                invest_stmt_line.trntype_detailed = "XFER"
                invest_stmt_line.amount = Decimal(line[10])
                return invest_stmt_line
            else:
                # Transfer of Assets: security
                invest_stmt_line.trntype = "TRANSFER"
                invest_stmt_line.security_id = line[2]
                # Fidelity CSV stores the shares at line[6]
                invest_stmt_line.units = Decimal(line[6])
                # This is a pure stock transfer; make sure cash value is 0
                invest_stmt_line.amount = Decimal("0")
                return invest_stmt_line

        # USA T-Bill purchase (must come before security purchase due to security purchase's more general regex)
        if re.match(r"^YOU BOUGHT .*UNITED STATES TREAS BILLS", line[1]):
            invest_stmt_line.trntype = "BUYDEBT"
            invest_stmt_line.security_id = line[2]  # CUSIP
            units_in_dollars = Decimal(line[6])
            invest_stmt_line.units = units_in_dollars
            # Calculate unit price from amount and units, because line[5] is rounded leading to roundoff error.
            assert invest_stmt_line.amount is not None
            invest_stmt_line.unit_price = (
                abs(invest_stmt_line.amount) / units_in_dollars
            ) * 100  # e.g., 99.08 which means "99.08% of par"
            return invest_stmt_line

        # USA T-Bills redemption
        if re.match(r"^REDEMPTION PAYOUT .*UNITED STATES TREAS BILLS", line[1]):

            invest_stmt_line.trntype = "SELLDEBT"
            invest_stmt_line.security_id = line[2]  # CUSIP
            invest_stmt_line.unit_price = Decimal(
                "100"
            )  # T-Bills always sold at 100% of par
            invest_stmt_line.units = abs(Decimal(line[6]))

            return invest_stmt_line

        # Security purchase
        match_result = re.match(r"^YOU BOUGHT ", line[1])
        if match_result:
            invest_stmt_line.trntype = "BUYSTOCK"
            invest_stmt_line.trntype_detailed = "BUY"
            invest_stmt_line.security_id = line[2]
            invest_stmt_line.unit_price = Decimal(line[5])
            invest_stmt_line.units = Decimal(line[6])
            return invest_stmt_line

        # Security sale
        match_result = re.match(r"^YOU SOLD ", line[1])
        if match_result:
            invest_stmt_line.trntype = "SELLSTOCK"
            invest_stmt_line.trntype_detailed = "SELL"
            invest_stmt_line.security_id = line[2]
            invest_stmt_line.unit_price = Decimal(line[5])
            invest_stmt_line.units = Decimal(line[6])
            return invest_stmt_line

        # print(f"{invest_stmt_line}")
        assert False, f"Unhandled investment line: {invest_stmt_line}"

    # parse the CSV file and return a Statement
    def parse(self) -> Statement:
        """Main entry point for parsers"""
        with open(self.filename, "r") as fin:

            self.fin = fin

            reader = csv.reader(self.fin)

            # loop through the CSV file lines
            for csv_line in reader:

                self.cur_record += 1
                if not csv_line:
                    continue
                invest_stmt_line = self.parse_record(csv_line)
                if invest_stmt_line:
                    invest_stmt_line.assert_valid()
                    self.statement.invest_lines.append(invest_stmt_line)

            # derive account id from file name
            match = re.search(
                r".*History_for_Account_(.*)\.csv", path.basename(self.filename)
            )
            if match:
                self.statement.account_id = match[1]

            # reverse the lines
            self.statement.invest_lines.reverse()

            # after reversing the lines in the list, update the id
            for invest_line in self.statement.invest_lines:
                line_date = invest_line.date
                new_id = self.id_generator.create_id(line_date)
                invest_line.id = new_id

            # figure out start_date and end_date for the statement
            dates = []
            for sl in self.statement.invest_lines:
                if sl.date is None:
                    continue
                d = sl.date
                # convert date -> datetime at midnight so types are comparable
                if isinstance(d, date) and not isinstance(d, datetime):
                    d = datetime.combine(d, datetime.min.time())
                dates.append(d)

            if dates:
                self.statement.start_date = min(dates)
                self.statement.end_date = max(dates)

            # print(f"{self.statement}")
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
