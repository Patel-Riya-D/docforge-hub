"""
logger.py

This module provides a centralized logging utility for the DocForge Hub system.

It configures and returns reusable logger instances with:
- Console logging for real-time debugging
- File logging for persistent records
- Standardized log formatting

Key Features:
- Environment-based log level configuration
- Prevents duplicate handlers
- Consistent logging across modules

This module ensures that all parts of the application use a unified
logging strategy for better observability and debugging.
"""
import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def get_logger(name: str):
    """
    Create and return a configured logger instance.

    This function initializes a logger with:
    - Console output (stdout)
    - File output (logs/app.log)
    - Standardized formatting

    Args:
        name (str): Name of the logger (typically module name).

    Returns:
        logging.Logger: Configured logger instance.

    Behavior:
        - Sets log level from environment variable (LOG_LEVEL)
        - Adds handlers only once (prevents duplicate logs)
        - Applies consistent formatting across all logs

    Log Format:
        [timestamp] [level] [logger_name] message

    Example:
        logger = get_logger("API")
        logger.info("Request received")

    Notes:
        - Log file is stored at: logs/app.log
        - Ensure 'logs/' directory exists before use
        - Suitable for both development and production environments
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(LOG_LEVEL)

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger