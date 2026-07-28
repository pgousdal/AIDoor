import logging
import sys


def setup_logging(log_level: str = "INFO", log_file: str = "") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    handler: logging.Handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger("aidoor")
    root.setLevel(level)
    root.addHandler(handler)
