from fixed_width_lib.file import File
from typing import List
from logging import Handler


class Reader(File):

    def __init__(self, filepath: str, mode: str, logger_name: str, handlers_list: List[Handler], formatting: str):
        super().__init__(filepath, mode, logger_name, handlers_list, formatting)

    def read(self):
        pass

    def get_header_fields(self, fields: List[str]):
        pass

    def get_transaction(self, idx: int):
        pass


    def get_footer_field(self, fields: List[str]):
        pass
