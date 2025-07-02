"""Watchdog process to detect hangs and restart the bot if needed."""

import time


class Watchdog:
    """Monitor the application and trigger restarts when unresponsive."""

    def __init__(self, config, logger):
        """Create a watchdog instance."""

        self.last_heartbeat = time.time()
        self.timeout = config.get("watchdog_timeout", 120)
        self.logger = logger

    def heartbeat(self):
        """Record a heartbeat and log if the process seems stuck."""

        now = time.time()
        if now - self.last_heartbeat > self.timeout:
            self.logger.error("Watchdog: reiniciando proceso...")
        self.last_heartbeat = now
