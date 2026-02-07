import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Polymarket Copy Trade Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# APIs
DATA_API = "https://data-api.polymarket.com"
PROFILE_API = "https://gamma-api.polymarket.com"

# Session state
if 'monitor_active' not in st.session_state:
    st.session_state.monitor_active = False
if 'check_count' not in st.session_state:
    st.session_state.check_count = 0
if 'trade_count' not in st.session_state:
    st.session_state.trade_count = 0
if 'copy_count' not in st.session_state:
    st.session_state.copy_count = 0
if 'skip_count' not in st.session_state:
    st.session_state.skip_count = 0
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'latest_trades' not in st.session_state:
    st.session_state.latest_trades = []
if 'your_positions' not in st.session_state:
    st.session_state.your_positions = []

def add_log(message, log_type="info"):
    """Add message to logs"""
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "message": message,
        "type": log_type
    }
    st.session_state.logs.insert(0, log_entry)
    if len(st.session_state.logs) > 100:
        st.session_state.logs.pop()

def get_profile_name(address):
    """Get trader profile name"""
    try:
        response = requests.get(f"{PROFILE_API}/public-profile?address={address}", timeout=10)
        if response.status_code == 200:
            profile = response.json()
            return profile.get("name") or profile.get("pseudonym") or f"{address[:10]}..."
    except:
        pass
    return f"{address[:10]}..."

@st.cache_data(ttl=300)
def get_latest_bets(address):
    """Get trader's latest BUY trades"""
    try:
        response = requests.get(f"{DATA_API}/activity?user={address}&limit=50", timeout=10)
        if response.status_code == 200:
            activities = response.json()
            buy_trades = [a for a in activities if a.get("type") == "TRADE" and a.get("side") == "BUY"]
            return buy_trades[:10]
    except:
        pass
    return []

