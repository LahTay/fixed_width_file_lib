import os
import pytest
from decimal import Decimal
from pathlib import Path
from fixed_width_lib.writer import Writer
from fixed_width_lib.logger import Logger
from fixed_width_lib.file import File
from fixed_width_lib.utils import Header, Transaction


def detect_line_ending(file_path):
    """
    Detects the line ending format (\n or \r\n) in a file.
    
    :param file_path: Path to the read file
    :return: str \r\n or \n depending on what the file is written in
    """
    
    with open(file_path, "r", newline="") as f:
        first_line = f.readline()
        return "\r\n" if first_line.endswith("\r\n") else "\n"


def test_set_and_change_header(test_output_path, file_stream_logger):
    """
    Verify that set_header correctly sets the header and change_header modifies only the specified fields.
    """
    file_path = test_output_path / "writer_set_and_change_header.txt"
    if file_path.exists():
        file_path.unlink()

    file = File(str(file_path), file_stream_logger, create_if_missing=True)
    file.open()

    writer = Writer(file, file_stream_logger)

    header = Header(name="Name123321", surname="Sur Na Me", patronymic="Something", address="Old Address")
    writer.set_header(header)

    os_end = detect_line_ending(file_path)

    with open(file_path, "r") as f:
        header_line = f.readline().rstrip(os_end)

    assert header_line[:2] == "01"
    assert header_line[2:30] == "Name123321".rjust(28)
    assert header_line[30:60] == "Sur Na Me".rjust(30)
    assert header_line[60:90] == "Something".rjust(30)
    assert header_line[90:120] == "Old Address".rjust(30)

    writer.change_header(Header(address="New Address"))

    file.close()

    with open(file_path, "r") as f:
        header_line = f.readline().rstrip(os_end)

    assert header_line[:2] == "01"
    assert header_line[2:30] == "Name123321".rjust(28)
    assert header_line[30:60] == "Sur Na Me".rjust(30)
    assert header_line[60:90] == "Something".rjust(30)
    assert header_line[90:120] == "New Address".rjust(30)


def test_add_transaction(test_output_path, file_stream_logger):
    """
    Verify that add_transaction correctly appends transactions to the file.
    """
    file_path = test_output_path / "writer_add_transaction.txt"
    if file_path.exists():
        file_path.unlink()

    file = File(str(file_path), file_stream_logger, create_if_missing=True)
    file.open()

    writer = Writer(file, file_stream_logger)

    writer.set_header(Header(name="Bob", surname="Smith", patronymic="D", address="123 Street"))

    writer.add_transaction(Transaction(amount=Decimal("1234.56"), currency="ABC"))
    writer.add_transaction(Transaction(amount=Decimal("9874563.85"), currency="XYZ"))

    file.close()

    os_end = detect_line_ending(file_path)

    with open(file_path, "r") as f:
        lines = f.readlines()

    transaction_line_1 = lines[1].rstrip(os_end)
    transaction_line_2 = lines[2].rstrip(os_end)

    assert transaction_line_1[:2] == "02"
    assert transaction_line_1[2:8] == "000001"
    assert transaction_line_1[8:20] == "000000123456"
    assert transaction_line_1[20:23] == "ABC"

    assert transaction_line_2[:2] == "02"
    assert transaction_line_2[2:8] == "000002"
    assert transaction_line_2[8:20] == "000987456385"
    assert transaction_line_2[20:23] == "XYZ"


def change_transactions(test_output_path, file_stream_logger):
    """
    Verify that change_transactions modifies only the specified transaction fields.
    """
    file_path = test_output_path / "writer_change_transaction.txt"
    if file_path.exists():
        file_path.unlink()

    file = File(str(file_path), file_stream_logger, create_if_missing=True)
    file.open()

    writer = Writer(file, file_stream_logger)

    writer.set_header(Header(name="Charlie", surname="Jones", patronymic="E", address="456 Road"))
    writer.add_transaction(Transaction(amount=Decimal("1500.00"), currency="USD"))
    writer.add_transaction(Transaction(amount=Decimal("2500.00"), currency="GBP"))


    os_end = detect_line_ending(file_path)
    with open(file_path, "r") as f:
        lines = f.readlines()

    transaction_line_1 = lines[1].rstrip(os_end)
    transaction_line_2 = lines[2].rstrip(os_end)

    assert transaction_line_1[8:20] == "000000150000"  # Amount updated
    assert transaction_line_1[20:23] == "USD"  # Currency unchanged

    assert transaction_line_2[8:20] == "000000250000"  # Amount unchanged
    assert transaction_line_2[20:23] == "GBP"  # Currency updated

    # Modify the first transaction's amount and the second one's currency
    writer.change_transactions([
        Transaction(transaction_id=1, amount=Decimal("1800.01")),
        Transaction(transaction_id=2, currency="AUD")
    ])

    file.close()

    with open(file_path, "r") as f:
        lines = f.readlines()

    transaction_line_1 = lines[1].rstrip(os_end)
    transaction_line_2 = lines[2].rstrip(os_end)
    footer_line = lines[3].rstrip(os_end)

    assert transaction_line_1[8:20] == "000000180001"
    assert transaction_line_1[20:23] == "USD"

    assert transaction_line_2[8:20] == "000000250000"
    assert transaction_line_2[20:23] == "AUD"

    assert footer_line[2:8] == "000002"
    assert footer_line[8:20] == "000000430001"


def test_footer_update(test_output_path, file_stream_logger):
    """
    Verify that the footer updates correctly after adding transactions.
    """
    file_path = test_output_path / "writer_footer_update.txt"

    if file_path.exists():
        file_path.unlink()

    file = File(str(file_path), file_stream_logger, create_if_missing=True)
    file.open()

    writer = Writer(file, file_stream_logger)

    writer.set_header(Header(name="Daniel", surname="White", patronymic="F", address="789 Blvd"))
    writer.add_transaction(Transaction(amount=Decimal("500.00"), currency="GBP"))
    writer.add_transaction(Transaction(amount=Decimal("1200.00"), currency="EUR"))

    file.close()

    os_end = detect_line_ending(file_path)

    with open(file_path, "r") as f:
        lines = f.readlines()

    footer_line = lines[-1].rstrip(os_end)
    assert footer_line[:2] == "03"
    assert footer_line[2:8] == "000002"
    assert footer_line[8:20] == "000000170000"

@pytest.mark.parametrize("invalid_amount", [100.0, "100.0", None])
def test_invalid_transaction_amount(test_output_path, invalid_amount, file_stream_logger, caplog):
    """
    Verify that add_transaction raises a TypeError for non-Decimal amounts.
    """
    file_path = test_output_path / "writer_invalid_transaction.txt"
    if file_path.exists():
        file_path.unlink()

    file = File(str(file_path), file_stream_logger, create_if_missing=True)
    file.open()

    writer = Writer(file, file_stream_logger)
    writer.set_header(Header(name="Eric", surname="Brown", patronymic="G", address="987 Street"))

    with caplog.at_level("ERROR"):  # Capture only ERROR logs
        writer.add_transaction(Transaction(amount=invalid_amount, currency="JPY"))

    file.close()

    if invalid_amount is None:
        assert any("cannot be None" in record.message for record in caplog.records), \
            f"Expected log message not found! Logs: {[record.message for record in caplog.records]}"
    else:
        assert any("has to be of Decimal class" in record.message for record in caplog.records), \
            f"Expected log message not found! Logs: {[record.message for record in caplog.records]}"
