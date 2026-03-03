import logging
import os
import sys
from datetime import datetime
from core.infrastructure.config_manager import config

class LogManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        self.logger = logging.getLogger("LuminaAI")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(module)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        if config.get("system.developer_mode", False):
            console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 2. File Handler
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"lumina_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8-sig')
        file_handler.setLevel(logging.DEBUG) # Always log debug to file
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

# Global logger instance
logger = LogManager().get_logger()
