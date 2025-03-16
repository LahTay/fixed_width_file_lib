from pathlib import Path
from decimal import Decimal, InvalidOperation
from fixed_width_lib.logger import Logger, LogHandler
from fixed_width_lib.transaction_manager import TransactionManager
from fixed_width_lib.utils import Transaction, Header
import shlex
import sys
from pprint import pprint


class CLI:
    def __init__(self, file_path):
        """
        Initializes the CLI, setting up logging and the TransactionManager.
        """
        self.logger = Logger("cli_logger",
                             [LogHandler.FILE.value("./logs/cli.log")],
                             "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.logger.set_level("INFO")
        self.logger.set_global_level("CRITICAL")
        self.manager = TransactionManager(self.logger)
        self.file_set = False

        if file_path:
            self.set_file(file_path)

    def set_file(self, file_path: str):
        """
        Sets the transaction file in the manager.

        :param file_path: Path to the fixed-width transaction file.
        """
        self.manager.set_file(Path(file_path))
        self.file_set = True
        print(f"File set to: {file_path}")

    def parse_filters(self, filters: list[str]) -> dict:
        """
        Parses CLI input filters into a structured dictionary.

        :param filters: List of filter arguments in the form of key=value.
        :return: Dictionary containing parsed filters.
        """
        parsed_filters = {}
        for filter_str in filters:
            if '=' in filter_str:
                key, value = filter_str.split('=', 1)
                key = key.strip().lower()
                value = value.strip().strip('"')

                if key in ("amount", "counter"):
                    values = value.split(',')
                    parsed_filters[key] = [
                        Decimal(v) if '.' in v else int(v) for v in values]
                elif key == "currency":
                    parsed_filters[key] = value.split(',')

        return parsed_filters

    def run(self):
        """
        Runs the interactive CLI loop.
        """
        print("Transaction File CLI Interface - Type 'help' for commands")
        while True:
            command = shlex.split(input("cli> "))
            if not command:
                continue

            cmd = command[0].lower()
            args = command[1:]

            if cmd == "exit":
                print("Exiting CLI.")
                break
            elif cmd == "help":
                print(
                    "\n **Available Commands:**\n"
                    "  setfile <file_path>                                   - Set the transaction file\n"
                    "  get <header/footer/transactions> [filters]            - Retrieve data with optional filters\n"
                    "  add header <name> <surname> <patronymic> <address>    - Add a new header\n"
                    "  add transaction <amount> <currency>                   - Add a new transaction\n"
                    "  modify header <field> <value>                         - Modify a header field\n"
                    "  modify transaction <id> <field=value> [<field=value>] - Modify transaction(s)\n"
                    "  lock <header_field | transaction_field> [value]       - Lock fields from modifications\n"
                    "  unlock <header_field | transaction_field> [value]     - Unlock fields from modifications\n"
                    "  validate                                              - Validate file integrity\n"
                    "  exit                                                  - Quit the CLI\n")
            elif cmd == "setfile" and len(args) == 1:
                self.set_file(args[0])
            elif not self.file_set:
                print("Error: No file set. Use 'setfile <file_path>' first.")
            elif cmd == "get":
                if len(args) < 1:
                    print("Error: No fields specified for retrieval.")
                    continue

                valid_sections = {"header", "footer", "transactions"}
                valid_filters = {"counter", "amount", "currency"}
                header_fields = {"name", "surname", "patronymic", "address"}
                footer_fields = {"total_counter", "control_sum"}

                sections = []
                filters = {}
                selected_fields = {
                    "header": set(),
                    "footer": set(),
                    "transactions": set()}

                for arg in args:
                    if "=" in arg:
                        key, value = arg.split("=", 1)
                        key = key.strip().lower()
                        value = value.strip().strip('"')
                        if key not in valid_filters:
                            print(
                                f"Error: Invalid filter '{key}'. Valid filters: {', '.join(valid_filters)}.")
                            continue
                        values = [v.strip() for v in value.split(",")]
                        try:
                            if key == "amount":
                                filters[key] = [Decimal(v) for v in values]
                            elif key == "counter":
                                filters[key] = [int(v) for v in values]
                            elif key == "currency":
                                filters[key] = values
                        except (ValueError, InvalidOperation):
                            print(f"Error: Invalid value for '{key}': {value}")
                            break
                    elif arg in valid_sections:
                        sections.append(arg)
                    elif arg in header_fields:
                        selected_fields["header"].add(arg)
                    elif arg in footer_fields:
                        selected_fields["footer"].add(arg)
                    else:
                        print(f"Error: Unknown field '{arg}'.")
                        continue
                else:
                    if not sections:
                        print(
                            "Error: No valid sections specified (header, footer, transactions).")
                        continue
                    result = self.manager.get_field(*sections, **filters)
                    filtered_result = {}
                    for section in sections:
                        if section in selected_fields and selected_fields[section]:
                            filtered_result[section] = {
                                field: getattr(
                                    result[section],
                                    field,
                                    None) for field in selected_fields[section]}
                        else:
                            filtered_result[section] = result[section]
                    if 'transactions' in filtered_result:
                        for transaction in filtered_result["transactions"]:
                            transaction.amount = str(
                                transaction.amount)  # A change just for pretty print
                    pprint(
                        filtered_result,
                        indent=2,
                        width=80,
                        compact=True,
                        sort_dicts=False)
            elif cmd == "modify" and len(args) >= 2:
                section = args[0].lower()  # "header" or "transaction"

                if section == "header":
                    if len(args) != 3:
                        print("Error: Use 'modify header <field> <value>'.")
                        continue

                    field_name = args[1]
                    new_value = args[2]

                    print(self.manager.modify_field(field_name, new_value))

                elif section == "transaction":
                    if len(args) < 3:
                        print(
                            "Error: Use 'modify transaction <counter> <field=value> [<field=value>]'.")
                        continue

                    if args[1].startswith("id="):
                        try:
                            transaction_id = int(args[1][3:])
                        except ValueError:
                            print("Error: Invalid transaction ID format.")
                            continue
                    else:
                        try:
                            transaction_id = int(args[1])
                        except ValueError:
                            print("Error: Transaction counter must be an integer.")
                            continue

                    modifications = {}
                    for arg in args[2:]:
                        if "=" in arg:
                            key, value = arg.split("=", 1)
                            key = key.strip().lower()
                            value = value.strip()

                            if key in ["amount", "a"]:
                                try:
                                    modifications["amount"] = Decimal(value)
                                except InvalidOperation:
                                    print(f"Error: Invalid amount '{value}'.")
                                    continue
                            elif key in ["currency", "c"]:
                                if len(value) != 3:
                                    print(
                                        f"Error: Currency must be exactly 3 letters. Got '{value}'.")
                                    continue
                                modifications["currency"] = value
                            else:
                                print(
                                    f"Error: Unknown field '{key}'. Use 'amount|a' or 'currency|c'.")
                                continue
                        else:
                            print(
                                f"Error: Invalid format '{arg}', use key=value.")
                            continue

                    if not modifications:
                        print("Error: No valid modifications provided.")
                        continue

                    modified_transaction = Transaction(
                        transaction_id=transaction_id,
                        amount=modifications.get("amount", None),
                        currency=modifications.get("currency", None)
                    )

                    print(
                        self.manager.modify_field(
                            "transactions",
                            [modified_transaction]))

                else:
                    print(
                        "Error: Use 'modify header <field> <value>' or 'modify transaction <counter> <field=value>'.")

            elif cmd == "add" and len(args) >= 2:
                sub_cmd = args[0].lower()

                if sub_cmd == "header":
                    if len(args) != 5:
                        print(
                            "Error: Use 'add header <name> <surname> <patronymic> <address>'.")
                        continue
                    result = self.manager.add_header(
                        Header(
                            name=args[1],
                            surname=args[2],
                            patronymic=args[3],
                            address=args[4])
                    )
                    print(result)

                elif sub_cmd == "transaction":
                    if len(args) != 3:
                        print("Error: Use 'add transaction <amount> <currency>'.")
                        continue

                    try:
                        amount = Decimal(args[1])
                        currency = args[2].upper()
                        if len(currency) != 3:
                            print("Error: Currency must be exactly 3 letters.")
                            continue
                        print(
                            self.manager.add_transaction(
                                Transaction(
                                    amount=amount,
                                    currency=currency)))
                    except InvalidOperation:
                        print("Error: Invalid amount format.")
            elif cmd == "lock" and len(args) >= 1:
                field_name = args[0]
                filter_value = None
                if len(args) == 2:
                    filter_value = args[1]
                    if field_name == "amount":
                        try:
                            filter_value = Decimal(filter_value)
                        except InvalidOperation:
                            print("Error: Invalid amount format.")
                            continue
                print(self.manager.lock_field(field_name, filter_value))
            elif cmd == "unlock" and len(args) >= 1:
                field_name = args[0]
                filter_value = args[1] if len(args) > 1 else None
                if field_name == "amount":
                    try:
                        filter_value = Decimal(filter_value)
                    except InvalidOperation:
                        print("Error: Invalid amount format.")
                        continue
                print(self.manager.unlock_field(field_name, filter_value))
            elif cmd == "validate":
                print(self.manager.validate())
            else:
                print("Invalid command. Type 'help' for usage.")


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    cli = CLI(file_path)
    cli.run()
