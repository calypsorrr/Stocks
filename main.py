"""Command-line helper to rank stocks and preview notifications."""
from __future__ import annotations

import argparse
from typing import Iterable

from tabulate import tabulate

from notifier import format_summary, send_notification
from stock_data import DEFAULT_TICKERS


def display_table(tickers: Iterable[str], days: int, top_n: int) -> None:
    message, summary = format_summary(tickers, days, top_n)
    headers = ["Rank", "Ticker", "Start", "End", "% Change"]
    rows = [
        (idx + 1, row.ticker, row.start_price, row.end_price, f"{row.pct_change}%")
        for idx, row in enumerate(summary.itertuples())
    ]
    print(tabulate(rows, headers=headers, tablefmt="github"))
    return message


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank stocks by recent performance.")
    parser.add_argument("--days", type=int, default=30, help="Lookback window in days")
    parser.add_argument("--top", type=int, default=10, help="How many tickers to display")
    parser.add_argument(
        "--tickers",
        nargs="*",
        default=DEFAULT_TICKERS,
        help="Universe of tickers to evaluate (space separated)",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send a desktop notification summarizing the top results.",
    )
    args = parser.parse_args()

    message = display_table(args.tickers, args.days, args.top)
    if args.notify:
        send_notification("Top movers update", message)


if __name__ == "__main__":
    main()
