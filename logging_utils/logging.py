import logging

def setup_logging(config):
    level = config.get("log_level", "INFO")
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(config.get("log_file", "bot.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("Bot")
