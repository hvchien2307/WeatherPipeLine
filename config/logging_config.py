import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR/"app.log"


def setup_logging(
        file_level :int = logging.INFO,
        console_level :int = logging.WARNING
) -> None:
    """Configure root logging for whole pipeline

        Call this exactly once, at the entry point (main.py),
        or inside the module's own `if __name__ == "__main__"` block
        when testing that module stand alone
        """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(min(file_level, console_level))
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)
