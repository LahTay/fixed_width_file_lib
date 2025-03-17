from decimal import Decimal
import pytest

from fixed_width_lib.utils import Header, Transaction
from fixed_width_lib.transaction_manager import TransactionManager


def _create_manager(test_output_path, file_stream_logger, filename):
    """
    Creates a fresh TransactionManager instance for each test.

    :param test_output_path: Path to the directory where test output files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param filename: Name of the file to be used for testing.
    :return: A tuple containing the TransactionManager instance and the file path.
    """
    file_path = test_output_path / filename
    if file_path.exists():
        file_path.unlink()

    manager = TransactionManager(file_stream_logger)
    manager.set_file(file_path)
    return manager, file_path


def _create_necessary_starting_fields(manager: TransactionManager, transactions=0):
    """
    Adds a header and a specified number of transactions to the test file.

    :param manager: The TransactionManager instance handling the test file.
    :param transactions: Number of transactions to add.
    """
    manager.add_header(Header("name", "surname", "p", "address"))
    for i in range(transactions):
        manager.add_transaction(
            Transaction(
                amount=Decimal(
                    100 * i),
                currency="PLN"))


@pytest.mark.parametrize("header_field, new_value", [
    ("name", "Newest Changed Name"),
    ("surname", "New Surname"),
    ("address", "Address Changed 123, 0"),
])
def test_modify_header(
        test_output_path,
        file_stream_logger,
        header_field,
        new_value):
    """
    Tests modifying different header fields.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param header_field: The header field to modify.
    :param new_value: The new value to set for the header field.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, f"test_modify_header_{header_field}.txt")
    _create_necessary_starting_fields(manager, 0)
    result = manager.modify_field(header_field, new_value)
    assert result == f"Updated {header_field}: {new_value}"

    header = manager.get_field("header")["header"]
    assert getattr(header, header_field) == new_value

    # Also check without using class for certainty
    with open(file_path, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0
    assert new_value in lines[0]


def test_modify_header_locked(test_output_path, file_stream_logger, caplog):
    """
    Tests that modifying a locked header field is prevented.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param caplog: Pytest logging capture fixture.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_modify_header_locked.txt")
    _create_necessary_starting_fields(manager, 0)
    manager.lock_field("name")

    with caplog.at_level("WARNING"):
        result = manager.modify_field("name", "Blocked Name")

    assert "Attempt to modify locked field: name" in caplog.text
    assert result == "Error: Field 'name' is locked and cannot be modified."

    with open(file_path, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0
    assert "name" == lines[0][2:30].strip(" ")


@pytest.mark.parametrize("amount, expected, num", [
                          ("100.00", "Added transaction:"
                                     " Transaction(transaction_id=None, amount=Decimal('100.00'), currency='USD')", 0),
                          ("200.01", "Added transaction:"
                                     " Transaction(transaction_id=None, amount=Decimal('200.01'), currency='USD')", 1),
                          ])
def test_add_valid_transaction(
        test_output_path,
        file_stream_logger,
        amount,
        expected,
        num):
    """
    Tests adding valid transactions with different amounts.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param amount: The amount for the transaction.
    :param expected: The expected response message.
    :param num: The transaction number (to test appending transactions correctly).
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, f"test_add_valid_transaction_{amount}.txt")
    _create_necessary_starting_fields(manager, num)
    transaction = Transaction(amount=Decimal(amount), currency="USD")
    result = manager.add_transaction(transaction)
    assert result == expected

    with open(file_path, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0
    added_transaction = lines[num + 1]
    assert amount.replace(".", "") == added_transaction[8:20].strip(" ").lstrip("0")


@pytest.mark.parametrize("invalid_amount, num", [("100.001", 0), ("200.0001", 1)])
def test_add_invalid_transaction_amount(
        test_output_path,
        file_stream_logger,
        invalid_amount,
        num,
        caplog):
    """
    Tests that adding a transaction with more than two decimal places fails.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param invalid_amount: Invalid amount with too many decimal places.
    :param num: Transaction number.
    :param caplog: Pytest logging capture fixture.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, f"test_add_invalid_transaction_{invalid_amount}.txt")
    _create_necessary_starting_fields(manager, num)
    transaction = Transaction(amount=Decimal(invalid_amount), currency="USD")

    with caplog.at_level("ERROR"):
        result = manager.add_transaction(transaction)

    assert "Error: Amount must have at most two decimal places" in result
    assert f"Invalid transaction amount: {invalid_amount}" in caplog.text


