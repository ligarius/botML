import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import yaml


def load_config():
    """Load configuration from config.yaml located at the project root."""
    config_path = Path(__file__).resolve().parents[1] / 'config.yaml'
    with open(config_path, 'r') as fh:
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
    logger.handlers.clear()

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
    logger.addHandler(console)

    if rotate:
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    else:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
