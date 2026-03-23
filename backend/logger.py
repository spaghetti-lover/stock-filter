import json
import logging
import sys
import traceback
from datetime import datetime, timezone


def _filter_traceback_exception(te: traceback.TracebackException) -> None:
    _SKIP = (".venv", "site-packages")
    te.stack[:] = [
        frame for frame in te.stack
        if not any(skip in frame.filename for skip in _SKIP)
    ]
    if te.__cause__ is not None:
        _filter_traceback_exception(te.__cause__)
    if te.__context__ is not None:
        _filter_traceback_exception(te.__context__)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        obj: dict = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            te = traceback.TracebackException(*record.exc_info)
            _filter_traceback_exception(te)
            frames = [
                {"file": f.filename, "line": f.lineno, "in": f.name}
                for f in te.stack
            ]
            obj["exception"] = {
                "type": te.exc_type.__name__ if te.exc_type else "Unknown",
                "message": str(te),
                "traceback": frames,
            }
            full_te = traceback.TracebackException(*record.exc_info)
            obj["full_log"] = (
                f"{obj['time']} | {obj['level']} | {obj['logger']} | {obj['message']}\n"
                + "".join(full_te.format()).rstrip()
            )
        return json.dumps(obj, indent=2)


class _JsonArrayHandler(logging.FileHandler):
    """Writes log records as a JSON array: opens with '[', separates entries with ','."""

    def __init__(self, filename: str) -> None:
        super().__init__(filename, mode="w")
        self._first = True

    def _open(self):
        stream = super()._open()
        stream.write("[\n")
        stream.flush()
        self._first = True
        return stream

    def emit(self, record: logging.LogRecord) -> None:
        if not self._first:
            self.stream.write(",\n")
        self._first = False
        super().emit(record)

    def close(self) -> None:
        if self.stream:
            self.stream.write("\n]\n")
            self.stream.flush()
        super().close()


class _LatestErrorHandler(logging.FileHandler):
    """Overwrites the file with only the most recent error."""

    def __init__(self, filename: str) -> None:
        super().__init__(filename, mode="w")

    def emit(self, record: logging.LogRecord) -> None:
        self.stream.seek(0)
        self.stream.truncate()
        super().emit(record)
        self.stream.flush()


def setup_logging(
    level: int = logging.INFO,
    error_log_file: str = "errors.log",
    latest_only: bool = False,
) -> None:
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    plain_formatter = logging.Formatter(fmt, datefmt=datefmt)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(plain_formatter)

    error_handler = _LatestErrorHandler(error_log_file) if latest_only else _JsonArrayHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(stdout_handler)
    root.addHandler(error_handler)

    logging.getLogger("vnstock").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
