from decimal import Decimal
import os
from typing import List, Optional, Union

from fixed_width_lib.file import File
from fixed_width_lib.logger import Logger
from fixed_width_lib.utils import HeaderFields, FooterFields, TransactionFields, LINESIZE, MAX_TRANSACTIONS
from fixed_width_lib.utils import Header, Transaction


class Writer:
    def __init__(self, file_handler: File, logger: Logger):
        self.file_handler = file_handler
        self.logger = logger

    def set_header(self, header: Header) -> None:
        """
        This is a function that will set the header anew
        :param name:
        :param surname:
        :param patronymic:
        :param address:
        :return:
        """
        if self.file_handler.mode != 'r+':
            self.logger.log_message(f"The file is open with {self.file_handler.mode} mode."
                                    f" To set the header properly it needs to be in 'r+' mode", "ERROR")
            return
        if header.name is None or header.surname is None or header.patronymic is None or header.address is None:
            self.logger.log_message(f"To set the header fully none of the header fields can be empty",
                                    "ERROR")
            return

        file = self.file_handler.get_file()
        file.seek(0)
        text_to_insert = (
            f"01"
            f"{header.name:>{HeaderFields.FIELD_SIZES['name']}}"
            f"{header.surname:>{HeaderFields.FIELD_SIZES['surname']}}"
            f"{header.patronymic:>{HeaderFields.FIELD_SIZES['patronymic']}}"
            f"{header.address:>{HeaderFields.FIELD_SIZES['address']}}"
        )
        if len(text_to_insert) != LINESIZE:
            self.logger.log_message(f"The header contents are too long, check them and try again."
                                    f"Values can be at most: name:{HeaderFields.FIELD_SIZES['name']},"
                                    f" surname:{HeaderFields.FIELD_SIZES['surname']},"
                                    f" patronymic:{HeaderFields.FIELD_SIZES['patronymic']},"
                                    f" address:{HeaderFields.FIELD_SIZES['address']} characters",
                                    "ERROR")
            return
        file.write(text_to_insert)
        file.seek(0)

    def change_header(self, header: Header) -> None:
        """
        This is a function that changes header, only the required parts
        :param name:
        :param surname:
        :param patronymic:
        :param address:
        :return:
        """
        if self.file_handler.mode != 'r+':
            self.logger.log_message(f"The file is open with {self.file_handler.mode} mode."
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
                    self.logger.log_message(f"{field} exceeds max length of {max_length} characters.",
                                            "ERROR")
                    return

                formatted_value = new_value.rjust(max_length)
                file.seek(start)
                file.write(formatted_value)


    def add_transaction(self, transaction: Transaction) -> None:
        """
        This function adds a new transaction
        :param amount:
        :param currency:
        :return:
        """

        if self.file_handler.mode != 'r+':
            self.logger.log_message(f"The file is open with {self.file_handler.mode} mode."
                                    f" To add a new transaction properly it needs to be in 'r+' mode", "ERROR")
            return
        file = self.file_handler.get_file()

        # First find out which OS the file endings are formatted in
        first_line = file.readline()
        os_end = "\r\n" if first_line.endswith("\r\n") else "\n"
        line_size = LINESIZE + len(os_end)

        file.seek(-2*line_size, os.SEEK_END)  # Puts the file to the beginning of the last transaction
        file.seek(FooterFields.TOTAL_COUNTER[0], os.SEEK_CUR)  # Move to the part where the counter is
        counter = int(file.read(FooterFields.FIELD_SIZES["total_counter"]))

        if counter >= MAX_TRANSACTIONS:
            self.logger.log_message(
                f"The max amount of transactions inside this file has been reached. Create a new file",
                "WARNING")
            return


        file.seek(-line_size, os.SEEK_END)  # Puts the file to the beginning of the footer

        footer = file.readline()
        new_transaction = (
            f"02"
            f"{counter + 1:0{TransactionFields.FIELD_SIZES['counter']}d}"
            f"{int(transaction.amount * 100):0{TransactionFields.FIELD_SIZES['amount']}d}"
            f"{transaction.currency:>{TransactionFields.FIELD_SIZES['currency']}}"
            f"{' ' * TransactionFields.FIELD_SIZES['reserved']}"
        )
        if len(new_transaction) != LINESIZE:
            self.logger.log_message(f"The transaction contents are too long, check them and try again."
                                    f"Values can be at most: amount:{TransactionFields.FIELD_SIZES['amount']},"
                                    f" currency:{TransactionFields.FIELD_SIZES['currency']} characters",
                                    "ERROR")
            return
        file.write(new_transaction)
        file.write(os_end)
        footer = self._update_footer(footer, 1, transaction.amount)
        file.write(footer)
        file.write(os_end)

        file.seek(0)

    def change_transactions(self, transactions: List[Transaction]) -> None:
        """
        Modify the amount and/or currency of an existing transaction based on its counter (idx).

        :param idx: Transaction index (counter) or a list of indices.
        :param amount: New amount(s) (must match the idx count if list).
        :param currency: New currency/currencies (must match the idx count if list).
        :return: None
        """
        if self.file_handler.mode != 'r+':
            self.logger.log_message(
                f"The file is open with {self.file_handler.mode} mode. "
                f"To change a transaction properly, it needs to be in 'r+' mode.",
                "ERROR"
            )
            return

        file = self.file_handler.get_file()
        file.seek(0)

        # Detect OS-specific newline format
        first_line = file.readline()
        os_end = "\r\n" if first_line.endswith("\r\n") else "\n"
        line_size = LINESIZE + len(os_end)


        amount_changes = []
        # Process each index separately
        for transaction in transactions:
            # Seek to the transaction position
            transaction_pos = (transaction.transaction_id - 1) * line_size  # -1 since counter starts at 1
            file.seek(transaction_pos + TransactionFields.COUNTER[0])

            # Read counter value
            read_counter = int(file.read(TransactionFields.FIELD_SIZES["counter"]))

            if read_counter != transaction.transaction_id:
                self.logger.log_message(
                    f"Transaction with counter {transaction.transaction_id} not found in expected location.",
                    "ERROR"
                )
                return

            # Overwrite only the required fields
            if transaction.amount is not None:
                formatted_amount = f"{int(transaction.amount * 100):0{TransactionFields.FIELD_SIZES['amount']}d}"
                file.seek(transaction_pos + TransactionFields.AMOUNT[0])
                current_amount = Decimal(file.read(TransactionFields.FIELD_SIZES["amount"]).strip()) / 100
                file.seek(-TransactionFields.FIELD_SIZES["amount"], os.SEEK_CUR)
                file.write(formatted_amount)
                amount_changes.append(transaction.amount - current_amount)

            if transaction.currency is not None:
                formatted_currency = transaction.currency.rjust(TransactionFields.FIELD_SIZES["currency"])
                file.seek(transaction_pos + TransactionFields.CURRENCY[0])
                file.write(formatted_currency)

        file.seek(-line_size, os.SEEK_END)
        footer = file.readline()
        footer = self._update_footer(footer, 0, sum(amount_changes))
        file.write(footer)

    def _update_footer(self, footer_line, added_transaction_num, added_transaction_amount) -> str:
        total_counter = int(footer_line[FooterFields.TOTAL_COUNTER[0]:FooterFields.TOTAL_COUNTER[1]])
        control_sum = Decimal(footer_line[FooterFields.CONTROL_SUM[0]:FooterFields.CONTROL_SUM[1]]) / 100

        total_counter += added_transaction_num
        control_sum += added_transaction_amount

        # Format updated footer
        updated_footer = (
            f"03"
            f"{total_counter:0{FooterFields.FIELD_SIZES['total_counter']}d}"
            f"{int(control_sum * 100):0{FooterFields.FIELD_SIZES['control_sum']}d}"
            f"{' ' * FooterFields.FIELD_SIZES['reserved']}"
        )

        return updated_footer
