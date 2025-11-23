"""Send desktop notifications about the current top performers."""
from __future__ import annotations

import argparse
from typing import Iterable

from plyer import notification

from stock_data import DEFAULT_TICKERS, fetch_history, rank_top_performers


def format_summary(tickers: Iterable[str], days: int, top_n: int) -> str:
    closes = fetch_history(tickers, days)
    summary = rank_top_performers(tickers, days, top_n)
    lines = [f"{row.ticker}: {row.pct_change}%" for row in summary.itertuples()]
    return "\n".join(lines), summary


def send_notification(title: str, message: str) -> None:
    notification.notify(title=title, message=message, timeout=10)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a notification with top stock movers.")
    parser.add_argument("--tickers", nargs="*", default=DEFAULT_TICKERS, help="Universe of tickers to scan")
    parser.add_argument("--days", type=int, default=30, help="Lookback window for returns")
    parser.add_argument("--top", type=int, default=5, help="Number of tickers to include in the alert")
    args = parser.parse_args()

    message, _ = format_summary(args.tickers, args.days, args.top)
    send_notification("Top movers update", message)


if __name__ == "__main__":
    main()
