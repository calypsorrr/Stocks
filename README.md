# Stocks Dashboard & Notifier

This project ranks a universe of tickers by their recent performance, shows the top movers in a Streamlit dashboard, and can send a desktop notification summarizing the leaders.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Streamlit dashboard

```bash
streamlit run dashboard.py
```

* Adjust the tickers, lookback window, and number of winners from the sidebar.
* The main panel lists the leaderboard and plots the daily trajectories for the current top symbols.

## Command-line ranking & notification

Print a table of the top performers and optionally trigger a desktop notification:

```bash
python main.py --days 30 --top 10 --notify
```

To monitor a custom universe:

```bash
python main.py --tickers AAPL MSFT NVDA AMD --notify
```

You can schedule `python notifier.py --top 5` in a cron job or Task Scheduler to get a quick daily summary.
