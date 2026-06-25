"""
Logger module for crawlergo
"""
import logging
import sys

# Default log level
DEFAULT_LEVEL = "WARNING"

# Log level mapping
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class Logger:
    """Logger wrapper around Python's logging module"""

    _instance = None

    def __new__(cls, level: str = DEFAULT_LEVEL):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger(level)
        return cls._instance

    def _init_logger(self, level: str):
        self.logger = logging.getLogger("crawlergo")
        self.logger.setLevel(LOG_LEVEL_MAP.get(level.upper(), logging.WARNING))

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(LOG_LEVEL_MAP.get(level.upper(), logging.WARNING))

        # Formatter
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def set_level(self, level: str):
        """Set log level"""
        self.logger.setLevel(LOG_LEVEL_MAP.get(level.upper(), logging.WARNING))
        for handler in self.logger.handlers:
            handler.setLevel(LOG_LEVEL_MAP.get(level.upper(), logging.WARNING))

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


# Global logger instance
Logger = Logger()


def get_logger():
    """Get the global logger instance"""
    return Logger
