"""
Logging configuration for GitHub Skill Indexer
"""
import logging
import os
from datetime import datetime
from config import Config


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Setup logger with file and console handlers

    Args:
        name: Logger name (usually __name__)
        log_file: Optional log file name (without path)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(Config.LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        file_path = os.path.join(Config.LOG_DIR, log_file)
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create logger

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
