import time

class Watchdog:
    def __init__(self, config, logger):
        self.last_heartbeat = time.time()
        self.timeout = config.get("watchdog_timeout", 120)
        self.logger = logger

    def heartbeat(self):
        now = time.time()
        if now - self.last_heartbeat > self.timeout:
            self.logger.error("Watchdog: reiniciando proceso...")
        self.last_heartbeat = now
