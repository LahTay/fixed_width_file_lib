import pytest
from decimal import Decimal
from pathlib import Path
from fixed_width_lib.file import File
from fixed_width_lib.reader import Reader
from fixed_width_lib.writer import Writer
from fixed_width_lib.logger import Logger
from fixed_width_lib.utils import Header, Transaction, Footer
from fixed_width_lib.transaction_manager import TransactionManager


def _create_manager(test_output_path, file_stream_logger, filename):
    """Creates a fresh TransactionManager for each test."""
    file_path = test_output_path / filename
    if file_path.exists():
        file_path.unlink()

    manager = TransactionManager(file_stream_logger)
    manager.set_file(file_path)
    return manager, file_path


def _create_necessary_starting_fields(
        manager: TransactionManager,
        transactions=0):
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
    Test modifying different header fields.
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
    Test that modifying a locked header field is prevented.
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


@pytest.mark.parametrize("amount, expected, num",
                         [("100.00",
                           "Added transaction: Transaction(transaction_id=None, amount=Decimal('100.00'), currency='USD')",
                           0),
                          ("200.01",
                           "Added transaction: Transaction(transaction_id=None, amount=Decimal('200.01'), currency='USD')",
                             1),
                          ])
def test_add_valid_transaction(
        test_output_path,
        file_stream_logger,
        amount,
        expected,
        num):
    """
    Test adding valid transactions with different amounts and testing if both adding to file with no transactions and
    with transactions works.
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
    assert amount.replace(
        ".", "") == added_transaction[8:20].strip(" ").lstrip("0")


@pytest.mark.parametrize("invalid_amount, num",
                         [("100.001", 0), ("200.0001", 1)])
def test_add_invalid_transaction_amount(
        test_output_path,
        file_stream_logger,
        invalid_amount,
        num,
        caplog):
    """
    Test that adding a transaction with more than two decimal places fails.
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
    Test modifying an existing transaction.
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
    Test modifying a locked transaction fails.
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
    Test file validation when all transactions and footer match.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_validate_valid_file.txt")
    _create_necessary_starting_fields(manager, transactions=10)

    assert manager.validate() == "File validation successful."


def test_validate_invalid_transaction_count(
        test_output_path, file_stream_logger, caplog):
    """
    Test validation failure when transaction count does not match footer.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_validate_invalid_transaction_count.txt")
    _create_necessary_starting_fields(manager, transactions=4)

    # Manually corrupt the file by removing one transaction
    with open(file_path, "r+") as f:
        lines = f.readlines()
        f.seek(0)
        del lines[-2]
        f.writelines(lines)  # Remove last transaction
        f.truncate()
        result = manager.validate()
    with caplog.at_level("ERROR"):
        result = manager.validate()

    assert "Error: Footer total_counter 4 does not match transaction count 3" in caplog.text
    assert "Error: Footer total_counter 4 does not match transaction count 3." == result


def test_full_transaction_pipeline(
        test_output_path,
        file_stream_logger,
        caplog):
    """
    🚀 Full pipeline test for TransactionManager.
    """
    manager, file_path = _create_manager(
        test_output_path, file_stream_logger, "test_full_transaction_pipeline.txt")

    # Step 1: Add Header
    header = Header(
        name="John",
        surname="Doe",
        patronymic="Smith",
        address="123 Main St")
    assert manager.add_header(header) == "Header added successfully."

    # Step 2: Add Transactions
    transactions = [
        Transaction(amount=Decimal("100.00"), currency="USD"),
        Transaction(amount=Decimal("250.50"), currency="EUR"),
        Transaction(amount=Decimal("500.75"), currency="GBP"),
    ]
    for t in transactions:
        assert "Added transaction" in manager.add_transaction(t)

    # Step 3: Modify Transaction
    modified_tx = Transaction(
        transaction_id=2,
        amount=Decimal("400.50"),
        currency="JPY")
    what = manager.modify_field("transactions", [modified_tx])
    assert "Updated transactions in" in what

    # Step 4: Lock Fields and Transactions
    assert "Locked header field" in manager.lock_field("address")
    assert "Locked transactions where counter=3" in manager.lock_field(
        "counter", 3)

    # Step 5: Try Modifying Locked Fields (Should Fail)
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

    # Step 6: Validate File
    assert manager.validate() == "File validation successful."

    # Step 7: Try Adding Invalid Transactions
    invalid_transactions = [
        Transaction(
            amount=Decimal("100.001"),
            currency="USD"),
        # Too many decimal places
        Transaction(amount=None, currency="EUR"),  # Missing amount
        Transaction(amount=Decimal("50.00"), currency=""),  # Missing currency
    ]
    for t in invalid_transactions:
        with caplog.at_level("ERROR"):
            result = manager.add_transaction(t)
        assert "Error" in result

    # Step 8: Final Transaction Count Check
    transactions = manager.get_field("transactions")["transactions"]
    assert len(transactions) == 3  # Should be 3 valid transactions

    # Step 9: Final Log Check
    assert "File validation successful." in caplog.text
    assert "Locked transactions where counter is 3" in caplog.text

# from fixed_width_lib.logger import LogHandler
# full_transaction_pipeline(Path("./output"), Logger("", [LogHandler.STREAM.value()], ""), "")
