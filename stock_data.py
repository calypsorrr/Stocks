"""Utilities to fetch and rank stocks by recent performance."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Iterable

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DEFAULT_TICKERS: list[str] = [
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

    Args:
        tickers: Iterable of stock ticker symbols
        days: Number of days of history to retrieve (default: 30)

    Returns:
        DataFrame with dates as index and tickers as columns, containing adjusted close prices

    Raises:
        ValueError: If no valid tickers are provided or if days is invalid
        Exception: If data fetching fails
    """
    ticker_list = list(tickers)
    if not ticker_list:
        raise ValueError("At least one ticker must be provided")
    if days <= 0:
        raise ValueError("Days must be a positive integer")

    # Validate and normalize ticker symbols
    ticker_list = [t.strip().upper() for t in ticker_list if t.strip()]
    if not ticker_list:
        raise ValueError("No valid ticker symbols provided")

    logger.info(f"Fetching data for {len(ticker_list)} tickers over {days} days")

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days + 5)
    
    try:
        data = yf.download(
            ticker_list,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
            group_by="column",
            auto_adjust=True,
        )
    except Exception as e:
        logger.error(f"Failed to download data from yfinance: {e}")
        raise RuntimeError(f"Failed to fetch stock data: {e}") from e

    # When only one ticker is present, yfinance returns a Series
    if isinstance(data, pd.DataFrame) and ("Adj Close" in data.columns):
        closes = data["Adj Close"]
    else:  # Single ticker case
        closes = data

    if closes.empty:
        raise ValueError("No price data returned; check tickers or network connectivity.")

    closes = closes.dropna(axis=1, how="all").dropna()
    
    # Log which tickers were successfully retrieved
    retrieved_tickers = list(closes.columns)
    if len(retrieved_tickers) < len(ticker_list):
        missing = set(ticker_list) - set(retrieved_tickers)
        logger.warning(f"Failed to retrieve data for tickers: {missing}")
    
    closes.index.name = "Date"
    result = closes.tail(days)
    logger.info(f"Successfully retrieved data for {len(result.columns)} tickers")
    return result


def rank_top_performers(
    tickers: Iterable[str] = DEFAULT_TICKERS, days: int = 30, top_n: int = 10
) -> pd.DataFrame:
    """Compute top performing tickers by percentage change over the window.

    Args:
        tickers: Iterable of stock ticker symbols to analyze (default: DEFAULT_TICKERS)
        days: Number of days to look back (default: 30)
        top_n: Number of top performers to return (default: 10)

    Returns:
        DataFrame with columns: ticker, start_price, end_price, pct_change
        Sorted by pct_change in descending order, limited to top_n rows

    Raises:
        ValueError: If no data is available or if top_n is invalid
    """
    if top_n <= 0:
        raise ValueError("top_n must be a positive integer")

    closes = fetch_history(tickers, days)
    if closes.empty:
        raise ValueError("No price data returned; check tickers or network connectivity.")

    # Calculate percentage change from first to last available price
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
    logger.info(f"Ranked top {len(summary)} performers")
    return summary.reset_index(drop=True)


def merge_top_history(summary: pd.DataFrame, closes: pd.DataFrame) -> pd.DataFrame:
    """Attach price trajectories to the summary for the selected tickers.
    
    This function filters the price history DataFrame to include only the tickers
    from the summary and reshapes it into a long format suitable for plotting.

    Args:
        summary: DataFrame with a 'ticker' column containing ticker symbols
        closes: DataFrame with dates as index and tickers as columns

    Returns:
        DataFrame in long format with columns: Date, ticker, price
    """
    tickers = summary["ticker"].tolist()
    filtered = closes[tickers]
    melted = filtered.reset_index().melt(id_vars="Date", var_name="ticker", value_name="price")
    return melted
