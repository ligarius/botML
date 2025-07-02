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

    def update(self, trader_stats, model_stats, variants=None):
        """Render the latest trader and model statistics along with variants."""
        # Avoid warning when Streamlit is not running.
        ctx = get_script_run_ctx()
        if ctx is None:
            self.logger.debug("Streamlit context missing; dashboard update skipped")
            return

        st.title("Dashboard Bot Trading")
        st.write("Trader stats:", trader_stats)
        st.write("Model stats:", model_stats)
        if variants:
            st.subheader("Variantes activas")
            table = [
                {
                    "gen": v.generation,
                    **v.params,
                    **(v.history[-1] if v.history else {}),
                }
                for v in variants
            ]
            st.table(table)
