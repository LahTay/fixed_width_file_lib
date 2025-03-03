from dataclasses import dataclass
from typing import List


@dataclass
class Transaction:
    transaction_id: int
    amount: float
    currency: str


@dataclass
class Content:
    name: str
    surname: str
    patronymic: str
    address: str
    transactions: List[Transaction]
    total_counter: int
    control_sum: int


class FileContent:
    def __init__(self):
        self.contents: List[Content] = []

    def add_content(self):
        pass

    def delete_content(self):
        pass

    def get_content(self):
        pass


