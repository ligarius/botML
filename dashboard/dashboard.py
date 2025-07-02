"""Streamlit dashboard displaying metrics saved by the bot."""

import streamlit as st

from modules.analytics import load_metrics


st.set_page_config(page_title="Bot Dashboard")


def main() -> None:
    """Render dashboard widgets from ``results.json``."""
    st.title("Dashboard Bot Trading")
    try:
        data = load_metrics("results.json")
    except FileNotFoundError:
        st.error("results.json not found. Run the bot first.")
        return

    st.subheader("Trader stats")
    st.json(data.get("trader", {}))

    st.subheader("Model stats")
    st.json(data.get("model", {}))

    variants = data.get("variants")
    if variants:
        st.subheader("Variantes activas")
        st.table(variants)


if __name__ == "__main__":
    main()
