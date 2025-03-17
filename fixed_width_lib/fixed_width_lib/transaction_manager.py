from pathlib import Path
from decimal import Decimal, InvalidOperation
from typing import Optional, Union, List
from fixed_width_lib.reader import Reader
from fixed_width_lib.writer import Writer
from fixed_width_lib.file import File
from fixed_width_lib.logger import Logger
from fixed_width_lib.utils import Header, Transaction, Footer, Content
from fixed_width_lib.utils import HeaderFields, FooterFields, TransactionFields
from collections import defaultdict


class TransactionManager:
    def __init__(self, logger: Logger) -> None:
        """
        Initializes the TransactionManager with a logger.

        :param logger: Logger instance for logging events
        """
        self.logger = logger
        self.file_handler = None
        self.reader = None
        self.writer = None
        self.locked_fields = set()
        self.locked_transactions = defaultdict(set)

    def set_file(self, file_path: Path) -> None:
        """
        Sets the file for reading and writing transactions.

        :param file_path: Path to the fixed-width transaction file
        :return: None
        """
        if self.file_handler and self.file_handler.filepath == file_path:
            self.logger.log_message(
                f"File is already set to {file_path}", "INFO")
            return

        self.file_handler = File(
            str(file_path),
            self.logger,
            create_if_missing=True)
        self.file_handler.open()

        self.reader = Reader(self.file_handler, self.logger)
        self.writer = Writer(self.file_handler, self.logger)

        self.logger.log_message(f"File set to {file_path}", "INFO")

    def get_field(self, *field_names, **filters) -> str | dict:
        """
        Retrieves requested fields from the file.

        :param field_names: Fields to retrieve ('header', 'footer', 'transactions')
        :param filters: Optional filters for transactions (e.g., counter, amount, currency)
        :return: Dictionary of retrieved fields or error message
        """
        if not self.reader:
            return "Error: No file is set. Use set_file() first."

        results = {}

        if "header" in field_names:
            results["header"] = self.reader.read_header()

        if "footer" in field_names:
            results["footer"] = self.reader.read_footer()

        if "transactions" in field_names:
            transactions = self.reader.get_transactions(
                counter=filters.get("counter"),
                amount=filters.get("amount"),
                currency=filters.get("currency")
            )
            results["transactions"] = transactions

        return results if results else "Invalid field names"

    def modify_field(self,
                     field_name: str,
                     new_value: Union[str, List[Transaction]],
                     **filters) -> str:
        """
        Modifies a specific header field if it's not locked.

        :param field_name: Name of the field to modify (name, surname, patronymic, address, transactions)
        :param new_value: New value to assign to the field (str for all besides transaction which must be
        a list of Transaction class
        :return: Success message or error message
        """
        if not self.reader or not self.writer:
            return "Error: No file is set. Use set_file() first."

        if field_name in HeaderFields.FIELD_SIZES.keys():
            if field_name in self.locked_fields:
                self.logger.log_message(
                    f"Attempt to modify locked field: {field_name}", "WARNING")
                return f"Error: Field '{field_name}' is locked and cannot be modified."

            if not self.reader.read_header():
                return "Error: Header not found in file."

            header = Header()
            setattr(header, field_name, new_value)
            self.writer.change_header(header)

            self.logger.log_message(
                f"Modified header field {field_name} to {new_value}", "INFO")
            return f"Updated {field_name}: {new_value}"

        valid_transactions = []
        if field_name == "transactions":
            if not isinstance(new_value, List):
                self.logger.log_message(
                    f"Transactions have to be given in a list object", "ERROR")
                return f"Error: Transactions have to be given in a list object"
            for transaction in new_value:
                if not isinstance(transaction, Transaction):
                    self.logger.log_message(
                        f"Transactions have to be given as object of class Transaction", "ERROR")
                    return f"Error: Transactions have to be given as object of class Transaction"

                if transaction.transaction_id is None:
                    self.logger.log_message(
                        f"To change the transaction its counter has to be given,"
                        f" {transaction} skipped", "ERROR")
                    continue

                # Now check if any part of transaction is locked if it is skip that one
                if self._is_transaction_locked(transaction):
                    self.logger.log_message(
                        f"Attempt to modify locked transaction: {transaction}", "WARNING")
                    continue
                valid_transactions.append(transaction)

            if self.writer.change_transactions(valid_transactions):

                self.logger.log_message(
                    f"Modified transactions where {filters}: set {field_name} to {new_value}",
                    "INFO")
                return f"Updated {field_name} in matching transactions: {new_value}"
            else:
                self.logger.log_message(
                    f"Something went wrong, check the logs", "ERROR")
                return f"Something went wrong, check the logs"

        return "Invalid field name for modification"

    def add_header(self, header: Header) -> str:
        """
        Adds a header to an empty file. If the file already contains a header, it does nothing.

        :param header: Header object containing name, surname, patronymic, and address.
        :return: Success or error message
        """
        if not self.reader or not self.writer:
            return "Error: No file is set. Use set_file() first."

        if self.reader.read_header():
            self.logger.log_message(
                "File already contains a header. Skipping header addition.", "WARNING")
            return "Error: Header already exists in file."

        self.writer.set_header(header)
        self.logger.log_message(f"Added header: {header}", "INFO")
        return "Header added successfully."

    def add_transaction(self, transaction: Transaction) -> str:
        """
        Adds a new transaction to the file.

        :param transaction: Transaction object containing the amount and currency (both have to be present).
                            The transaction_id is automatically assigned and should be None.
        :return:  Success or error message
        """
        if not self.reader or not self.writer:
            return "Error: No file is set. Use set_file() first."
        try:
            amount = Decimal(transaction.amount)
            if abs(amount.as_tuple().exponent) > 2:
                self.logger.log_message(
                    f"Invalid transaction amount: {amount}", "ERROR")
                return "Error: Amount must have at most two decimal places"
        except (InvalidOperation, ValueError, TypeError):
            self.logger.log_message(
                f"Invalid transaction amount or format: {transaction.amount}", "ERROR")
            return "Error: Invalid amount format"
        if transaction.transaction_id is not None:
            self.logger.log_message(
                f"Transaction counter was given however "
                f"it is skipped as counter is added automatically", "ERROR")
        if transaction.currency is None or len(transaction.currency) != 3:
            self.logger.log_message(
                f"Currency has to be given and be of length 3", "ERROR")
            return "Error: Invalid amount format"

        result = self.writer.add_transaction(transaction)
        if result:
            self.logger.log_message(f"Added transaction: {transaction}", "INFO")
            return f"Added transaction: {transaction}"
        else:
            self.logger.log_message(f"Something went wrong, check the logs", "ERROR")
            return f"Something went wrong, check the logs"

    def lock_field(self, field_name: str, filter_value=None):
        """
        Locks a header field or transactions based on criteria.

        :param field_name: Field to lock ('name', 'surname', 'patronymic', 'address', 'amount', 'currency', 'counter')
        :param filter_value: Value to lock transactions by
                             (example: counter=10, amount=Decimal("100.00"), currency="USD")
        :return: Success message
        """
        if field_name in HeaderFields.FIELD_SIZES.keys():
            self.locked_fields.add(field_name)
            self.logger.log_message(
                f"Locked header field: {field_name}", "INFO")
            return f"Locked header field: {field_name}"

        if field_name in ["counter", "amount", "currency"]:
            self.locked_transactions[field_name].add(filter_value)

            self.logger.log_message(
                f"Locked transactions where {field_name} is "
                f"{'all' if filter_value is None else filter_value}", "INFO")
            return f"Locked transactions where {field_name}={filter_value}"

        return "Invalid field name for locking"

    def unlock_field(self, field_name: str, filter_value=None) -> str:
        """
        Unlocks a previously locked header field or transactions.

        :param field_name: Field to unlock ('name', 'surname', 'patronymic', 'address', 'amount', 'currency', 'counter')
        :param filter_value: Value to unlock transactions by
                             (example: counter=10, amount=Decimal("100.00"), currency="USD")
        :return: Success message
        """
        if field_name in HeaderFields.FIELD_SIZES.keys():
            if field_name in self.locked_fields:
                self.locked_fields.remove(field_name)
                self.logger.log_message(
                    f"Unlocked header field: {field_name}", "INFO")
                return f"Unlocked header field: {field_name}"
            else:
                return f"Error: Field '{field_name}' was not locked."

        if field_name in ["counter", "amount", "currency"]:
            if filter_value in self.locked_transactions[field_name]:
                self.locked_transactions[field_name].remove(filter_value)
                self.logger.log_message(
                    f"Unlocked transactions where {field_name}={filter_value}", "INFO")
                return f"Unlocked transactions where {field_name}={filter_value}"
            else:
                return f"Error: Transactions where {field_name}={filter_value} were not locked."

        return "Invalid field name for unlocking"

    def validate(self) -> str:
        """
        Validates the integrity of the file using the Reader's validation function.

        :return: Validation success message or error message
        """
        if not self.reader:
            return "Error: No file is set. Use set_file() first."

        validation_result = self.reader.validate_file()

        if validation_result != "File validation successful.":
            self.logger.log_message(validation_result, "ERROR")
        else:
            self.logger.log_message(validation_result, "INFO")

        return validation_result

    def _is_transaction_locked(self, transaction: Transaction) -> bool:
        """
        Checks if a transaction is locked.
        For any transaction if all counters are locked no modifications can happen
        otherwise we check if the transaction counter is locked

        For both currency and amount if they are not None we check the same this as counter

        :param transaction: Transaction to check
        :return: True if locked, False otherwise
        """

        if (None in self.locked_transactions["counter"] or
                transaction.transaction_id in self.locked_transactions["counter"]):
            return True

        if transaction.amount is not None:
            if (None in self.locked_transactions["amount"] or
                    transaction.amount in self.locked_transactions["amount"]):
                return True

        if transaction.currency is not None:
            if (None in self.locked_transactions["currency"] or
                    transaction.currency in self.locked_transactions["currency"]):
                return True

        return False
