import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Get the project root directory (three levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_dir_path = os.path.join(project_root, LOG_DIR)
os.makedirs(log_dir_path, exist_ok=True)

log_file_path = os.path.join(log_dir_path, LOG_FILE)


def get_logger(name: str = "FraudShieldAI") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger  # prevent duplicate logs

    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = get_logger()