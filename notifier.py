"""Send desktop notifications about the current top performers."""
from __future__ import annotations

import argparse
import logging
from typing import Iterable

import pandas as pd
from plyer import notification

from stock_data import DEFAULT_TICKERS, fetch_history, rank_top_performers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_summary(tickers: Iterable[str], days: int, top_n: int) -> tuple[str, pd.DataFrame]:
    """Format a summary message and return both the message and summary DataFrame.
    
    Args:
        tickers: List of stock ticker symbols to analyze
        days: Number of days to look back
        top_n: Number of top performers to include
        
    Returns:
        Tuple of (formatted message string, summary DataFrame)
    """
    closes = fetch_history(tickers, days)
    summary = rank_top_performers(tickers, days, top_n)
    lines = [f"{row.ticker}: {row.pct_change}%" for row in summary.itertuples()]
    return "\n".join(lines), summary


def send_notification(title: str, message: str) -> None:
    """Send a desktop notification.
    
    Args:
        title: Notification title
        message: Notification message body
        
    Raises:
        Exception: If notification fails to send
    """
    try:
        notification.notify(title=title, message=message, timeout=10)
        logger.info("Notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise


def main() -> None:
    """Main entry point for the notification script."""
    parser = argparse.ArgumentParser(description="Send a notification with top stock movers.")
    parser.add_argument("--tickers", nargs="*", default=DEFAULT_TICKERS, help="Universe of tickers to scan")
    parser.add_argument("--days", type=int, default=30, help="Lookback window for returns")
    parser.add_argument("--top", type=int, default=5, help="Number of tickers to include in the alert")
    args = parser.parse_args()

    # Validate arguments
    if args.days <= 0:
        logger.error("--days must be a positive integer")
        return
    if args.top <= 0:
        logger.error("--top must be a positive integer")
        return

    try:
        message, _ = format_summary(args.tickers, args.days, args.top)
        send_notification("Top movers update", message)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise


if __name__ == "__main__":
    main()
