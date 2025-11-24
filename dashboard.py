"""Streamlit dashboard for ranking and visualizing top stocks."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from stock_data import DEFAULT_TICKERS, fetch_history, rank_top_performers

st.set_page_config(page_title="Top Stocks Scout", layout="wide")
st.title("📈 Top 10 Movers (Last Month)")
st.write(
    "Use the controls to rank your favorite tickers by their price change over a "
    "custom window, then drill into daily trajectories. Data refreshes live from "
    "Yahoo Finance via `yfinance`."
)

with st.sidebar:
    st.header("Universe & Settings")
    selected = st.text_area(
        "Tickers (comma-separated)",
        ", ".join(DEFAULT_TICKERS),
        help="Paste or type any symbols supported by Yahoo Finance.",
    )
    days = st.slider("Lookback window (days)", min_value=10, max_value=90, value=30)
    top_n = st.slider("How many to show?", min_value=5, max_value=25, value=10)
    tickers = [t.strip().upper() for t in selected.split(",") if t.strip()]

@st.cache_data(show_spinner=False)
def _load_data(tickers: list[str], days: int) -> pd.DataFrame:
    return fetch_history(tickers, days)

try:
    prices = _load_data(tickers, days)
    summary = rank_top_performers(tickers, days, top_n)
    st.success(f"Retrieved {len(prices.columns)} tickers over {len(prices)} trading days.")
except Exception as exc:  # noqa: BLE001 - surface the error to the user
    st.error(f"Failed to load data: {exc}")
    st.stop()

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Leaderboard")
    st.dataframe(summary, hide_index=True, use_container_width=True)
    st.caption("Percent change is calculated from the first to last closing price in the window.")

with col2:
    st.subheader("Trajectories")
    prices_with_dates = prices.reset_index()
    if "Date" not in prices_with_dates.columns:
        index_col = prices_with_dates.columns[0]
        prices_with_dates = prices_with_dates.rename(columns={index_col: "Date"})
    melted = prices_with_dates.melt(id_vars="Date", var_name="ticker", value_name="price")
    top_tickers = summary["ticker"].tolist()
    filtered = melted[melted["ticker"].isin(top_tickers)]
    fig = px.line(
        filtered,
        x="Date",
        y="price",
        color="ticker",
        title="Adjusted Close by Day",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    **Tip:** schedule the companion notifier script to run daily so you get a desktop alert
    whenever the leaderboard changes.
    """
)
