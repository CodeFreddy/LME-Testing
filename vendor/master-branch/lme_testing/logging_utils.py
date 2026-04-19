from __future__ import annotations

import logging
from pathlib import Path

from .storage import ensure_dir, timestamp_slug


_CONFIGURED_LOG_PATH: str | None = None


def configure_logging(command_name: str, log_root: Path) -> Path:
    # ??????? + ?????????????????
    global _CONFIGURED_LOG_PATH

    ensure_dir(log_root)
    log_path = log_root / f"{command_name}_{timestamp_slug()}.log"
    resolved_path = str(log_path.resolve())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if _CONFIGURED_LOG_PATH == resolved_path:
        return log_path

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    _CONFIGURED_LOG_PATH = resolved_path
    logging.getLogger(__name__).info("Logging initialized: %s", resolved_path)
    return log_path
