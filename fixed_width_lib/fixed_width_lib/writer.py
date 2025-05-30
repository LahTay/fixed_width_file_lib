from decimal import Decimal
import os
from typing import List, Optional, Union

from fixed_width_lib.file import File
from fixed_width_lib.logger import Logger
from fixed_width_lib.utils import HeaderFields, FooterFields, TransactionFields, LINESIZE, MAX_TRANSACTIONS
from fixed_width_lib.utils import Header, Transaction


class Writer:
    def __init__(self, file_handler: File, logger: Logger):
        """
        Initializes the Writer instance.

        :param file_handler: File instance that manages file operations.
        :param logger: Logger instance for logging events.
        """
        self.file_handler = file_handler
        self.logger = logger

    def set_header(self, header: Header) -> None:
        """
        If file is empty then creates the header, otherwise replaces it.
        Requires the file to be properly structured.

        :param header: Header class - it has to be completely filled with no None values
        :return: None
        """
        if self.file_handler.mode != 'r+':
            self.logger.log_message(
                f"The file is open with {self.file_handler.mode} mode."
                f" To set the header properly it needs to be in 'r+' mode", "ERROR")
            return
        if header.name is None or header.surname is None or header.patronymic is None or header.address is None:
            self.logger.log_message(
                f"To set the header fully none of the header fields can be empty", "ERROR")
            return

        file = self.file_handler.get_file()
        file.seek(0)
        test_line = file.readline()
        file.seek(0)
        if test_line:
            linesep = file.newlines
            print(test_line)
        else:
            linesep = os.linesep
            print(2)
        if linesep is None:
            self.logger.log_message(
                f"The header line has no endline character. Reset file or fix that by hand",
                "ERROR")
            return
        text_to_insert = (
            f"01"
            f"{header.name:>{HeaderFields.FIELD_SIZES['name']}}"
            f"{header.surname:>{HeaderFields.FIELD_SIZES['surname']}}"
            f"{header.patronymic:>{HeaderFields.FIELD_SIZES['patronymic']}}"
            f"{header.address:>{HeaderFields.FIELD_SIZES['address']}}"
            f"{linesep}"
        )
        if len(text_to_insert) != LINESIZE + len(linesep):
            self.logger.log_message(
                f"The header contents are too long, check them and try again."
                f"Values can be at most: name:{HeaderFields.FIELD_SIZES['name']},"
                f" surname:{HeaderFields.FIELD_SIZES['surname']},"
                f" patronymic:{HeaderFields.FIELD_SIZES['patronymic']},"
                f" address:{HeaderFields.FIELD_SIZES['address']} characters", "ERROR")
            return
        file.write(text_to_insert)
        file.flush()

    def change_header(self, header: Header) -> None:
        """
        Change given values from the header. It requires the header to be already present in the file.

        :param header: Header class - it can be partially filled with None values
        :return: None
        """
        if self.file_handler.mode != 'r+':
            self.logger.log_message(
                f"The file is open with {self.file_handler.mode} mode."
                f" To set the header properly it needs to be in 'r+' mode", "ERROR")
            return
        file = self.file_handler.get_file()
        updates = {
            "name": header.name,
            "surname": header.surname,
            "patronymic": header.patronymic,
            "address": header.address
        }

        for field, new_value in updates.items():
            if new_value is not None:
                start, end = getattr(HeaderFields, field.upper())
                max_length = HeaderFields.FIELD_SIZES[field]

                if len(new_value) > max_length:
                    self.logger.log_message(
                        f"{field} exceeds max length of {max_length} characters.", "ERROR")
                    return

                formatted_value = new_value.rjust(max_length)
                file.seek(start)
                file.write(formatted_value)
                file.flush()

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Adds a new transaction to the bottom of the file, moving the footer and updating it.

        :param transaction: Transaction class - has to be filled, only counter can be None (it doesn't matter here)
        :return: None
        """

        if self.file_handler.mode != 'r+':
            self.logger.log_message(
                f"The file is open with {self.file_handler.mode} mode."
                f" To add a new transaction properly it needs to be in 'r+' mode", "ERROR")
            return False

        if transaction.amount is None or transaction.currency is None:
            self.logger.log_message(
                f"Amount: {transaction.amount} and currency {transaction.currency} cannot be None",
                "ERROR")
            return False
        if not isinstance(transaction.amount, Decimal):
            self.logger.log_message(
                f"Amount: {transaction.amount} has to be of Decimal class",
                "ERROR")
            return False

        file = self.file_handler.get_file()
        file.seek(0)

        # First find out which OS the file endings are formatted in
        first_line = file.readline()
        os_end = file.newlines
        line_size = LINESIZE + len(os_end)

        file.seek(0, os.SEEK_END)
        file_size = file.tell()

        if file_size <= line_size:  # Only header exists
            self.logger.log_message(
                "No transactions found, appending first transaction after the header.", "INFO")
            file.seek(0, os.SEEK_END)
            counter = 0
            footer = (  # Empty footer
                f"03"
                f"{0:0{FooterFields.FIELD_SIZES['total_counter']}d}"
                f"{0:0{FooterFields.FIELD_SIZES['control_sum']}d}"
                f"{' ' * FooterFields.FIELD_SIZES['reserved']}"
            )
        else:
            file.seek(0, os.SEEK_END)
            # Puts the file to the beginning of the last transaction
            file.seek(file.tell() - 2 * line_size)
            # Move to the part where the counter is
            file.read(FooterFields.TOTAL_COUNTER[0])
            try:
                counter = int(file.read(FooterFields.FIELD_SIZES["total_counter"]))
            except (ValueError, TypeError):
                self.logger.log_message(
                    f"Last transactions counter couldn't be properly read! The file is corrupted!"
                    f" Aborting addition!", "ERROR")
                return False

            if counter >= MAX_TRANSACTIONS:
                self.logger.log_message(
                    f"The max amount of transactions inside this file has been reached. Create a new file",
                    "WARNING")
                return False

            file.seek(0, os.SEEK_END)
            # Puts the file to the beginning of the footer
            file.seek(file.tell() - line_size)

            footer = file.readline()
            file.seek(0, os.SEEK_END)
            file.seek(file.tell() - line_size)

        transaction_amount = str(transaction.amount * 100)
        if len(transaction_amount) > TransactionFields.FIELD_SIZES["amount"]:
            self.logger.log_message(
                f"Maximum supported transaction amount is "
                f"{int('9' * TransactionFields.FIELD_SIZES['amount']) / 100} while {transaction.amount} was given",
                "ERROR")
            return False
        new_transaction = (
            f"02"
            f"{counter + 1:0{TransactionFields.FIELD_SIZES['counter']}d}"
            f"{int(transaction.amount * 100):0{TransactionFields.FIELD_SIZES['amount']}d}"
            f"{transaction.currency:>{TransactionFields.FIELD_SIZES['currency']}}"
            f"{' ' * TransactionFields.FIELD_SIZES['reserved']}")

        if len(new_transaction) != LINESIZE:
            self.logger.log_message(
                f"The transaction contents are too long, check them and try again."
                f"Values can be at most: amount:{TransactionFields.FIELD_SIZES['amount']},"
                f" currency:{TransactionFields.FIELD_SIZES['currency']} characters", "ERROR")
            return False
        footer = self._update_footer(footer, 1, transaction.amount)
        if len(footer) != LINESIZE:
            self.logger.log_message(
                f"Adding the transaction with amount: {transaction_amount} would overflow the footer as"
                f" the total amount is bigger than the control sum space!. Transaction was not added!"
                f"Create a new file!", "ERROR")
            return False

        file.write(new_transaction)
        file.write(os_end)

        file.write(footer)
        file.write(os_end)

        file.flush()
        return True

    def change_transactions(self, transactions: List[Transaction]) -> bool:
        """
        Changes transactions based on their counters. The counters have to be set, but the other values can be Nones

        :param transactions: List of Transaction instances where transaction_id must be set.
        :return: True if successful, False otherwise.
        """

        if self.file_handler.mode != 'r+':
            self.logger.log_message(
                f"The file is open with {self.file_handler.mode} mode. "
                f"To change a transaction properly, it needs to be in 'r+' mode.", "ERROR")
            return False

        if not transactions:
            self.logger.log_message(
                f"No transactions were given, so no changes happen", "INFO")
            return False

        file = self.file_handler.get_file()
        file.seek(0)

        first_line = file.readline()
        if not first_line:
            self.logger.log_message(
                f"The file is empty. Set a header first", "ERROR")
            return False

        os_end = file.newlines
        line_size = LINESIZE + len(os_end)


        amount_changes = []
        for transaction in transactions:
            if transaction.transaction_id is None:
                self.logger.log_message(
                    f"Transaction: {transaction} doesn't have a valid counter present. It was skipped",
                    "WARNING")
                continue
            transaction_pos = transaction.transaction_id * line_size
            file.seek(transaction_pos + TransactionFields.COUNTER[0])
            
            try:
                read_counter = int(file.read(TransactionFields.FIELD_SIZES["counter"]))
            except (ValueError, TypeError):
                self.logger.log_message(
                    f"Couldn't find proper counter of given transaction: {transaction}."
                    f" It doesn't exist or the file is corrupted.",
                    "ERROR")
                return False

            if read_counter != transaction.transaction_id:
                self.logger.log_message(
                    f"Transaction with counter {transaction.transaction_id} not found in expected location.",
                    "ERROR")
                return False

            if transaction.amount is not None:
                if not isinstance(transaction.amount, Decimal):
                    self.logger.log_message(
                        f"Amount: {transaction.amount} has to be of Decimal class", "ERROR")
                    continue

                transaction_amount = str(transaction.amount * 100)
                if len(transaction_amount) > TransactionFields.FIELD_SIZES["amount"]:
                    self.logger.log_message(
                        f"Maximum supported transaction amount is "
                        f"{int('9' * TransactionFields.FIELD_SIZES['amount']) / 100} while {transaction.amount} was given",
                        "ERROR")
                    return False

                formatted_amount = f"{int(transaction.amount * 100):0{TransactionFields.FIELD_SIZES['amount']}d}"
                file.seek(transaction_pos + TransactionFields.AMOUNT[0])
                current_amount = Decimal(
                    file.read(
                        TransactionFields.FIELD_SIZES["amount"]).strip()) / 100
                file.seek(transaction_pos + TransactionFields.AMOUNT[0])
                file.write(formatted_amount)
                amount_changes.append(transaction.amount - current_amount)

            if transaction.currency is not None:
                formatted_currency = transaction.currency.rjust(
                    TransactionFields.FIELD_SIZES["currency"])
                file.seek(transaction_pos + TransactionFields.CURRENCY[0])
                file.write(formatted_currency)

        file.seek(0, os.SEEK_END)
        file.seek(file.tell() - line_size)
        footer = file.readline()
        file.seek(0, os.SEEK_END)
        file.seek(file.tell() - line_size)
        footer = self._update_footer(footer, 0, sum(amount_changes))
        file.write(footer)
        file.flush()
        return True

    def _update_footer(
            self,
            footer_line,
            added_transaction_num,
            added_transaction_amount) -> str:
        """
        Updates the footer with new transaction count and control sum.

        :param footer_line: The existing footer line from the file.
        :param added_transaction_num: Number of transactions added or modified.
        :param added_transaction_amount: The sum of transaction amount changes.
        :return: Updated footer string.
        """
        total_counter = int(
            footer_line[FooterFields.TOTAL_COUNTER[0]:FooterFields.TOTAL_COUNTER[1]])
        control_sum = Decimal(
            footer_line[FooterFields.CONTROL_SUM[0]:FooterFields.CONTROL_SUM[1]]) / 100

        total_counter += added_transaction_num
        control_sum += added_transaction_amount

        updated_footer = (
            f"03"
            f"{total_counter:0{FooterFields.FIELD_SIZES['total_counter']}d}"
            f"{int(control_sum * 100):0{FooterFields.FIELD_SIZES['control_sum']}d}"
            f"{' ' * FooterFields.FIELD_SIZES['reserved']}")

        return updated_footer
