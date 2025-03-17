from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

LINESIZE = 120
MAX_TRANSACTIONS = 20000


class HeaderFields:
    """
    Defines the byte offsets for header fields in a fixed-width file.

    Attributes:
        IDX (tuple): The index range for the header identifier.
        NAME (tuple): The index range for the name field.
        SURNAME (tuple): The index range for the surname field.
        PATRONYMIC (tuple): The index range for the patronymic field.
        ADDRESS (tuple): The index range for the address field.
        FIELD_SIZES (dict): Dictionary mapping field names to their maximum lengths.
    """
    IDX = (0, 2)
    NAME = (2, 30)
    SURNAME = (30, 60)
    PATRONYMIC = (60, 90)
    ADDRESS = (90, 120)

    FIELD_SIZES = {
        "name": 28,
        "surname": 30,
        "patronymic": 30,
        "address": 30
    }


class TransactionFields:
    """
    Defines the byte offsets for transaction fields in a fixed-width file.

    Attributes:
        IDX (tuple): The index range for the transaction identifier.
        COUNTER (tuple): The index range for the transaction counter.
        AMOUNT (tuple): The index range for the transaction amount.
        CURRENCY (tuple): The index range for the transaction currency.
        RESERVED (tuple): The index range for reserved space.
        FIELD_SIZES (dict): Dictionary mapping field names to their maximum lengths.
    """
    IDX = (0, 2)
    COUNTER = (2, 8)
    AMOUNT = (8, 20)
    CURRENCY = (20, 23)
    RESERVED = (23, 120)

    FIELD_SIZES = {
        "counter": 6,
        "amount": 12,
        "currency": 3,
        "reserved": 97
    }


class FooterFields:
    """
    Defines the byte offsets for footer fields in a fixed-width file.

    Attributes:
        IDX (tuple): The index range for the footer identifier.
        TOTAL_COUNTER (tuple): The index range for the total number of transactions.
        CONTROL_SUM (tuple): The index range for the control sum of all transaction amounts.
        RESERVED (tuple): The index range for reserved space.
        FIELD_SIZES (dict): Dictionary mapping field names to their maximum lengths.
    """
    IDX = (0, 2)
    TOTAL_COUNTER = (2, 8)
    CONTROL_SUM = (8, 20)
    RESERVED = (20, 120)

    FIELD_SIZES = {
        "total_counter": 6,
        "control_sum": 12,
        "reserved": 100
    }


@dataclass
class Header:
    """
    Represents the header section of a fixed-width transaction file.

    Attributes:
        name (Optional[str]): Name field.
        surname (Optional[str]): Surname field.
        patronymic (Optional[str]): Patronymic field.
        address (Optional[str]): Address field.
    """
    name: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    address: Optional[str] = None


@dataclass
class Footer:
    """
    Represents the footer section of a fixed-width transaction file.

    Attributes:
        total_counter (int): The total number of transactions in the file.
        control_sum (Decimal): The sum of all transaction amounts (currency does not matter).
    """
    total_counter: int
    control_sum: Decimal


@dataclass
class Transaction:
    """
    Represents a single transaction in a fixed-width transaction file.

    Attributes:
        transaction_id (Optional[int]): Unique identifier for the transaction.
        amount (Optional[Decimal]): The amount of the transaction.
        currency (Optional[str]): Three-letter currency code.
    """
    transaction_id: Optional[int] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None


@dataclass
class Content:
    """
    Represents the entire content of a fixed-width transaction file.

    Attributes:
        header (Header): The header section of the file.
        transactions (List[Transaction]): A list of all transactions in the file.
        footer (Footer): The footer section of the file.
    """
    header: Header
    transactions: List[Transaction]
    footer: Footer
