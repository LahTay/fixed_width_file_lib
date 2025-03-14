import logging
import pytest
from pathlib import Path
from fixed_width_lib.writer import Writer
from decimal import Decimal
from fixed_width_lib.logger import LogHandler
def test_change_header(test_output_path, file_stream_logger):
    """
    Verify that change_header updates only the specified header fields.
    The header record is expected to be 120 characters long with:
      - Positions 1-2: Fixed "01"
      - Positions 3-30: Name (28 characters)
      - Positions 31-60: Surname (30 characters)
      - Positions 61-90: Patronymic (30 characters)
      - Positions 91-120: Address (30 characters)
    """
    file_path = test_output_path / "writer_change_header.txt"
    writer = Writer(str(file_path), "w", file_stream_logger)
    writer.set_header(name="Alice", surname="Brown", patronymic="C", address="Old Address")
    writer.change_header(address="New Address")
    writer.write()

    with open(file_path, "r") as f:
        header = f.readline().rstrip("\n")

    # Verify fixed field "01" is intact
    assert header[0:2] == "01"
    # Verify name, surname, patronymic remain unchanged
    assert header[2:30] == "Alice".ljust(28)
    assert header[30:60] == "Brown".ljust(30)
    assert header[60:90] == "C".ljust(30)
    # Verify that address was updated
    assert header[90:120] == "New Address".ljust(30)

def test_change_transaction(test_output_path, file_stream_logger):
    """
    Verify that change_transaction updates only the specified fields of a transaction.
    A transaction record (120 characters) has:
      - Positions 1-2: Fixed "02"
      - Positions 3-8: Counter (6 digits, e.g. "000001" for first, "000002" for second)
      - Positions 9-20: Amount (12 digits, e.g. "000000002000" for 2000.00)
      - Positions 21-23: Currency (3 characters)
      - Positions 24-120: Reserved (97 spaces)
    """
    file_path = test_output_path / "writer_change_transaction.txt"
    writer = Writer(str(file_path), "w", file_stream_logger)
    writer.set_header(name="Bob", surname="Smith", patronymic="D", address="123 Street")
    writer.add_transaction(amount=Decimal("1000.00"), currency="EUR")
    writer.add_transaction(amount=Decimal("2000.00"), currency="EUR")
    # Now update the second transaction (idx=2) to change amount and currency.
    writer.change_transaction(2, amount=Decimal("2500.00"), currency="USD")
    writer.write()

    with open(file_path, "r") as f:
        lines = f.readlines()

    # Assuming the first line is the header, transaction lines follow,
    # and the last line is the footer.
    # Retrieve the second transaction record.
    transaction_line = lines[2].rstrip("\n")
    # Verify fixed part "02"
    assert transaction_line[0:2] == "02"
    # Verify counter remains "000002"
    assert transaction_line[2:8] == "000002"
    # Verify updated amount: 2500.00 should be formatted as "000000002500"
    assert transaction_line[8:20] == "000000002500"
    # Verify updated currency "USD"
    assert transaction_line[20:23] == "USD"
    # And reserved part remains spaces.
    assert transaction_line[23:120] == " " * 97

def test_change_footer(test_output_path, file_stream_logger):
    """
    Verify that change_footer updates only the specified footer fields.
    The footer record (120 characters) should have:
      - Positions 1-2: Fixed "03"
      - Positions 3-8: Total transaction count (6 digits)
      - Positions 9-20: Control sum (12 digits)
      - Positions 21-120: Reserved (100 spaces)
    In this test, we'll override the control sum.
    """
    file_path = test_output_path / "writer_change_footer.txt"
    writer = Writer(str(file_path), "w", file_stream_logger)
    writer.set_header(name="Eve", surname="White", patronymic="F", address="789 Avenue")
    writer.add_transaction(amount=Decimal("500.00"), currency="GBP")
    writer.add_transaction(amount=Decimal("1500.00"), currency="GBP")
    writer.write()

    with open(file_path, "r") as f:
        lines = f.readlines()

    footer = lines[-1].rstrip("\n")
    # Verify fixed "03" is intact.
    assert footer[0:2] == "03"
    # Verify total counter remains (should be "000002" for two transactions)
    assert footer[2:8] == "000002"
    # Verify that the control sum field is updated as specified.
    assert footer[8:20] == "000000003000"
    # Reserved field should be 100 spaces.
    assert footer[20:120] == " " * 100

def test_update_individual_fields(test_output_path, file_stream_logger):
    """
    Verify that individual updates can be applied without resetting the entire record.
    For example, update a header field and then update a transaction field separately.
    """
    file_path = test_output_path / "writer_individual_update.txt"
    writer = Writer(str(file_path), "w", file_stream_logger)
    # Set initial header and add one transaction.
    writer.set_header(name="Carol", surname="King", patronymic="G", address="Initial Address")
    writer.add_transaction(amount=Decimal("3000.00"), currency="CAD")
    writer.write()

    # Now, simulate updating the _file by changing the header's surname and the transaction's currency.
    writer.change_header(surname="Queen")
    writer.change_transaction(1, currency="AUD")  # Update the first (and only) transaction.
    writer.write()

    with open(file_path, "r") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n")
    # Surname should now be updated to "Queen"
    assert header[30:60] == "Queen".ljust(30)

    transaction = lines[1].rstrip("\n")
    # The first transaction's currency field should now be "AUD"
    assert transaction[20:23] == "AUD"

@pytest.mark.parametrize("bad_amount", [100, 100.0, "100.0", None])
def test_transaction_amount_strict_decimal(test_output_path, bad_amount, file_stream_logger):
    """
    Test that add_transaction raises a TypeError when the amount is not a decimal.Decimal.
    """
    file_path = test_output_path / "writer_bad_amount.txt"
    writer = Writer(str(file_path), "w", file_stream_logger)
    # Set a header so that transactions can be added.
    writer.set_header(name="Test", surname="User", patronymic="X", address="Some Address")

    with pytest.raises(TypeError):
        writer.add_transaction(amount=bad_amount, currency="USD")