import sys
from src.utils.logging import logger


def error_message_detail(error: Exception, error_detail: sys) -> str:
    try:
        _, _, exc_tb = error_detail.exc_info()

        if exc_tb is None:
            return f"Error occurred: {str(error)}"

        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno

        error_message = (
            f"Error occurred in python script: [{file_name}] "
            f"at line number [{line_number}]: {str(error)}"
        )

        logger.error(error_message)

        return error_message

    except Exception as e:
        fallback_msg = f"Failed to parse error detail: {str(e)}"
        logger.error(fallback_msg)
        return fallback_msg


class FraudShieldException(Exception):
    def __init__(self, error_message: str, error_detail: sys):
        super().__init__(error_message)
        self.error_message = error_message_detail(error_message, error_detail)

    def __str__(self):
        return self.error_message