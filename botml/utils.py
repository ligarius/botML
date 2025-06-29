import logging
from pathlib import Path
import yaml


def load_config():
    """Load configuration from config.yaml located at the project root."""
    config_path = Path(__file__).resolve().parents[1] / 'config.yaml'
    with open(config_path, 'r') as fh:
        return yaml.safe_load(fh)


def setup_logging(config):
    """Configure logging based on a configuration dictionary."""
    level_name = config.get('log_level', 'INFO').upper()
    log_file = config.get('log_file', 'bot.log')
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(),
                  logging.FileHandler(log_file, encoding='utf-8')]
    )
