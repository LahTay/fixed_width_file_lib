from decimal import Decimal
import os
import re
from typing import List, Optional, Union

from fixed_width_lib.file import File
from fixed_width_lib.logger import Logger
from fixed_width_lib.utils import Header, Footer, Transaction, Content
from fixed_width_lib.utils import HeaderFields, FooterFields, TransactionFields, LINESIZE


class Reader:
    def __init__(self, file_handler: File, logger: Logger):
        self.file_handler = file_handler
        self.logger = logger

    def read(self) -> Optional[Content]:
        """
        Read the entire _file and return it
        :return: Content class containing the _file values
        """
        header_data = self.read_header()
        if header_data is None:
            self.logger.log_message("Header record not found", "ERROR")
            return

        transactions = self.read_transactions()
        footer_data = self.read_footer()

        if footer_data is None:
            self.logger.log_message("Footer record not found", "ERROR")
            return

        return Content(
            header=header_data,
            transactions=transactions,
            footer=footer_data)

    def read_header(self) -> Optional[Header]:
        file = self.file_handler.get_file()
        file.seek(0)
        header_line = file.readline()
        if not header_line.startswith("01"):
            self.logger.log_message("Invalid header record", "ERROR")
            return None

        return Header(
            name=header_line[HeaderFields.NAME[0]:HeaderFields.NAME[1]].strip(),
            surname=header_line[HeaderFields.SURNAME[0]:HeaderFields.SURNAME[1]].strip(),
            patronymic=header_line[HeaderFields.PATRONYMIC[0]:HeaderFields.PATRONYMIC[1]].strip(),
            address=header_line[HeaderFields.ADDRESS[0]:HeaderFields.ADDRESS[1]].strip(),
        )

    def read_transactions(self) -> List[Transaction]:
        """
        Read the all transactions and return them
        :return: List containing all transactions in a Transaction class
        """
        file = self.file_handler.get_file()
        file.seek(0)
        transactions = []
        for line in file:
            if line.startswith("03"):
                break
            if not line.startswith("02"):
                continue
            transaction_id = int(
                line[TransactionFields.COUNTER[0]:TransactionFields.COUNTER[1]])
            amount = Decimal(
                line[TransactionFields.AMOUNT[0]:TransactionFields.AMOUNT[1]]) / 100
            currency = line[TransactionFields.CURRENCY[0]                            :TransactionFields.CURRENCY[1]].strip()
            transactions.append(Transaction(transaction_id, amount, currency))
        return transactions

    def read_footer(self) -> Optional[Footer]:
        """
        Read the entire footer line and return it
        :return: Dict containing the footer
        """
        file = self.file_handler.get_file()
        file.seek(0)
        first_line = file.readline()
        if not first_line:
            self.logger.log_message("File is empty", "ERROR")
            return
        os_end = file.newlines
        line_size = LINESIZE + len(os_end)

        file.seek(0, os.SEEK_END)
        file.seek(file.tell() - line_size)

        footer_line = file.readline()

        if not footer_line.startswith("03"):
            self.logger.log_message("Footer record not found", "ERROR")
            return

        return Footer(
            total_counter=int(footer_line[FooterFields.TOTAL_COUNTER[0]:FooterFields.TOTAL_COUNTER[1]]),
            control_sum=Decimal(footer_line[FooterFields.CONTROL_SUM[0]:FooterFields.CONTROL_SUM[1]]) / 100
        )

    def get_transactions(self,
                         *,
                         counter: Union[int,
                                        List[int]] = None,
                         amount: Union[int,
                                       str,
                                       List[Union[int,
                                            str]]] = None,
                         currency: Union[str,
                                         List[str]] = None,
                         limit=None) -> List[Optional[Transaction]]:
        """
        Returns a list of Transaction objects that match the provided filters and limits the number of results.

        A transaction is included if, for each filter provided, its field value is equal to one of the allowed values.
        For example, get_transactions(amount=[1000, 2000], currency="EUR", limit=5) will return up to five transactions
        with currency "EUR" and an amount equal to either Decimal(1000) or Decimal(2000).

        :param counter: A single value or list of values representing the transaction counter.
        :param amount:  A single value or list of values representing the transaction amount.
                        Only int or str values are allowed and will be converted to Decimal.
        :param currency: A single value or list of values representing the transaction currency.
        :param limit: An optional integer specifying the maximum number of transactions to return.
        :return:
        """
        file = self.file_handler.get_file()
        file.seek(0)
        results = []
        found_counters = set()

        if isinstance(counter, int):
            counter = [counter]
        if isinstance(amount, (int, str)):
            amount = [Decimal(amount)]
        elif isinstance(amount, list):
            amount = [Decimal(a) for a in amount]
        if isinstance(currency, str):
            currency = [currency]

        for line in file:
            if not line.startswith("02"):
                continue

            transaction_id = int(
                line[TransactionFields.COUNTER[0]:TransactionFields.COUNTER[1]])
            transaction_amount = Decimal(
                line[TransactionFields.AMOUNT[0]:TransactionFields.AMOUNT[1]]) / 100
            transaction_currency = line[TransactionFields.CURRENCY[0]                                        :TransactionFields.CURRENCY[1]].strip()

            match_counter = counter is None or transaction_id in counter
            match_amount = amount is None or transaction_amount in amount
            match_currency = currency is None or transaction_currency in currency

            if match_counter and match_amount and match_currency:
                results.append(
                    Transaction(
                        transaction_id,
                        transaction_amount,
                        transaction_currency))
                found_counters.add(transaction_id)
                if limit and len(results) >= limit:
                    break
                if counter and set(counter) == found_counters:
                    break
        return results

    def validate_file(self):
        """
        Validates the integrity of the file's header, footer, and transactions.

        :return: Validation success message or error message
        """
        file = self.file_handler.get_file()
        file.seek(0)

        total_transactions = 0
        control_sum = Decimal("0.00")

        header = file.readline()
        if not header:
            self.logger.log_message("File is empty", "ERROR")
            return "Error: File is empty."
        endline = file.newlines
        if endline is None:
            self.logger.log_message(
                "No valid endline character exists", "ERROR")
            return "No valid endline character exists"
        header = header.rstrip(endline)
        if not header.startswith("01") or len(header) != 120:
            self.logger.log_message(
                "No valid endline character exists", "ERROR")
            return "No valid endline character exists"

        for line in file:

            if not line.endswith(endline):
                self.logger.log_message(
                    "No valid endline character exists", "ERROR")
                return "No valid endline character exists"
            line = line.rstrip(endline)

            if line.startswith("03"):
                break
            total_transactions += 1
            if not line.startswith("02"):
                self.logger.log_message(
                    f"Incorrect start id of transaction no. {total_transactions}", "ERROR")
                return f"Incorrect start id of transaction no. {total_transactions}"

            if len(line) != 120:
                self.logger.log_message(
                    f"Incorrect length: {len(line)} of transaction no. {total_transactions}",
                    "ERROR")
                return f"Incorrect length: {len(line)} of transaction no. {total_transactions}"

            # Validate counter + amount [2:20] are numbers
            if not re.match(r"^\d{18}$", line[2:20]):
                return f"Error: Transaction no. {total_transactions} contains invalid numeric fields."

            # Validate reserved space [23:120] is spaces only
            if not re.match(r"^ *$", line[23:120]):
                return f"Error: Transaction no. {total_transactions} contains non-space characters in reserved section."

                # Update validation sums
            control_sum += Decimal(line[8:20]) / 100
        footer = line
        if not footer.startswith("03"):
            self.logger.log_message("Incorrect start id of footer", "ERROR")
            return "Incorrect start id of footer"

        if len(footer) != 120:
            self.logger.log_message(
                f"Incorrect length: {len(footer)} of footer", "ERROR")
            return f"Incorrect length: {len(footer)} of footer"

        if not re.match(r"^\d{18}$", line[2:20]):
            self.logger.log_message(
                f"Error: Footer {footer} contains invalid numeric fields.", "ERROR")
            return f"Error: Footer {footer} contains invalid numeric fields."

        footer_total_counter = int(footer[2:8])
        if footer_total_counter != total_transactions:
            self.logger.log_message(
                f"Error: Footer total_counter {footer_total_counter}"
                f" does not match transaction count {total_transactions}.", "ERROR")
            return (f"Error: Footer total_counter {footer_total_counter} "
                    f"does not match transaction count {total_transactions}.")

        footer_control_sum = Decimal(footer[8:20]) / 100
        if footer_control_sum != control_sum:
            self.logger.log_message(
                f"Error: Footer control_sum {footer_control_sum} "
                f"does not match transaction total {control_sum}.", "ERROR")
            return f"Error: Footer control_sum {footer_control_sum} does not match transaction total {control_sum}."

        if not re.match(r"^ *$", footer[20:120]):
            return f"Error: Footer: '{footer}' reserved section contains non-space characters."
        return "File validation successful."
