"""
JSON Log Formatter Module

This module provides a custom logging formatter that converts log records 
into JSON format. It enables structured logging by transforming log entries 
into machine-readable JSON documents with enhanced metadata.

Key Features:
    - Converts log records to JSON format
    - Supports custom field mapping
    - Captures additional log record attributes
    - Provides UTC timestamp for log entries
"""

import json
import logging
import datetime as dt
from typing import override

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """
    A custom logging formatter that serializes log records to JSON.

    This formatter transforms Python logging records into JSON-formatted
    log entries, providing a structured and easily parseable log format.
    It allows for custom field mapping and captures both standard and
    custom log record attributes.

    Args:
        fmt_keys (dict[str, str], optional): A dictionary mapping custom
            output keys to log record attributes. Defaults to an empty dictionary.

    Attributes:
        fmt_keys (dict[str, str]): Mapping of output keys to log record attributes.

    Examples:
        >>> import logging
        >>> logger = logging.getLogger()
        >>> handler = logging.StreamHandler()
        >>> formatter = JsonFormatter(fmt_keys={
        ...     'log_level': 'levelname',
        ...     'service': 'name'
        ... })
        >>> handler.setFormatter(formatter)
        >>> logger.addHandler(handler)
        >>> logger.info('Test log message', extra={'service': 'user-service'})
        # Outputs a JSON-formatted log entry
    """

    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        """
        Initialize the JSON log formatter.

        Args:
            fmt_keys (dict[str, str], optional): Custom key mappings for
                log record attributes. Allows renaming or selecting specific
                attributes in the output JSON.
        """
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON string.

        Converts the log record to a dictionary and then serializes it
        to a JSON string. Handles both standard and custom log attributes.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: A JSON-formatted string representation of the log record.
        """
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        """
        Prepare a dictionary representation of the log record.

        Constructs a comprehensive dictionary of log record attributes,
        including:
            - Standard log message
            - UTC timestamp
            - Exception information (if applicable)
            - Stack trace (if applicable)
            - Custom log record attributes

        Args:
            record (logging.LogRecord): The log record to process.

        Returns:
            dict: A dictionary containing log record information.
        """
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message
