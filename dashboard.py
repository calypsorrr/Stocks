"""Streamlit dashboard for ranking and visualizing top stocks."""
from __future__ import annotations

import logging

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from stock_data import DEFAULT_TICKERS, fetch_history, rank_top_performers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Top Stocks Scout",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stock-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #e0e0e0;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .stock-card:hover {
        border-color: #1f77b4;
        background-color: #f0f8ff;
    }
    .stock-card.selected {
        border-color: #1f77b4;
        background-color: #e6f3ff;
    }
    .positive {
        color: #00cc00;
        font-weight: bold;
    }
    .negative {
        color: #ff3333;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Top Stock Performers")
st.markdown("**Discover the best performing stocks right now. Click any stock to see its growth chart.**")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    days = st.slider(
        "Lookback Period (days)",
        min_value=7,
        max_value=90,
        value=30,
        help="How many days to look back for performance calculation"
    )
    
    top_n = st.slider(
        "Number of Top Stocks",
        min_value=5,
        max_value=20,
        value=10,
        help="How many top performers to display"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Stock Universe")
    selected = st.text_area(
        "Tickers (comma-separated)",
        ", ".join(DEFAULT_TICKERS),
        help="Enter stock ticker symbols separated by commas",
        height=150
    )
    
    tickers = [t.strip().upper() for t in selected.split(",") if t.strip()]
    
    if not tickers:
        st.warning("⚠️ Please enter at least one ticker symbol.")
        st.stop()
    
    st.markdown("---")
    st.caption(f"📅 Data updates automatically from Yahoo Finance")

# Cache data fetching
@st.cache_data(ttl=3600, show_spinner=True)  # Cache for 1 hour
def _load_data(tickers: list[str], days: int) -> pd.DataFrame:
    """Load stock data with caching."""
    return fetch_history(tickers, days)

# Load and process data
try:
    with st.spinner("🔄 Fetching latest stock data..."):
        prices = _load_data(tickers, days)
        summary = rank_top_performers(tickers, days, top_n)
    
    # Handle MultiIndex columns if present (yfinance sometimes returns MultiIndex)
    if isinstance(prices.columns, pd.MultiIndex):
        # Flatten MultiIndex columns - take the last level (ticker name)
        prices.columns = [col[-1] if isinstance(col, tuple) else col for col in prices.columns]
    
    retrieved_count = len(prices.columns)
    requested_count = len(tickers)
    
    if retrieved_count < requested_count:
        st.warning(
            f"⚠️ Retrieved data for {retrieved_count} of {requested_count} tickers. "
            "Some tickers may be invalid or unavailable."
        )
    else:
        st.success(f"✅ Successfully loaded {retrieved_count} stocks")
        
except ValueError as exc:
    st.error(f"❌ Invalid input: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"❌ Failed to load data: {exc}")
    logger.exception("Error loading stock data")
    st.stop()

# Initialize session state for selected stock
if "selected_ticker" not in st.session_state:
    # Default to top performer
    if not summary.empty:
        st.session_state.selected_ticker = summary.iloc[0]["ticker"]
    else:
        st.session_state.selected_ticker = None

# Display top performers in a grid
st.subheader("🏆 Top Performers Leaderboard")

# Create columns for stock cards
num_cols = 3
cols = st.columns(num_cols)

for idx, row in summary.iterrows():
    col_idx = idx % num_cols
    ticker = row["ticker"]
    pct_change = row["pct_change"]
    start_price = row["start_price"]
    end_price = row["end_price"]
    
    with cols[col_idx]:
        # Determine if this card is selected
        is_selected = st.session_state.selected_ticker == ticker
        
        # Color based on performance
        color_class = "positive" if pct_change >= 0 else "negative"
        symbol = "📈" if pct_change >= 0 else "📉"
        
        # Create clickable card
        card_style = "selected" if is_selected else ""
        
        # Display stock info in a card-like format
        st.markdown(f"### {symbol} {ticker}")
        st.markdown(f"<p class='{color_class}' style='font-size: 1.5em; margin: 0.5em 0;'>{pct_change:+.2f}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 0.9em; color: #666;'>${start_price:.2f} → ${end_price:.2f}</p>", unsafe_allow_html=True)
        
        # Button to select this stock
        if st.button(f"📊 View Chart", key=f"btn_{ticker}", use_container_width=True):
            st.session_state.selected_ticker = ticker
            st.rerun()

# Main chart area
st.markdown("---")
st.subheader("📊 Stock Performance Chart")

# Stock selector
available_tickers = summary["ticker"].tolist()
try:
    default_index = available_tickers.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in available_tickers else 0
except (ValueError, AttributeError):
    default_index = 0

selected_ticker = st.selectbox(
    "Select a stock to view its chart:",
    options=available_tickers,
    index=default_index,
    key="ticker_selector"
)

# Update session state
st.session_state.selected_ticker = selected_ticker

if selected_ticker:
    # Ensure selected_ticker is a string (not a tuple)
    if isinstance(selected_ticker, tuple):
        selected_ticker = selected_ticker[-1]  # Take last element if tuple
    selected_ticker = str(selected_ticker)
    
    # Check if columns are MultiIndex and flatten them if needed
    if isinstance(prices.columns, pd.MultiIndex):
        # Flatten MultiIndex columns - take the last level (ticker name)
        prices.columns = [col[-1] if isinstance(col, tuple) else str(col) for col in prices.columns]
    else:
        # Ensure all columns are strings
        prices.columns = [str(col) for col in prices.columns]
    
    # Check if ticker exists in columns
    if selected_ticker not in prices.columns:
        st.error(f"Ticker {selected_ticker} not found in data. Available columns: {list(prices.columns)[:10]}")
        st.stop()
    
    # Prepare data for the selected stock
    # Get the price series directly first
    price_series = prices[selected_ticker].copy()
    
    # Reset index to convert date index to a column
    stock_data = prices[[selected_ticker]].copy()
    stock_data = stock_data.reset_index()
    
    # Find the date column - after reset_index, the index becomes a column
    # Check for common date column names
    date_col = None
    for possible_name in ["Date", "date", "index"]:
        if possible_name in stock_data.columns:
            date_col = possible_name
            break
    
    # If not found, the first column should be the date (from reset_index)
    if date_col is None and len(stock_data.columns) > 0:
        date_col = stock_data.columns[0]
    
    # Rename to "Date" for consistency
    if date_col and date_col != "Date":
        stock_data = stock_data.rename(columns={date_col: "Date"})
    
    # Final check - if Date column still doesn't exist, something went wrong
    if "Date" not in stock_data.columns:
        st.error(f"Could not find Date column. Available columns: {list(stock_data.columns)}")
        st.stop()
    
    # Ensure we have the price series as a Series (not DataFrame)
    if isinstance(stock_data[selected_ticker], pd.DataFrame):
        price_series = stock_data[selected_ticker].iloc[:, 0]
    else:
        price_series = stock_data[selected_ticker]
    
    # Get stock info from summary
    stock_info = summary[summary["ticker"] == selected_ticker]
    if not stock_info.empty:
        pct_change = stock_info.iloc[0]["pct_change"]
        current_price = stock_info.iloc[0]["end_price"]
        
        # Display stock info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**Ticker**")
            st.markdown(f"### {selected_ticker}")
        with col2:
            st.metric("Current Price", current_price, delta=None)
        with col3:
            st.metric("30-Day Change", f"{pct_change:+.2f}%")
        with col4:
            # Extract scalar values - ensure we have a Series
            try:
                start_val = float(price_series.iloc[0])
                end_val = float(price_series.iloc[-1])
            except (TypeError, ValueError, AttributeError):
                # Fallback: convert to list and take first/last
                price_list = price_series.tolist() if hasattr(price_series, 'tolist') else list(price_series)
                start_val = float(price_list[0])
                end_val = float(price_list[-1])
            price_change = end_val - start_val
            st.metric("Price Change", price_change, delta=None)
    
    # Create the chart
    try:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=stock_data["Date"],
            y=price_series,
            mode='lines+markers',
            name=selected_ticker,
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Date: %{x}<br>' +
                         'Price: $%{y:.2f}<extra></extra>'
        ))
        
        # Add fill area
        fig.add_trace(go.Scatter(
            x=stock_data["Date"],
            y=price_series,
            mode='lines',
            name='Fill',
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Calculate trend - extract scalar values
        try:
            start_price = float(price_series.iloc[0])
            end_price = float(price_series.iloc[-1])
        except (TypeError, ValueError, AttributeError):
            # Fallback: convert to list and take first/last
            price_list = price_series.tolist() if hasattr(price_series, 'tolist') else list(price_series)
            start_price = float(price_list[0])
            end_price = float(price_list[-1])
        trend_color = '#00cc00' if end_price >= start_price else '#ff3333'
        
        fig.update_layout(
            title=f"{selected_ticker} - Last {days} Days Performance",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            hovermode='x unified',
            template='plotly_white',
            height=500,
            showlegend=False,
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional stats
        with st.expander("📈 Detailed Statistics", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                highest = float(price_series.max())
                st.metric("Highest Price", highest, delta=None)
                lowest = float(price_series.min())
                st.metric("Lowest Price", lowest, delta=None)
            
            with col2:
                avg_price = float(price_series.mean())
                st.metric("Average Price", avg_price, delta=None)
                volatility = float(price_series.std())
                st.metric("Volatility", volatility, delta=None)
            
            with col3:
                total_return = float(((end_price - start_price) / start_price) * 100)
                st.metric("Total Return", f"{total_return:+.2f}%", delta=None)
                days_count = int(len(stock_data))
                st.metric("Trading Days", days_count, delta=None)
    
    except Exception as e:
        st.error(f"Error creating chart: {e}")
        logger.exception("Error creating chart")
        # Fallback: show raw data
        st.dataframe(stock_data)
else:
    st.info("👆 Select a stock from the leaderboard above to view its performance chart.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>📊 Data provided by Yahoo Finance via yfinance</p>
        <p>💡 Tip: Refresh the page to get the latest data</p>
    </div>
""", unsafe_allow_html=True)
