"""Utilities to fetch and rank stocks by recent performance."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List

import pandas as pd
import yfinance as yf


DEFAULT_TICKERS: List[str] = [
    # A compact, high-liquidity universe across sectors
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "TSLA",
    "JPM",
    "V",
    "PG",
    "UNH",
    "MA",
    "HD",
    "XOM",
    "CVX",
    "BAC",
    "KO",
    "PEP",
    "DIS",
    "CSCO",
    "ADBE",
    "CRM",
    "NFLX",
    "INTC",
    "ORCL",
    "WMT",
    "COST",
    "PYPL",
    "PFE",
    "ABBV",
    "MCD",
    "NKE",
    "T",
    "VZ",
    "UPS",
    "BA",
    "AMD",
    "IBM",
    "QCOM",
    "DHR",
    "AVGO",
    "TXN",
    "SBUX",
    "HON",
    "LIN",
    "LOW",
    "MDT",
    "BMY",
    "MS",
    "GS",
]


def fetch_history(tickers: Iterable[str], days: int = 30) -> pd.DataFrame:
    """Return recent adjusted close prices for the provided tickers.

    The function requests a little more data than the requested window to avoid
    empty results when markets are closed. The output is a DataFrame indexed by
    date with tickers as columns and contains adjusted close values.
    """

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days + 5)
    data = yf.download(
        list(tickers),
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        progress=False,
        group_by="column",
        auto_adjust=True,
    )
    # When only one ticker is present, yfinance returns a Series
    if isinstance(data, pd.DataFrame) and ("Adj Close" in data.columns):
        closes = data["Adj Close"]
    else:  # Single ticker case
        closes = data

    closes = closes.dropna(axis=1, how="all").dropna()
    return closes.tail(days)


def rank_top_performers(
    tickers: Iterable[str] = DEFAULT_TICKERS, days: int = 30, top_n: int = 10
) -> pd.DataFrame:
    """Compute top performing tickers by percentage change over the window."""

    closes = fetch_history(tickers, days)
    if closes.empty:
        raise ValueError("No price data returned; check tickers or network connectivity.")

    pct_change = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]
    summary = pd.DataFrame(
        {
            "ticker": pct_change.index,
            "start_price": closes.iloc[0].round(2),
            "end_price": closes.iloc[-1].round(2),
            "pct_change": (pct_change * 100).round(2),
        }
    )
    summary = summary.sort_values("pct_change", ascending=False).head(top_n)
    return summary.reset_index(drop=True)


def merge_top_history(summary: pd.DataFrame, closes: pd.DataFrame) -> pd.DataFrame:
    """Attach price trajectories to the summary for the selected tickers."""

    tickers = summary["ticker"].tolist()
    filtered = closes[tickers]
    melted = filtered.reset_index().melt(id_vars="Date", var_name="ticker", value_name="price")
    return melted
