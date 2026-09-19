import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import os
import platform
import traceback

class LogfmtFormatter(logging.Formatter):
    """
    Formatter producing log lines in standard logfmt key=value syntax:
    time="YYYY-MM-DD HH:MM:SS" level=info logger=main msg="..." [key=value]
    """
    STANDARD_ATTRS = {
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
        'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
        'message', 'msg', 'name', 'pathname', 'process', 'processName',
        'relativeCreated', 'stack_info', 'thread', 'threadName', 'taskName'
    }

    LEVEL_MAP = {
        'DEBUG': 'debug',
        'INFO': 'info',
        'WARNING': 'warn',
        'ERROR': 'error',
        'CRITICAL': 'critical',
    }

    def __init__(self, datefmt="%Y-%m-%d %H:%M:%S"):
        super().__init__(datefmt=datefmt)

    @staticmethod
    def _format_value(value):
        if value is None:
            return '""'
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)

        s = str(value)
        # Escape backslashes, quotes, and whitespace control chars
        s = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{s}"'

    def format(self, record):
        time_str = self.formatTime(record, self.datefmt)
        level_str = self.LEVEL_MAP.get(record.levelname, record.levelname.lower())
        logger_name = record.name

        record.message = record.getMessage()
        msg_str = self._format_value(record.message)

        parts = [
            f'time="{time_str}"',
            f'level={level_str}',
            f'logger="{logger_name}"',
            f'msg={msg_str}'
        ]

        # Extra attributes if provided in record
        for key, val in record.__dict__.items():
            if key not in self.STANDARD_ATTRS and not key.startswith('_'):
                parts.append(f'{key}={self._format_value(val)}')

        # Single-line escaped traceback if exception is present
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            parts.append(f'error={self._format_value(record.exc_text)}')

        if record.stack_info:
            parts.append(f'stack={self._format_value(record.stack_info)}')

        return ' '.join(parts)


def setup_logging(log_path=None, log_level=logging.INFO, log_rotation=None):
    """
    Configure root logging with LogfmtFormatter.
    - log_path: directory or file path for logs. Defaults to 'log/automated-backup.log'.
    - log_rotation: dict containing rotation settings:
        - when: rotation frequency ('W0'-'W6', 'midnight', 'D', etc., default 'W0')
        - interval: rotation interval (default 1)
        - backup_count: number of rotated log files to retain (default 4)
        - max_size_mb: if provided and > 0, activates RotatingFileHandler with size limit in MB
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clean existing handlers to allow clean re-initialization
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    # Resolve log path
    if log_path:
        if log_path.endswith('.log'):
            log_file_path = os.path.abspath(log_path)
            log_directory = os.path.dirname(log_file_path)
        else:
            log_directory = os.path.abspath(log_path)
            log_file_path = os.path.join(log_directory, 'automated-backup.log')
    else:
        log_directory = 'log'
        log_file_path = os.path.join(log_directory, 'automated-backup.log')

    if log_directory:
        os.makedirs(log_directory, exist_ok=True)

    formatter = LogfmtFormatter()

    rotation_config = log_rotation if isinstance(log_rotation, dict) else {}
    backup_count = int(rotation_config.get('backup_count', 4))
    max_size_mb = rotation_config.get('max_size_mb')

    if max_size_mb is not None and float(max_size_mb) > 0:
        max_bytes = int(float(max_size_mb) * 1024 * 1024)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
    else:
        when = rotation_config.get('when', 'W0')
        interval = int(rotation_config.get('interval', 1))
        file_handler = TimedRotatingFileHandler(
            log_file_path,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding='utf-8'
        )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # StreamHandler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
