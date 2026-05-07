"""
Structured Logging Configuration
Provides JSON-formatted logs with context for production monitoring
"""

import logging
import sys
from pathlib import Path
from typing import Any

try:
    from pythonjsonlogger.jsonlogger import JsonFormatter
except ImportError:
    # Fallback for older versions
    from pythonjsonlogger import jsonlogger
    JsonFormatter = jsonlogger.JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    """
    Custom JSON formatter with additional context fields
    """

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        """
        Add custom fields to log records
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        
        # Add process and thread info
        log_record["process_id"] = record.process
        log_record["thread_id"] = record.thread
        
        # Include exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored formatter for console output (development)
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Color the level name
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
    use_json: bool = True,
    use_colors: bool = True,
) -> None:
    """
    Configure application-wide logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        use_json: Use JSON formatting for file logs
        use_colors: Use colored output for console (development only)
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if use_colors and sys.stdout.isatty():
        # Colored output for development
        console_format = ColoredConsoleFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Plain text for production/CI
        console_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File Handler (if log file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        if use_json:
            # JSON formatting for structured logs
            json_format = CustomJsonFormatter(
                fmt="%(timestamp)s %(level)s %(name)s %(message)s"
            )
        else:
            # Plain text formatting
            json_format = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        file_handler.setFormatter(json_format)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log initial message
    root_logger.info(
        f"Logging initialized: level={log_level}, file={log_file}, json={use_json}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter for adding context to all log messages
    """
    
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """
        Add extra context to log messages
        """
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_context_logger(name: str, **context: Any) -> LoggerAdapter:
    """
    Get a logger with additional context fields
    
    Args:
        name: Logger name
        **context: Additional context fields to include in all logs
    
    Returns:
        Logger adapter with context
    
    Example:
        >>> logger = get_context_logger(__name__, user_id="123", request_id="abc")
        >>> logger.info("User action performed")
        # Logs will include user_id and request_id fields
    """
    base_logger = get_logger(name)
    return LoggerAdapter(base_logger, context)
