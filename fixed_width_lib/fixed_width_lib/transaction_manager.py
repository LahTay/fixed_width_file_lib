from pathlib import Path
from fixed_width_lib.reader import Reader
from fixed_width_lib.writer import Writer
from fixed_width_lib.utils import Transaction
from fixed_width_lib.logger import Logger
from decimal import Decimal


class TransactionManager:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.file_path = None
        self.reader = None
        self.writer = None
        self.locked_fields = set()

    def set_file(self, file_path: Path, mode: str):
        if self.file_path == file_path and self.reader and self.writer:
            self.logger.log_message(f"File is already set to {file_path}", "INFO")
            return

        self.file_path = file_path
        if self.reader:
            self.reader.set_file(file_path, mode)
        else:
            self.reader = Reader(file_path, mode, self.logger)

        if self.writer:
            self.writer.set_file(file_path, mode)
        else:
            self.writer = Writer(file_path, mode, self.logger)

        self.logger.log_message(f"File set to {file_path}", "INFO")

    def get_field(self, *field_names, **filters):
        if not self.reader:
            return "Error: No file is set. Use set_file() first."

        results = {}

        if "header" in field_names:
            results["header"] = self.reader.read_header()

        if "footer" in field_names:
            results["footer"] = self.reader.read_footer()

        if "transactions" in field_names:
            counter = filters.get("counter")
            amount = filters.get("amount")
            currency = filters.get("currency")
            transactions = self.reader.get_transactions(counter=counter, amount=amount, currency=currency)
            results["transactions"] = transactions

        return results if results else "Invalid field names"

    def modify_field(self, field_name: str, new_value: str):
        if not self.reader or not self.writer:
            return "Error: No file is set. Use set_file() first."

        if field_name in self.locked_fields:
            self.logger.log_message(f"Attempt to modify locked field: {field_name}", "WARNING")
            return f"Error: Field '{field_name}' is locked and cannot be modified."

        if field_name in ["name", "surname", "patronymic", "address"]:
            header = self.reader.read_header()
            header[field_name] = new_value
            self.writer.write_header(header)
            self.logger.log_message(f"Modified field {field_name} to {new_value}", "INFO")
            return f"Updated {field_name}: {new_value}"
        else:
            return "Invalid field name for modification"

    def add_transaction(self, transaction_id: int, amount: str, currency: str):
        if not self.reader or not self.writer:
            return "Error: No file is set. Use set_file() first."

        new_transaction = Transaction(
            transaction_id=transaction_id,
            amount=Decimal(amount),
            currency=currency
        )

        self.writer.write_transactions(new_transaction)
        self.logger.log_message(f"Added transaction: {new_transaction}", "INFO")
        return f"Added transaction: {new_transaction}"

    def lock_field(self, field_name: str):
        self.locked_fields.add(field_name)
        self.logger.log_message(f"Locked field: {field_name}", "INFO")
        return f"Locked field: {field_name}"

    def validate(self):
        if not self.reader:
            return "Error: No file is set. Use set_file() first."

        header = self.reader.read_header()
        footer = self.reader.read_footer()
        transactions = self.reader.read_transactions()

        if not header or not footer:
            self.logger.log_message("Validation failed: Header or Footer is missing.", "ERROR")
            return "Error: Header or Footer is missing."
        if len(transactions) != footer["total_counter"]:
            self.logger.log_message("Validation failed: Transaction count does not match footer total_counter.", "ERROR")
            return "Error: Transaction count does not match footer total_counter."
        self.logger.log_message("File validation successful.", "INFO")
        return "File validation successful."
