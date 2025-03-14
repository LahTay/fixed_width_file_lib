from pathlib import Path
from fixed_width_lib.logger import Logger, LogHandler
from fixed_width_lib.transaction_manager import TransactionManager
import shlex


class CLI:
    def __init__(self):
        self.logger = Logger("cli_logger",
                             [LogHandler.FILE.value("./logs/cli.log"), LogHandler.STREAM.value()],
                             "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.logger.set_level("INFO")
        self.logger.set_global_level("INFO")
        self.manager = TransactionManager(self.logger)
        self.file_set = False

    def set_file(self, file_path: str):
        self.manager.set_file(Path(file_path))
        self.file_set = True
        print(f"File set to: {file_path}")

    def parse_filters(self, filters: list[str]) -> dict:
        """Parses filters from CLI input into a structured dictionary."""
        parsed_filters = {}
        for filter_str in filters:
            if '=' in filter_str:
                key, value = filter_str.split('=', 1)
                key = key.strip().lower()
                value = value.strip().strip('"')  # Remove potential surrounding quotes

                if key in ("amount", "counter"):
                    values = value.split(',')
                    parsed_filters[key] = [Decimal(v) if '.' in v else int(v) for v in values]
                elif key == "currency":
                    parsed_filters[key] = value.split(',')

        return parsed_filters

    def run(self):
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
                print("Available commands:")
                print("  setfile <file_path>    - Set the transaction _file")
                print("  get <header/footer/transactions> [filters] - "
                      "Retrieve a header, footer, or transactions with filters")
                print("  modify <field> <value> - Modify a field value")
                print("  add <id> <amount> <currency> - Add a new transaction")
                print("  lock <field>           - Lock a field from modifications")
                print("  validate               - Validate _file integrity")
                print("  exit                   - Quit the CLI")
            elif cmd == "setfile" and len(args) == 1:
                self.set_file(args[0])
            elif not self.file_set:
                print("Error: No _file set. Use 'setfile <file_path>' first.")
            elif cmd == "get":
                if len(args) < 1:
                    print("Error: No fields specified for retrieval.")
                    continue

                fields = []
                filters = []
                for arg in args:
                    if "=" in arg:
                        filters.append(arg)
                    else:
                        fields.append(arg.lower())

                parsed_filters = self.parse_filters(filters)
                result = self.manager.get_field(*fields, **parsed_filters)
                print(result)
            elif cmd == "modify" and len(args) == 2:
                print(self.manager.modify_field(args[0], args[1]))
            elif cmd == "add" and len(args) == 3:
                print(self.manager.add_transaction(int(args[0]), args[1], args[2]))
            elif cmd == "lock" and len(args) == 1:
                print(self.manager.lock_field(args[0]))
            elif cmd == "validate":
                print(self.manager.validate())
            else:
                print("Invalid command. Type 'help' for usage.")


if __name__ == "__main__":
    cli = CLI()
    cli.run()
