from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

LINESIZE = 120
MAX_TRANSACTIONS = 20000
class HeaderFields:
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
    name: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    address: Optional[str] = None


@dataclass
class Footer:
    total_counter: int
    control_sum: Decimal


@dataclass
class Transaction:
    transaction_id: Optional[int] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None


@dataclass
class Content:
    header: Header
    transactions: List[Transaction]
    footer: Footer



