from fixed_width_lib.logger import Logger

class File:
    def __init__(self, filename, mode, logger_name, handlers_list, formatting):
        self.filename = filename
        self.mode = mode
        self.file = None
        self.logger = Logger(logger_name, handlers_list, formatting)

        self._set_logging(logger_name)

    def open(self):
        pass

    def is_open(self):
        pass

    def close(self):
        pass

    def delete_file(self):
        pass

    def _set_logging(self, logger_name):
        if self._logger:
            return
        File._logger = logging.getLogger("FileOperations")

        self.logger = logging.getLogger(f"FileLogger-{os.path.basename(filename)}")
        self.logger.setLevel(logging.INFO)

    def _set_logging_level(self, level):


    def __enter__(self):
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self):
        if self.file:
            self.file.close()

