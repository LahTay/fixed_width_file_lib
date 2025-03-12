import pytest
from pathlib import Path
from fixed_width_lib.reader import Reader  # Your Reader implementation
from fixed_width_lib.logger import LogHandler

def test_reader_read_entire_file(example_file: Path, file_stream_logger):
    """
    Verify that read() parses the entire fixed-width file correctly.
    Expected structure:
      - header: a dict with fields: "Field ID", "Name", "Surname", "Patronymic", "Address"
      - transactions: a list of dicts, each with fields: "Field ID", "Counter", "Amount", "Currency"
      - footer: a dict with fields: "Field ID", "Total Counter", "Control Sum"
    """
    reader = Reader(str(example_file), "r", file_stream_logger)
    result = reader.read()

    # Verify that we got the three main sections.
    assert "header" in result
    assert "transactions" in result
    assert "footer" in result

    # Verify header fields (adjust expected values as needed).
    header = result["header"]
    assert header.get("Field ID") == "01"
    assert header.get("Name").strip() == "John"
    assert header.get("Surname").strip() == "Doe"
    assert header.get("Patronymic").strip() == "M"
    assert header.get("Address").strip() == "123 Main St"

    # Verify transactions – assume there are 2 transactions.
    transactions = result["transactions"]
    assert isinstance(transactions, list)
    assert len(transactions) == 2

    t1 = transactions[0]
    assert t1.get("Field ID") == "02"
    assert t1.get("Counter") == "000001"
    assert t1.get("Amount") == "000000002000"
    assert t1.get("Currency") == "USD"

    t2 = transactions[1]
    assert t2.get("Field ID") == "02"
    assert t2.get("Counter") == "000002"
    assert t2.get("Amount") == "000000001500"
    assert t2.get("Currency") == "EUR"

    # Verify footer.
    footer = result["footer"]
    assert footer.get("Field ID") == "03"
    assert footer.get("Total Counter") == "000002"
    assert footer.get("Control Sum") == "000000003500"


def test_reader_get_header_fields(example_file: Path, file_stream_logger):
    """
    Verify that get_header_fields returns the correct header values for the requested fields.
    """
    reader = Reader(str(example_file), "r", file_stream_logger)
    # Request only a subset of header fields.
    header_fields = reader.get_header_fields(["Name", "Surname", "Address"])
    assert header_fields["Name"].strip() == "John"
    assert header_fields["Surname"].strip() == "Doe"
    assert header_fields["Address"].strip() == "123 Main St"
    # Optionally, if a field is not present, your implementation should decide how to handle it.
    # For example, you might return None or raise an error.


def test_reader_get_transaction(example_file: Path, file_stream_logger):
    """
    Verify that get_transaction(idx) returns the correct transaction record.
    Assumes that the first transaction has index 1.
    """
    reader = Reader(str(example_file), "r", file_stream_logger)
    transaction1 = reader.get_transaction(1)
    transaction2 = reader.get_transaction(2)

    # Verify first transaction.
    assert transaction1.get("Field ID") == "02"
    assert transaction1.get("Counter") == "000001"
    assert transaction1.get("Amount") == "000000002000"
    assert transaction1.get("Currency") == "USD"

    # Verify second transaction.
    assert transaction2.get("Field ID") == "02"
    assert transaction2.get("Counter") == "000002"
    assert transaction2.get("Amount") == "000000001500"
    assert transaction2.get("Currency") == "EUR"


def test_reader_get_footer_field(example_file: Path, file_stream_logger):
    """
    Verify that get_footer_field returns the correct footer values for the requested fields.
    """
    reader = Reader(str(example_file), "r", file_stream_logger)
    footer_fields = reader.get_footer_field(["Total Counter", "Control Sum"])
    assert footer_fields["Total Counter"] == "000002"
    assert footer_fields["Control Sum"] == "000000003500"
