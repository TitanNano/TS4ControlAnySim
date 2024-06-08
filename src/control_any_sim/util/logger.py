"""Logger utility."""

from __future__ import annotations

from pathlib import Path


def get_logfile_name() -> str:
    """Get the absolute path to the log file."""
    dir_name: Path = Path(__file__).resolve().parent
    log_dir = dir_name / ".." / ".." / ".."

    return str(log_dir / "debug.log")


class Logger:
    """Static logger class to write to log file."""

    PRODUCTION = False

    handler = Path(get_logfile_name()).open("a")  # noqa: SIM115

    @classmethod
    def log(cls: type[Logger], message: str) -> None:
        """Write generic message to log."""
        if cls.PRODUCTION:
            return

        cls.handler.write(message + "\n")
        cls.handler.flush()

    @classmethod
    def error(cls: type[Logger], message: str) -> None:
        """Write error message to log."""
        cls.handler.write("ERROR: " + message + "\n")
        cls.handler.flush()
