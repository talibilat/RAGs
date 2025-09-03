import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

class Logger:
    """
    Logger utility for handling application logging
    """
    def __init__(self, 
                 name="rag_app", 
                 log_level=logging.INFO, 
                 log_format=None, 
                 log_file=None, 
                 max_bytes=10485760, 
                 backup_count=5):
        """
        Initialize the logger
        
        Args:
            name (str): Logger name
            log_level (int): Logging level (default: INFO)
            log_format (str): Log format string (default: None - will use standard format)
            log_file (str): Path to log file (default: None - logs to console only)
            max_bytes (int): Maximum size in bytes for log file before rotation (default: 10MB)
            backup_count (int): Number of backup log files to keep (default: 5)
        """
        self.name = name
        self.log_level = log_level
        self.log_format = log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.handlers = []  # Remove any existing handlers
        
        # Create formatter
        formatter = logging.Formatter(self.log_format)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler if log_file is specified
        if self.log_file:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            # Create rotating file handler
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def get_logger(self):
        """
        Get the configured logger instance
        
        Returns:
            logging.Logger: Configured logger instance
        """
        return self.logger


def setup_logger(name, log_to_file=False, log_level=logging.INFO):
    """
    Set up and return a logger instance
    
    Args:
        name (str): Name of the logger
        log_to_file (bool): Whether to log to a file
        log_level (int): Logging level
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler and set level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if requested
    if log_to_file:
        # Determine project root (making sure we don't add duplicated 'backend' dir)
        if os.getcwd().endswith('backend'):
            log_dir = Path("logs")
        else:
            log_dir = Path("backend/logs")
        
        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        log_file = log_dir / f"{name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger 