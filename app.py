import streamlit as st
import requests
import json
from datetime import datetime
import time
import pandas as pd

# Streamlit page config
st.set_page_config(
    page_title="Polymarket Copy Trade Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match the original design exactly
st.markdown("""
<style>
    :root {
        --color-background: #fcfcf9;
        --color-surface: #fffffd;
        --color-text: #134252;
        --color-text-secondary: #626c71;
        --color-primary: #21808d;
        --color-primary-hover: #1d7480;
        --color-border: rgba(94, 82, 64, 0.2);
        --color-success: #21808d;
        --color-error: #c0152f;
        --color-warning: #a84b2f;
        --color-info: #626c71;
        --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04);
        --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.04);
    }

    .main .block-container {
        padding-top: 1rem;
        background: var(--color-background);
        color: var(--color-text);
    }

    .card {
        background: var(--color-surface);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid var(--color-border);
        box-shadow: var(--shadow-sm);
    }

    .card h3 {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .stTextInput > label {
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--color-text-secondary) !important;
        margin-bottom: 6px !important;
    }

    .stTextInput > div > div > input {
        padding: 10px 12px !important;
        border: 1px solid var(--color-border) !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        background: var(--color-surface) !important;
        color: var(--color-text) !important;
    }

    .stButton > button {
        padding: 10px 16px !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s !important;
        height: auto !important;
        line-height: 1.2 !important;
    }

    .btn-primary {
        background: var(--color-primary) !important;
        color: white !important;
    }

    .btn-primary:hover {
        background: var(--color-primary-hover) !important;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
    }

    .status-active {
        background: rgba(33, 128, 141, 0.15);
        color: var(--color-success);
        border: 1px solid rgba(33, 128, 141, 0.25);
    }

    .status-inactive {
        background: rgba(119, 124, 124, 0.15);
        color: var(--color-text-secondary);
        border: 1px solid var(--color-border);
    }

    .status-checking {
        background: rgba(168, 75, 47, 0.15);
        color: var(--color-warning);
        border: 1px solid rgba(168, 75, 47, 0.25);
    }

    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid var(--color-border);
        font-size: 14px;
    }

    .info-row:last-child {
        border-bottom: none;
    }

    .info-label {
        color: var(--color-text-secondary);
        font-weight: 500;
    }

    .info-value {
        font-weight: 600;
        text-align: right;
    }

    .position-card {
        padding: 16px;
        border: 1px solid var(--color-border);
        border-radius: 8px;
        background: var(--color-background);
        margin-bottom: 12px;
    }

    .outcome-yes {
        color: var(--color-success);
        font-weight: 600;
    }

    .outcome-no {
        color: var(--color-error);
        font-weight: 600;
    }

    .log-entry {
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 6px;
        font-size: 13px;
        font-family: 'Courier New', monospace;
        border-left: 3px solid var(--color-border);
        background: var(--color-surface);
    }

    .log-info { border-left-color: var(--color-info); }
    .log-success { border-left-color: var(--color-success); }
    .log-warning { border-left-color: var(--color-warning); }
    .log-error { border-left-color: var(--color-error); }

    .settings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
        padding: 16px;
        background: var(--color-background);
        border-radius: 8px;
    }

    .empty-state {
        text-align: center;
        padding: 40px;
        color: var(--color-text-secondary);
        font-style: italic;
    }

    .pulse {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--color-warning);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
</style>
""", unsafe_allow_html=True)

# CORE VARIABLES - Exact match to original
monitor_active = False
check_count = 0
trade_count = 0
copy_count = 0
skip_count = 0
target_address = ''
your_address = ''
logs = []
DATA_API = "https://data-api.polymarket.com"
PROFILE_API = "https://gamma-api.polymarket.com"

# Streamlit session state for persistence
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
if 'your_address' not in st.session_state = ''
if 'trader_name' not in st.session_state:
    st.session_state.trader_name = 'Not set'

# Update session state
monitor_active = st.session_state.monitor_active
check_count = st.session_state.check_count
trade_count = st.session_state.trade_count
copy_count = st.session_state.copy_count
skip_count = st.session_state.skip_count
logs = st.session_state.logs
target_address = st.session_state.target_address
your_address = st.session_state.your_address
trader_name = st.session_state.trader_name

# CORE FUNCTIONS - NO CHANGES TO TRACKING LOGIC
def add_log(message, log_type='info'):
    """Exact same as original"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs.insert(0, {'message': message, 'time': timestamp, 'type': log_type})
    
    if len(logs) > 100:
        logs.pop()
    
    st.session_state.logs = logs

@st.cache_data(ttl=300)
def get_profile_name(address):
    """Exact same as original"""
    try:
        response = requests.get(f"{PROFILE_API}/public-profile?address={address}", timeout=10)
        profile = response.json()
        return profile.get('name') or profile.get('pseudonym') or f"{address[:10]}..."
    except:
        return f"{address[:10]}..."

@st.cache_data(ttl=60)
def get_latest_bet(address):
    """Exact same as original - CORE TRACKING FUNCTION"""
    try:
        response = requests.get(f"{DATA_API}/activity?user={address}&limit=50", timeout=10)
        activities = response.json()
        
        buy_trades = [a for a in activities if a.get('type') == 'TRADE' and a.get('side') == 'BUY'][:10]
        return buy_trades if buy_trades else None
    except Exception as e:
        add_log(f"Error fetching trades: {str(e)}", 'error')
        return None

@st.cache_data(ttl=60)
def get_positions(address):
    """Exact same as original - CORE TRACKING FUNCTION"""
    try:
        response = requests.get(f"{DATA_API}/positions?user={address}&sizeThreshold=0", timeout=10)
        return response.json()
    except Exception as e:
        add_log(f"Error fetching positions: {str(e)}", 'error')
        return []

def display_latest_trades(trades):
    """Exact same as original"""
    if not trades or len(trades) == 0:
        return '<div class="empty-state">No recent trades found</div>'
    
    html = ''
    for i, trade in enumerate(trades):
        outcome_class = 'outcome-yes' if trade.get('outcome') == 'YES' else 'outcome-no'
        html += f'''
        <div class="position-card">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <div class="position-header" style="margin-bottom: 0;">{trade.get("title", "Unknown")}</div>
                <span style="font-size: 12px; color: var(--color-text-secondary);">#{"%d" % (i+1)}</span>
            </div>
            <div class="position-details">
                <div><strong>Position:</strong> <span class="{outcome_class}">{trade.get("outcome", "")}</span></div>
                <div><strong>Size:</strong> {trade.get("size", 0):.2f} contracts</div>
                <div><strong>Price:</strong> {(trade.get("price", 0) * 100):.1f}¢</div>
                <div><strong>Value:</strong> ${(trade.get("size", 0) * trade.get("price", 0)):.2f}</div>
                <div><strong>Time:</strong> {datetime.fromtimestamp(trade.get("timestamp", 0)/1000).strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
        </div>
        '''
    return html

def display_your_positions(positions):
    """Exact same as original"""
    if len(positions) == 0:
        return '<div class="empty-state">No open positions</div>'
    
    html = ''
    for pos in positions[:3]:
        outcome_class = 'outcome-yes' if pos.get('outcome') == 'YES' else 'outcome-no'
        pnl_class = 'outcome-yes' if pos.get('cashPnl', 0) >= 0 else 'outcome-no'
        pnl_sign = '+' if pos.get('cashPnl', 0) >= 0 else ''
        html += f'''
        <div class="position-card">
            <div class="position-header">{pos.get("title", "Unknown")}</div>
            <div class="position-details">
                <div><strong>Position:</strong> <span class="{outcome_class}">{pos.get("outcome", "")}</span></div>
                <div><strong>Size:</strong> {pos.get("size", 0):.2f}</div>
                <div><strong>Avg Price:</strong> {(pos.get("avgPrice", 0) * 100):.1f}¢</div>
                <div><strong>P&L:</strong> <span class="{pnl_class}">{pnl_sign}${pos.get("cashPnl", 0):.2f}</span></div>
            </div>
        </div>
        '''
    
    if len(positions) > 3:
        html += f'<div style="text-align: center; margin-top: 12px; color: var(--color-text-secondary); font-size: 13px;">+ {len(positions) - 3} more positions</div>'
    
    return html

def already_has_position(my_positions, condition_id, outcome_index):
    """Exact same as original"""
    key = lambda c, o: f"{c}_{o}"
    target_key = key(condition_id, outcome_index)
    my_keys = {key(p.get('conditionId'), p.get('outcomeIndex')) for p in my_positions}
    return target_key in my_keys

# CORE CHECK FUNCTION - NO CHANGES
async def perform_check():
    """Exact same logic as original - CORE TRACKING"""
    global check_count, trade_count, copy_count, skip_count
    
    check_count += 1
    st.session_state.check_count = check_count
    
    add_log(f"[Check {check_count}] Fetching target's latest bet...", 'info')

    latest_trades = get_latest_bet(target_address)
    
    if not latest_trades or len(latest_trades) == 0:
        add_log('No recent trades found. Nothing to copy.', 'warning')
        return

    # Update session state for display
    st.session_state.latest_trades = latest_trades

    latest_trade = latest_trades[0]
    trade_count += 1
    st.session_state.trade_count = trade_count

    title = latest_trade.get('title', '')[:50]
    outcome = latest_trade.get('outcome', '')
    target_size = latest_trade.get('size', 0)
    price = latest_trade.get('price', 0)

    add_log(f"Found {len(latest_trades)} recent trades. Latest: {title} - {target_size:.1f} {outcome} @ {(price * 100):.1f}¢", 'success')

    add_log('Checking your positions...', 'info')
    my_positions = get_positions(your_address)
    st.session_state.my_positions = my_positions

    if len(my_positions) > 0:
        add_log(f"You have {len(my_positions)} open position(s)", 'info')
    else:
        add_log('You have no open positions', 'info')

    if already_has_position(my_positions, latest_trade.get('conditionId'), latest_trade.get('outcomeIndex')):
        skip_count += 1
        st.session_state.skip_count = skip_count
        add_log("Already in this market. Would NOT copy.", 'warning')
    else:
        copy_count += 1
        st.session_state.copy_count = copy_count
        add_log(f"Not in this market. Would copy: BUY $2.00 of {outcome}", 'success')
        add_log("[DRY RUN] Simulated order placed successfully", 'info')

    add_log("─" * 50, 'info')

# Main UI
st.title("📊 Polymarket Copy Trade Monitor")
st.markdown("**Dry run monitoring** - Track how accurately you would copy a trader's positions")

# Configuration Card
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>⚙️ Configuration</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        target_address = st.text_input(
            "Target Trader Address (0x...)",
            value=target_address,
            placeholder="0x0000000000000000000000000000000000000000",
            key="target_address_input",
            help="Enter a valid Ethereum address starting with 0x"
        )
    
    st.markdown("""
    <div class="settings-grid">
        <div class="setting-item">
            <label>Bet Amount</label>
            <div class="setting-value">$2.00</div>
        </div>
        <div class="setting-item">
            <label>Mode</label>
            <div class="setting-value" style="color: var(--color-warning);">DRY RUN</div>
        </div>
        <div class="setting-item">
            <label>Check Interval</label>
            <div class="setting-value">10 seconds</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Start Monitoring", key="start_btn", help="Click to begin monitoring"):
            if not target_address or not target_address.startswith('0x'):
                st.error("Please enter a valid Ethereum address (starting with 0x)")
            else:
                st.session_state.target_address = target_address
                st.session_state.your_address = target_address
                st.session_state.monitor_active = True
                st.rerun()
    
    with col_btn2:
        if st.button("Stop Monitoring", key="stop_btn"):
            st.session_state.monitor_active = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Status Card
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    status_indicator = '<span class="pulse"></span>' if monitor_active else ''
    status_class = "status-checking" if monitor_active else "status-inactive"
    status_text = "Active" if monitor_active else "Inactive"
    
    st.markdown(f'''
    <h3>{status_indicator}Monitor Status: <span class="status-badge {status_class}">{status_text}</span></h3>
    <div class="info-row">
        <span class="info-label">Target Trader</span>
        <span class="info-value">{trader_name}</span>
    </div>
    <div class="info-row">
        <span class="info-label">Checks Performed</span>
        <span class="info-value">{check_count}</span>
    </div>
    <div class="info-row">
        <span class="info-label">Trades Detected</span>
        <span class="info-value">{trade_count}</span>
    </div>
    <div class="info-row">
        <span class="info-label">Would Copy</span>
        <span class="info-value">{copy_count}</span>
    </div>
    <div class="info-row">
        <span class="info-label">Already In Position</span>
        <span class="info-value">{skip_count}</span>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Latest Trades Card
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>🎯 Target\'s Latest 10 Trades</h3>', unsafe_allow_html=True)
    
    if 'latest_trades' in st.session_state and st.session_state.latest_trades:
        st.markdown(display_latest_trades(st.session_state.latest_trades), unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">No trade data yet. Start monitoring to fetch.</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Your Positions Card
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>📍 Your Current Positions</h3>', unsafe_allow_html=True)
    
    if 'my_positions' in st.session_state and st.session_state.my_positions:
        st.markdown(display_your_positions(st.session_state.my_positions), unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">No position data yet. Start monitoring to fetch.</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Activity Log Card
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>📜 Activity Log</h3>', unsafe_allow_html=True)
    
    log_html = '<div class="log-container" style="max-height: 500px; overflow-y: auto; background: var(--color-background); border-radius: 8px; padding: 12px;">'
    if logs:
        for log in logs:
            log_class = f"log-{log['type']}"
            log_html += f'''
            <div class="log-entry {log_class}">
                <div class="log-time">{log['time']}</div>
                <div>{log['message']}</div>
            </div>
            '''
    else:
        log_html += '<div class="empty-state">Activity will appear here when monitoring starts.</div>'
    log_html += '</div>'
    
    st.markdown(log_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Auto-monitoring logic (runs every 10 seconds when active)
if monitor_active:
    # Initialize trader name on first run
    if not trader_name or trader_name == 'Not set':
        trader_name = get_profile_name(target_address)
        st.session_state.trader_name = trader_name
    
    # Perform check
    perform_check()
    
    # Auto-rerun every 10 seconds
    time.sleep(10)
    st.rerun()
else:
    # Reset on stop
    st.session_state.check_count = 0
    st.session_state.trade_count = 0
    st.session_state.copy_count = 0
    st.session_state.skip_count = 0
    st.session_state.logs = []
    st.session_state.latest_trades = None
    st.session_state.my_positions = []
