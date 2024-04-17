import logging


class MyLogger:
    def __init__(self, level=logging.INFO, file_name=None):
        self.logger = logging.getLogger()
        self.logger.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s"
        )

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Add file handler if file_name is provided
        if file_name:
            file_handler = logging.FileHandler(file_name)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger
