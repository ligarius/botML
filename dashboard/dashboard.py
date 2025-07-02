"""Simple Streamlit UI for monitoring bot metrics."""

import streamlit as st

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:  # streamlit < 1.18 compatibility
    def get_script_run_ctx() -> object:
        return None


class Dashboard:
    """Render metrics and charts in a Streamlit dashboard."""

    def __init__(self, config, logger):
        """Create the dashboard manager."""

        self.config = config
        self.logger = logger

    def update(self, trader_stats, model_stats):
        """Render the latest trader and model statistics."""
        # Avoid warning when Streamlit is not running.
        ctx = get_script_run_ctx()
        if ctx is None:
            self.logger.debug("Streamlit context missing; dashboard update skipped")
            return

        st.title("Dashboard Bot Trading")
        st.write("Trader stats:", trader_stats)
        st.write("Model stats:", model_stats)
