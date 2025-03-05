from fixed_width_lib.file import File
from typing import List, Optional
from logging import Handler
from decimal import Decimal


class Writer(File):
    def __init__(self, filepath: str, mode: str, logger_name: str, handlers_list: List[Handler], formatting: str):
        super().__init__(filepath, mode, logger_name, handlers_list, formatting)
        self.changed_header_values = {}
        self.new_transactions = []
        self.changed_transactions = {}

    def write(self):
        """
        This functions checks all the added/changed values and commits them to a file
        :return:
        """
        pass

    def set_header(self, name, surname, patronymic, address):
        """
        This is a function that will set the header anew
        :param name:
        :param surname:
        :param patronymic:
        :param address:
        :return:
        """
        pass

    def change_header(self, *,
                      name: Optional[str] = None,
                      surname: Optional[str] = None,
                      patronymic: Optional[str] = None,
                      address: Optional[str] = None):
        """
        This is a function that changes header, only the required parts
        :param name:
        :param surname:
        :param patronymic:
        :param address:
        :return:
        """
        pass

    def add_transaction(self, amount: Decimal, currency: str):
        """
        This function adds a new transaction
        :param amount:
        :param currency:
        :return:
        """
        pass

    def change_transaction(self, idx: int, *,
                           amount: Optional[Decimal] = None,
                           currency: Optional[str] = None):
        """
        This function changes and existing transaction based on its counter (idx)
        :param idx:
        :param amount:
        :param currency:
        :return:
        """
        pass


