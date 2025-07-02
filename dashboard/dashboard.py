"""Simple Streamlit UI for monitoring bot metrics."""

import streamlit as st


class Dashboard:
    """Render metrics and charts in a Streamlit dashboard."""

    def __init__(self, config, logger):
        """Create the dashboard manager."""

        self.config = config
        self.logger = logger

    def update(self, trader_stats, model_stats):
        """Render the latest trader and model statistics."""

        st.title("Dashboard Bot Trading")
        st.write("Trader stats:", trader_stats)
        st.write("Model stats:", model_stats)
