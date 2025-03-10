from fixed_width_lib.file import File
from typing import List, Optional, Union
from logging import Handler
from pathlib import Path
from decimal import Decimal
from utils import Transaction, Content


class Reader(File):

    def __init__(self, filepath: (str, Path), mode: str, logger_name: str, handlers_list: List[Handler], formatting: str):
        super().__init__(filepath, mode, logger_name, handlers_list, formatting)

    def read(self):
        """
        Read the entire file and return it
        :return: Content class containing the file values
        """
        if self.file is None:
            self.open()

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
            name=header_data["name"],
            surname=header_data["surname"],
            patronymic=header_data["patronymic"],
            address=header_data["address"],
            transactions=transactions,
            total_counter=footer_data["total_counter"],
            control_sum=footer_data["control_sum"]
        )

    def read_header(self):
        header_line = self.file.readline().rstrip("\n")
        if not header_line.startswith("01"):
            self.close()
            self.logger.log_message("Invalid header record", "ERROR")
            return None

        return {
            "name": header_line[2:30].strip(),
            "surname": header_line[30:60].strip(),
            "patronymic": header_line[60:90].strip(),
            "address": header_line[90:120].strip()
        }

    def read_transactions(self):
        """
        Read the all transactions and return them
        :return: List containing all transactions in a Transaction class
        """
        transactions = []
        for line in self.file:
            line = line.rstrip("\n")
            if line.startswith("03"):
                break
            if not line.startswith("02"):
                continue
            transaction_id = int(line[2:8])
            amount = Decimal(line[8:20])
            currency = line[20:23].strip()
            transactions.append(Transaction(transaction_id, amount, currency))
        return transactions

    def read_footer(self):
        """
        Read the entire footer line and return it
        :return: Dict containing the footer
        """
        footer_line = None
        for line in self.file:
            if line.startswith("03"):
                footer_line = line.rstrip("\n")
                break
        if footer_line is None:
            return None
        return {
            "total_counter": int(footer_line[2:8]),
            "control_sum": int(footer_line[8:20])
        }

    def get_transactions(self, *, counter: Union[int, List[int]] = None,
                         amount: Union[int, str, List[Union[int, str]]] = None,
                         currency: Union[str, List[str]] = None, limit=None) -> List[Optional[Transaction]]:
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
        if self.file is None:
            self.open()
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

        for line in self.file:
            line = line.rstrip("\n")
            if not line.startswith("02"):
                continue

            transaction_id = int(line[2:8])
            transaction_amount = Decimal(line[8:20])
            transaction_currency = line[20:23].strip()

            # If the match is None then it's not counted
            # otherwise if the value is in the match then the transaction is valid
            match_counter = counter is None or transaction_id in counter
            match_amount = amount is None or transaction_amount in amount
            match_currency = currency is None or transaction_currency in currency

            if match_counter and match_amount and match_currency:
                results.append(Transaction(transaction_id, transaction_amount, transaction_currency))
                found_counters.add(transaction_id)
                if limit and len(results) >= limit:
                    break
                if counter and set(counter) == found_counters:
                    break
            return results

