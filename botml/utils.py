import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import yaml


def load_config(path: str | None = None) -> dict:
    """Return configuration dictionary.

    Parameters
    ----------
    path : str, optional
        Explicit path to a YAML configuration file. If omitted the function
        first checks the ``BOTML_CONFIG`` environment variable and finally
        falls back to ``config.yaml`` located at the project root.
    """

    if path is None:
        path = os.getenv("BOTML_CONFIG")

    config_path = Path(path) if path else Path(__file__).resolve().parents[1] / "config.yaml"
    with open(config_path, "r") as fh:
        return yaml.safe_load(fh)


def setup_logging(config, name: str | None = None) -> logging.Logger:
    """Configure and return a logger using the supplied configuration.

    Parameters
    ----------
    config : dict
        Configuration dictionary typically loaded via ``load_config``.
    name : str, optional
        Name of the logger to create. If omitted the root logger is used.
    """

    level_name = config.get("log_level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file = config.get("log_file", "bot.log")
    rotate = config.get("log_rotation", False)
    max_bytes = int(config.get("log_max_bytes", 1_048_576))
    backup_count = int(config.get("log_backup_count", 3))
    log_format = config.get("log_format", "text").lower()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    root_logger = logging.getLogger()
    if not getattr(root_logger, "_botml_initialized", False):
        root_logger.handlers.clear()

        if log_format == "json":
            class JsonFormatter(logging.Formatter):
                def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
                    data = {
                        "time": self.formatTime(record, self.datefmt),
                        "level": record.levelname,
                        "name": record.name,
                        "message": record.getMessage(),
                    }
                    return json.dumps(data)

            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")

        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root_logger.addHandler(console)

        if rotate:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.setLevel(level)
        root_logger._botml_initialized = True

    logger.propagate = True
    return logger
