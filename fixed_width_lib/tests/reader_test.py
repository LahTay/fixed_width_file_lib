import pytest
from decimal import Decimal

from fixed_width_lib.file import File
from fixed_width_lib.reader import Reader
from fixed_width_lib.utils import Header, Footer, Transaction, Content


def test_reader_read_entire_file(example_file, file_stream_logger):
    """
    Test that `read()` correctly parses the entire fixed-width file.

    :param example_file: Path to the example fixed-width file.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    with File(str(example_file), file_stream_logger) as file_handler:
        reader = Reader(file_handler, file_stream_logger)
        content = reader.read()

    assert content is not None
    assert isinstance(content, Content)

    # Verify Header
    assert content.header.name == "Some Name"
    assert content.header.surname == "Some Surname"
    assert content.header.patronymic == "Some Other Surname"
    assert content.header.address == "Some Address, 1, 10"

    # Verify Transactions
    assert len(content.transactions) == 3

    assert content.transactions[0] == Transaction(
        transaction_id=1, amount=Decimal("100.00"), currency="USD")
    assert content.transactions[1] == Transaction(
        transaction_id=2, amount=Decimal("200.00"), currency="EUR")
    assert content.transactions[2] == Transaction(
        transaction_id=3, amount=Decimal("300.00"), currency="GBP")

    # Verify Footer
    assert content.footer.total_counter == 3
    assert content.footer.control_sum == Decimal("600.00")


def test_reader_read_header(example_file, file_stream_logger):
    """
    Test that `read_header()` correctly parses the header section.

    :param example_file: Path to the example fixed-width file.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    with File(str(example_file), file_stream_logger) as file_handler:
        reader = Reader(file_handler, file_stream_logger)
        header = reader.read_header()

    assert isinstance(header, Header)
    assert header.name == "Some Name"
    assert header.surname == "Some Surname"
    assert header.patronymic == "Some Other Surname"
    assert header.address == "Some Address, 1, 10"


def test_reader_read_transactions(example_file, file_stream_logger):
    """
    Test that `read_transactions()` correctly reads all transactions.

    :param example_file: Path to the example fixed-width file.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    with File(str(example_file), file_stream_logger) as file_handler:
        reader = Reader(file_handler, file_stream_logger)
        transactions = reader.read_transactions()

    assert len(transactions) == 3

    assert transactions[0] == Transaction(
        transaction_id=1,
        amount=Decimal("100.00"),
        currency="USD")
    assert transactions[1] == Transaction(
        transaction_id=2,
        amount=Decimal("200.00"),
        currency="EUR")
    assert transactions[2] == Transaction(
        transaction_id=3,
        amount=Decimal("300.00"),
        currency="GBP")


def test_reader_read_footer(example_file, file_stream_logger):
    """
    Test that `read_footer()` correctly parses the footer section.

    :param example_file: Path to the example fixed-width file.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    with File(str(example_file), file_stream_logger) as file_handler:
        reader = Reader(file_handler, file_stream_logger)
        footer = reader.read_footer()

    assert isinstance(footer, Footer)
    assert footer.total_counter == 3
    assert footer.control_sum == Decimal("600.00")


def test_reader_get_transactions(example_file, file_stream_logger):
    """
    Test `get_transactions()` method with different filtering criteria.

    :param example_file: Path to the example fixed-width file.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    with File(str(example_file), file_stream_logger) as file_handler:
        reader = Reader(file_handler, file_stream_logger)

        transactions = reader.get_transactions(counter=1)
        assert len(transactions) == 1
        assert transactions[0] == Transaction(
            transaction_id=1, amount=Decimal("100.00"), currency="USD")

        transactions = reader.get_transactions(amount="200.00")
        assert len(transactions) == 1
        assert transactions[0] == Transaction(
            transaction_id=2, amount=Decimal("200.00"), currency="EUR")

        transactions = reader.get_transactions(currency="GBP")
        assert len(transactions) == 1
        assert transactions[0] == Transaction(
            transaction_id=3, amount=Decimal("300.00"), currency="GBP")

        transactions = reader.get_transactions(counter=[1, 2], currency="USD")
        assert len(transactions) == 1
        assert transactions[0] == Transaction(
            transaction_id=1, amount=Decimal("100.00"), currency="USD")

        transactions = reader.get_transactions(limit=2)
        assert len(transactions) == 2


def test_reader_invalid_header(test_data_path, file_stream_logger, caplog):
    """
    Test handling of an invalid header and ensure error logging works.

    :param test_data_path: Path to the directory containing test files.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    :param caplog: Pytest fixture for capturing log messages.
    """
    with File(str(test_data_path / "invalid_header"), file_stream_logger) as file_handler:
        reader = Reader(file_handler, file_stream_logger)

        with caplog.at_level("ERROR"):
            header = reader.read_header()

    assert header is None
    assert any(
        "Invalid header record" in record.message for record in caplog.records)


def test_reader_invalid_footer(test_data_path, file_stream_logger, caplog):
    """
    Test handling of an invalid footer and ensure error logging works.

    :param test_data_path: Path to the directory containing test files.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    :param caplog: Pytest fixture for capturing log messages.
    """
    with File(str(test_data_path / "invalid_footer"), file_stream_logger) as file_handler:
        reader = Reader(file_handler, file_stream_logger)

        with caplog.at_level("ERROR"):
            footer = reader.read_footer()

    assert footer is None
    assert any(
        "Footer record not found" in record.message for record in caplog.records)
