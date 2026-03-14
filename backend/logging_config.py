"""
Logging Configuration for SBN ChatAgent
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """
    Configure application-wide logging with rotating file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    # Create logs directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename with date
    log_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"chatagent_{log_date}.log")
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation (10MB max, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel("INFO")
    logging.getLogger("httpx").setLevel("WARNING")
    logging.getLogger("chromadb").setLevel("WARNING")
    
    logging.info(f"Logging configured. Log file: {log_file}")
