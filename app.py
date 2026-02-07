import streamlit as st
import requests
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Polymarket Copy Trade Monitor",
    page_icon="📊",
    layout="wide"
)

# API endpoints (unchanged from original)
DATA_API = "https://data-api.polymarket.com"
PROFILE_API = "https://gamma-api.polymarket.com"

# Initialize session state
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
if 'target_address' not in st.session_state:
    st.session_state.target_address = ''
if 'trader_name' not in st.session_state:
    st.session_state.trader_name = 'Not set'
if 'latest_trades' not in st.session_state:
    st.session_state.latest_trades = None
if 'your_positions' not in st.session_state:
    st.session_state.your_positions = []

# Custom CSS (matching original design)
st.markdown("""
<style>
    .stApp {
        background-color: #fcfcf9;
    }
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #1f2121;
        }
    }
    .metric-card {
        background: #fffffd;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(94, 82, 64, 0.2);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .log-entry {
        font-family: 'Courier New', monospace;
        font-size: 13px;
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 6px;
        border-left: 3px solid #626c71;
    }
    .log-success { border-left-color: #21808d; }
    .log-warning { border-left-color: #a84b2f; }
    .log-error { border-left-color: #c0152f; }
    .outcome-yes { color: #21808d; font-weight: 600; }
    .outcome-no { color: #c0152f; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Helper functions (matching original logic exactly)
def add_log(message, log_type='info'):
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.logs.insert(0, {'message': message, 'time': timestamp, 'type': log_type})
    if len(st.session_state.logs) > 100:
        st.session_state.logs.pop()

def get_profile_name(address):
    try:
        response = requests.get(f"{PROFILE_API}/public-profile?address={address}")
        profile = response.json()
        return profile.get('name') or profile.get('pseudonym') or f"{address[:10]}..."
    except:
        return f"{address[:10]}..."

def get_latest_bet(address):
    try:
        response = requests.get(f"{DATA_API}/activity?user={address}&limit=50")
        activities = response.json()
        buy_trades = [a for a in activities if a.get('type') == 'TRADE' and a.get('side') == 'BUY'][:10]
        return buy_trades if buy_trades else None
    except Exception as e:
        add_log(f"Error fetching trades: {str(e)}", 'error')
        return None

def get_positions(address):
    try:
        response = requests.get(f"{DATA_API}/positions?user={address}&sizeThreshold=0")
        return response.json()
    except Exception as e:
        add_log(f"Error fetching positions: {str(e)}", 'error')
        return []

def already_has_position(my_positions, condition_id, outcome_index):
    target_key = f"{condition_id}_{outcome_index}"
    my_keys = set(f"{p.get('conditionId')}_{p.get('outcomeIndex')}" for p in my_positions)
    return target_key in my_keys

def perform_check():
    if not st.session_state.monitor_active:
        return
    
    st.session_state.check_count += 1
    add_log(f"[Check {st.session_state.check_count}] Fetching target's latest bet...", 'info')
    
    latest_trades = get_latest_bet(st.session_state.target_address)
    
    if not latest_trades:
        add_log('No recent trades found. Nothing to copy.', 'warning')
        st.session_state.latest_trades = None
        return
    
    st.session_state.latest_trades = latest_trades
    latest_trade = latest_trades[0]
    st.session_state.trade_count += 1
    
    title = latest_trade.get('title', '')[:50]
    outcome = latest_trade.get('outcome', '')
    target_size = latest_trade.get('size', 0)
    price = latest_trade.get('price', 0)
    
    add_log(f"Found {len(latest_trades)} recent trades. Latest: {title} - {target_size:.1f} {outcome} @ {(price * 100):.1f}¢", 'success')
    
    add_log('Checking your positions...', 'info')
    my_positions = get_positions(st.session_state.target_address)
    st.session_state.your_positions = my_positions
    
    if my_positions:
        add_log(f"You have {len(my_positions)} open position(s)", 'info')
    else:
        add_log('You have no open positions', 'info')
    
    if already_has_position(my_positions, latest_trade.get('conditionId'), latest_trade.get('outcomeIndex')):
        st.session_state.skip_count += 1
        add_log("Already in this market. Would NOT copy.", 'warning')
    else:
        st.session_state.copy_count += 1
        add_log(f"Not in this market. Would copy: BUY $2.00 of {outcome}", 'success')
        add_log("[DRY RUN] Simulated order placed successfully", 'info')
    
    add_log('─' * 50, 'info')

# UI Header
st.title("📊 Polymarket Copy Trade Monitor")
st.caption("Dry run monitoring - Track how accurately you would copy a trader's positions")

# Configuration Card
with st.container():
    st.subheader("⚙️ Configuration")
    
    target_input = st.text_input(
        "Target Trader Address (0x...)",
        placeholder="0x0000000000000000000000000000000000000000",
        key="target_input"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bet Amount", "$2.00")
    with col2:
        st.metric("Mode", "DRY RUN")
    with col3:
        st.metric("Check Interval", "10 seconds")
    
    col_btn1, col_btn2 = st.columns([1, 5])
    
    with col_btn1:
        if not st.session_state.monitor_active:
            if st.button("Start Monitoring", type="primary", use_container_width=True):
                if target_input and target_input.startswith('0x'):
                    st.session_state.target_address = target_input
                    st.session_state.monitor_active = True
                    add_log('═' * 50, 'info')
                    add_log('Monitor started', 'success')
                    st.session_state.trader_name = get_profile_name(target_input)
                    add_log(f"Copying: {st.session_state.trader_name}", 'info')
                    add_log("Bet amount: $2.00", 'info')
                    add_log("Mode: DRY RUN", 'info')
                    add_log('═' * 50, 'info')
                    perform_check()
                    st.rerun()
                else:
                    st.error("Please enter a valid Ethereum address (starting with 0x)")
    
    with col_btn2:
        if st.session_state.monitor_active:
            if st.button("Stop Monitoring", use_container_width=True):
                st.session_state.monitor_active = False
                add_log('═' * 50, 'info')
                add_log('Monitor stopped', 'warning')
                add_log('═' * 50, 'info')
                st.rerun()

st.divider()

# Monitor Status Card
with st.container():
    status_col1, status_col2 = st.columns([1, 3])
    with status_col1:
        if st.session_state.monitor_active:
            st.success("🟢 Monitor Status: Active")
        else:
            st.info("⚪ Monitor Status: Inactive")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Target Trader", st.session_state.trader_name)
    with col2:
        st.metric("Checks Performed", st.session_state.check_count)
    with col3:
        st.metric("Trades Detected", st.session_state.trade_count)
    with col4:
        st.metric("Would Copy", st.session_state.copy_count)
    with col5:
        st.metric("Already In Position", st.session_state.skip_count)

st.divider()

# Two column layout for trades and positions
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🎯 Target's Latest 10 Trades")
    if st.session_state.latest_trades:
        for idx, trade in enumerate(st.session_state.latest_trades):
            outcome_class = "outcome-yes" if trade.get('outcome') == 'YES' else "outcome-no"
            with st.container():
                st.markdown(f"**#{idx + 1}: {trade.get('title', 'Unknown')}**")
                st.markdown(f"<span class='{outcome_class}'>{trade.get('outcome', 'N/A')}</span> | "
                           f"Size: {trade.get('size', 0):.2f} | "
                           f"Price: {(trade.get('price', 0) * 100):.1f}¢ | "
                           f"Value: ${(trade.get('size', 0) * trade.get('price', 0)):.2f}", 
                           unsafe_allow_html=True)
                st.caption(f"Time: {datetime.fromtimestamp(trade.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()
    else:
        st.info("No trade data yet. Start monitoring to fetch.")

with col_right:
    st.subheader("📍 Your Current Positions")
    if st.session_state.your_positions:
        for pos in st.session_state.your_positions[:3]:
            outcome_class = "outcome-yes" if pos.get('outcome') == 'YES' else "outcome-no"
            pnl = pos.get('cashPnl', 0)
            pnl_class = "outcome-yes" if pnl >= 0 else "outcome-no"
            with st.container():
                st.markdown(f"**{pos.get('title', 'Unknown')}**")
                st.markdown(f"<span class='{outcome_class}'>{pos.get('outcome', 'N/A')}</span> | "
                           f"Size: {pos.get('size', 0):.2f} | "
                           f"Avg Price: {(pos.get('avgPrice', 0) * 100):.1f}¢ | "
                           f"<span class='{pnl_class}'>P&L: {'+ ' if pnl >= 0 else ''}${pnl:.2f}</span>",
                           unsafe_allow_html=True)
                st.divider()
        if len(st.session_state.your_positions) > 3:
            st.caption(f"+ {len(st.session_state.your_positions) - 3} more positions")
    else:
        st.info("No position data yet. Start monitoring to fetch.")

st.divider()

# Activity Log
st.subheader("📜 Activity Log")
log_container = st.container(height=400)
with log_container:
    if st.session_state.logs:
        for log in st.session_state.logs:
            log_class = f"log-{log['type']}"
            st.markdown(f"<div class='log-entry {log_class}'>"
                       f"<small>{log['time']}</small><br/>{log['message']}</div>",
                       unsafe_allow_html=True)
    else:
        st.info("Activity will appear here when monitoring starts.")

# Auto-refresh when monitoring is active
if st.session_state.monitor_active:
    time.sleep(10)
    perform_check()
    st.rerun()