def test_modify_transaction(test_output_path, file_stream_logger):
    """
    Tests modifying an existing transaction.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_modify_transaction.txt")
    _create_necessary_starting_fields(manager, 0)
    manager.add_transaction(
        Transaction(
            amount=Decimal("50.00"),
            currency="JPY"))
    manager.add_transaction(
        Transaction(
            amount=Decimal("50.00"),
            currency="GBY"))

    manager.modify_field("transactions", [
        Transaction(transaction_id=1, amount=Decimal("75.01")),
        Transaction(transaction_id=2, currency="PLN")
    ])

    transactions = manager.get_field("transactions")["transactions"]
    assert transactions[0].amount == Decimal("75.01")
    assert transactions[1].currency == "PLN"

    with open(file_path, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0
    transaction1 = lines[1]
    transaction2 = lines[2]
    assert "7501" == transaction1[8:20].strip(" ").lstrip("0")
    assert "JPY" == transaction1[20:23].strip(" ")
    assert "5000" == transaction2[8:20].strip(" ").lstrip("0")
    assert "PLN" == transaction2[20:23].strip(" ")


def test_modify_locked_transaction(
        test_output_path,
        file_stream_logger,
        caplog):
    """
    Test that modifying a locked transaction fails.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param caplog: Pytest logging capture fixture.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_modify_locked_transaction")
    _create_necessary_starting_fields(manager, 0)
    manager.add_transaction(
        Transaction(
            amount=Decimal("150.00"),
            currency="EUR"))
    manager.lock_field("amount")
    result = manager.modify_field(
        "transactions", [
            Transaction(
                transaction_id=1, amount=Decimal("200.00"))])

    with caplog.at_level("WARNING"):
        result = manager.modify_field(
            "transactions", [
                Transaction(
                    transaction_id=1, amount=Decimal("200.00"))])

    assert "Attempt to modify locked transaction" in caplog.text
    assert "Updated transactions where" not in result


def test_validate_valid_file(test_output_path, file_stream_logger):
    """
    Test file validation when header, transactions and the footer match expected values.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_validate_valid_file.txt")
    _create_necessary_starting_fields(manager, transactions=10)

    assert manager.validate() == "File validation successful."


def test_validate_invalid_transaction_count(
        test_output_path, file_stream_logger, caplog):
    """
    Test validation failure when the transaction count does not match the footer.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param caplog: Pytest logging capture fixture.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_validate_invalid_transaction_count.txt")
    _create_necessary_starting_fields(manager, transactions=4)

    # Manually corrupt the file by removing one transaction
    with open(file_path, "r+") as f:
        lines = f.readlines()
        f.seek(0)
        del lines[-2]
        f.writelines(lines)
        f.truncate()
    with caplog.at_level("ERROR"):
        result = manager.validate()

    assert "Footer total_counter 4 does not match transaction count 3." in caplog.text
    assert "Footer total_counter 4 does not match transaction count 3." in result


def test_full_transaction_pipeline(
        test_output_path,
        file_stream_logger,
        caplog):
    """
    Full possible pipeline test for TransactionManager.

    This test does the following:
    1. Adds a header.
    2. Adds multiple transactions.
    3. Modifies a transaction.
    4. Locks header and transaction fields.
    5. Attempts to modify locked fields (should fail).
    6. Validates the file.
    7. Attempts to add invalid transactions (should fail).
    8. Ensures the final transaction count is correct.
    9. Verifies expected log outputs.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance for logging test events.
    :param caplog: Pytest logging capture fixture.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_full_transaction_pipeline.txt")

    # Step 1
    header = Header(
        name="John",
        surname="Doe",
        patronymic="Smith",
        address="123 Main St")
    assert manager.add_header(header) == "Header added successfully."

    # Step 2
    transactions = [
        Transaction(amount=Decimal("100.00"), currency="USD"),
        Transaction(amount=Decimal("250.50"), currency="EUR"),
        Transaction(amount=Decimal("500.75"), currency="GBP"),
    ]
    for t in transactions:
        assert "Added transaction" in manager.add_transaction(t)

    # Step 3
    modified_tx = Transaction(
        transaction_id=2,
        amount=Decimal("400.50"),
        currency="JPY")
    what = manager.modify_field("transactions", [modified_tx])
    assert "Updated transactions in" in what

    # Step 4
    assert "Locked header field" in manager.lock_field("address")
    assert "Locked transactions where counter=3" in manager.lock_field(
        "counter", 3)

    # Step 5
    with caplog.at_level("WARNING"):
        result = manager.modify_field("address", "Locked Address")
    assert "Attempt to modify locked field" in caplog.text
    assert result == "Error: Field 'address' is locked and cannot be modified."

    with caplog.at_level("WARNING"):
        result = manager.modify_field(
            "transactions", [
                Transaction(
                    transaction_id=3, amount=Decimal("600.00"))])
    assert "Attempt to modify locked transaction" in caplog.text

    # Step 6
    assert manager.validate() == "File validation successful."

    # Step 7
    invalid_transactions = [
        Transaction(
            amount=Decimal("100.001"),
            currency="USD"),
        Transaction(amount=None, currency="EUR"),
        Transaction(amount=Decimal("50.00"), currency=""),
    ]
    for t in invalid_transactions:
        with caplog.at_level("ERROR"):
            result = manager.add_transaction(t)
        assert "Error" in result

    # Step 8
    transactions = manager.get_field("transactions")["transactions"]
    assert len(transactions) == 3

    # Step 9
    assert "File validation successful." in caplog.text
    assert "Locked transactions where counter is 3" in caplog.text