@st.cache_data(ttl=300)
def get_positions(address):
    """Get user's positions"""
    try:
        response = requests.get(f"{DATA_API}/positions?user={address}&sizeThreshold=0", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def already_has_position(positions, condition_id, outcome_index):
    """Check if already in position"""
    key = f"{condition_id}_{outcome_index}"
    pos_keys = {f"{p.get('conditionId')}_{p.get('outcomeIndex')}" for p in positions}
    return key in pos_keys

def perform_check(target_address):
    """Perform single monitoring check"""
    st.session_state.check_count += 1
    
    add_log(f"[Check {st.session_state.check_count}] Fetching latest bets...", "info")
    
    # Get latest trades
    latest_trades = get_latest_bets(target_address)
    st.session_state.latest_trades = latest_trades
    
    if not latest_trades:
        add_log("No recent trades found. Nothing to copy.", "warning")
        return
    
    # Display trades
    add_log(f"Found {len(latest_trades)} recent trades", "success")
    
    st.session_state.trade_count += 1
    
    # Get latest trade
    latest_trade = latest_trades[0]
    title = latest_trade.get("title", "")[:50]
    outcome = latest_trade.get("outcome", "")
    size = latest_trade.get("size", 0)
    price = latest_trade.get("price", 0)
    
    add_log(f"Latest: {title} - {size:.1f} {outcome} @ {(price*100):.1f}¢", "success")
    
    # Get positions
    positions = get_positions(target_address)
    st.session_state.your_positions = positions
    
    if positions:
        add_log(f"You have {len(positions)} open position(s)", "info")
    else:
        add_log("You have no open positions", "info")
    
    # Check if should copy
    if already_has_position(positions, latest_trade.get("conditionId"), latest_trade.get("outcomeIndex")):
        st.session_state.skip_count += 1
        add_log("Already in this market. Would NOT copy.", "warning")
    else:
        st.session_state.copy_count += 1
        add_log("Not in this market. Would copy: BUY $2.00", "success")
        add_log("[DRY RUN] Simulated order placed successfully", "info")

# Header
st.title("📊 Polymarket Copy Trade Monitor")
st.markdown("**Dry run monitoring** - Track how accurately you would copy a trader's positions")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    target_address = st.text_input(
        "Target Trader Address (0x...)",
        placeholder="0x0000000000000000000000000000000000000000",
        help="Enter the Ethereum address of the trader you want to copy"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bet Amount", "$2.00")
    with col2:
        st.metric("Mode", "DRY RUN", delta="Safe Mode")
    with col3:
        st.metric("Check Interval", "10 seconds")
    
    # Control buttons
    if st.button("▶️ Start Monitoring", type="primary", disabled=not target_address or not target_address.startswith("0x")):
        if target_address.startswith("0x"):
            st.session_state.target_address = target_address
            st.session_state.monitor_active = True
            st.rerun()
        else:
            st.error("Please enter a valid Ethereum address (starting with 0x)")
    
    if st.button("⏹️ Stop Monitoring"):
        st.session_state.monitor_active = False
        st.rerun()

# Main content
col1, col2 = st.columns([1, 3])

with col1:
    # Status card
    with st.container():
        st.subheader("Monitor Status")
        
        status_color = "🟢 Active" if st.session_state.monitor_active else "🔴 Inactive"
        st.metric("Status", status_color)
        
        st.metric("Target Trader", get_profile_name(st.session_state.get("target_address", "")))
        st.metric("Checks Performed", st.session_state.check_count)
        st.metric("Trades Detected", st.session_state.trade_count)
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Would Copy", st.session_state.copy_count)
        with col_b:
            st.metric("Already In Position", st.session_state.skip_count)

with col2:
    # Latest trades
    st.subheader("🎯 Target's Latest Trades")
    if st.session_state.latest_trades:
        for i, trade in enumerate(st.session_state.latest_trades[:5]):
            with st.container():
                outcome_color = "🟢 YES" if trade.get("outcome") == "YES" else "🔴 NO"
                st.markdown(f"**{trade.get('title', 'N/A')[:60]}...**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Outcome", outcome_color)
                with col2:
                    st.metric("Size", f"{trade.get('size', 0):.2f}")
                with col3:
                    st.metric("Price", f"${trade.get('price', 0):.3f}")
                st.caption(f"Time: {datetime.fromtimestamp(trade.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M')}")
                st.divider()
    else:
        st.info("No trade data yet. Start monitoring to fetch.")

# Positions row
st.subheader("📍 Your Current Positions")
if st.session_state.your_positions:
    for pos in st.session_state.your_positions[:3]:
        outcome_color = "🟢" if pos.get("outcome") == "YES" else "🔴"
        pnl_color = "🟢" if pos.get("cashPnl", 0) >= 0 else "🔴"
        st.markdown(f"**{pos.get('title', 'N/A')[:60]}...**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Outcome", outcome_color + " " + pos.get("outcome", ""))
        with col2:
            st.metric("Size", f"{pos.get('size', 0):.2f}")
        with col3:
            st.metric("Avg Price", f"${pos.get('avgPrice', 0):.3f}")
        with col4:
            st.metric("P&L", f"${pos.get('cashPnl', 0):.2f}", delta=pos.get('cashPnl', 0))
        st.divider()
else:
    st.info("No open positions")

# Activity log
with st.expander("📜 Activity Log", expanded=True):
    log_df = pd.DataFrame(st.session_state.logs)
    if not log_df.empty:
        st.dataframe(
            log_df,
            column_config={
                "timestamp": "Time",
                "message": st.column_config.TextColumn("Message", width="medium"),
                "type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["info", "success", "warning", "error"],
                    width="small"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Activity will appear here when monitoring starts.")

# Auto-refresh logic
if st.session_state.monitor_active and st.session_state.get("target_address"):
    time.sleep(1)  # Small delay to avoid rate limits
    perform_check(st.session_state.target_address)
    st.rerun()
