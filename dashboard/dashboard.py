import streamlit as st

class Dashboard:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def update(self, trader_stats, model_stats):
        st.title("Dashboard Bot Trading")
        st.write("Trader stats:", trader_stats)
        st.write("Model stats:", model_stats)
