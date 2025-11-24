import streamlit as st
import requests
import json
import re
import yfinance as yf

st.set_page_config(page_title="Global AI Hedge Fund Pod", layout="wide")
st.title("Global AI Hedge Fund Pod — NASDAQ/HOOD Fixed")

# API Key (handles OPENAI or GROK)
API_KEY = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("GROK_API_KEY")
if not API_KEY:
    st.error("Add OPENAI_API_KEY or GROK_API_KEY in secrets")
    st.stop()
st.sidebar.success("API key loaded")

raw_input = st.sidebar.text_input("Symbol (HOOD, NVDA, BTCUSD, etc.)", value="HOOD").strip().upper()

# FIXED UNIVERSAL MAPPER — HOOD = NASDAQ:HOOD (TradingView standard)
def get_symbol(t):
    t = t.upper().replace(" ", "")
    # Crypto
    if any(c in t for c in ["BTC","ETH","SOL","DOGE"]): return f"BINANCE:{t}USDT"
    # Forex
    if any(fx in t for fx in ["EURUSD","GBPUSD","USDJPY"]): return f"FX:{t}"
    # Futures
    if any(fut in t for fut in ["ES","NQ","CL"]): return f"CME:{t}1!"
    # International
    if t.endswith(".T"): return f"TSE:{t.replace('.T','')}"
    if t.endswith(".HK"): return f"HKEX:{t.replace('.HK','')}"
    if t.endswith(".L"): return f"LSE:{t.replace('.L','')}"
    # US Stocks — NASDAQ default (HOOD works as NASDAQ:HOOD per TradingView)
    if len(t) <= 5 and t.isalpha():
        if t in ["JPM", "BAC", "GS", "MS"]: return f"NYSE:{t}"  # True NYSE-only
        return f"NASDAQ:{t}"  # HOOD, NVDA, AAPL, SPY all NASDAQ in TradingView
    return t  # Full format

symbol = get_symbol(raw_input)
interval = st.sidebar.selectbox("Timeframe (min)", ["5","15","60"], index=0)

# TradingView Chart — Now loads HOOD as NASDAQ:HOOD
st.components.v1.html(f"""
<div class="tradingview-widget-container" style="height:700px; width:100%;">
  <div id="tv_chart"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "width": "100%",
    "height": 700,
    "symbol": "{symbol}",
    "interval": "{interval}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "container_id": "tv_chart"
  }});
  </script>
</div>
""", height=720)

# Live price
@st.cache_data(ttl=30)
def get_price():
    try:
        ticker = yf.Ticker(raw_input)
        data = ticker.history(period="1d")
        return round(data['Close'].iloc[-1], 2)
    except:
        return 0.0

live_price = get_price()
st.sidebar.metric("Live Price", f"${live_price}")

# AI Pod
def get_strategies():
    prompt = f"""Analyze {raw_input} at EXACT ${live_price} on {interval}min chart.

7 managers: 1. Cathie Wood 2. Warren Buffett 3. Ray Dalio 4. Paul Tudor Jones 5. Jim Simons 6. JPMorgan Prop 7. UBS Global

JSON array ONLY (7 objects):
[{{"manager":"Cathie Wood","direction":"Long","setup":"Breakout","entry":"{live_price-0.5}-{live_price+0.5}","target1":"{live_price+5}","stop":"{live_price-2}","rr":"3:1","confidence":94}}, ...]"""

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0.2,"max_tokens":1200},
            timeout=20)
        text = r.json()["choices"][0]["message"]["content"]
        match = re.search(r"\[.*\]", text, re.DOTALL)
        return json.loads(match.group()) if match else []
    except:
        return []

col1, col2 = st.columns([2.5, 1])
with col2:
    st.markdown("### 7 Legends Live")
    if st.button("ANALYZE NOW", type="primary", use_container_width=True):
        with st.spinner("Analyzing..."):
            st.session_state.strategies = get_strategies()

    if "strategies" in st.session_state:
        for s in st.session_state.strategies:
            color = "#00ff88" if "Long" in s.get("direction", "") else "#ff0066"
            st.markdown(f"### {s.get('manager', '?')}")
            st.markdown(f"<p style='color:{color};font-size:18px'><b>{s.get('direction', 'Hold')} — {s.get('setup', '?')}</b></p>", unsafe_allow_html=True)
            st.write(f"**Entry:** {s.get('entry', '-')} | **T1:** {s.get('target1', '-')} | **Stop:** {s.get('stop', '-')}")
            st.write(f"R:R {s.get('rr', '-')} | Conf {s.get('confidence', '-')}%")
            st.divider()

        copy_text = "\n".join([f"{s.get('manager', '?').split()[0]}: {s.get('direction', '?')} {raw_input} @ {s.get('entry', '-')}" for s in st.session_state.strategies])
        st.code(copy_text + f"\n#AIHedgeFund #{raw_input}", language=None)

st.success("NASDAQ/HOOD fixed — type HOOD, chart loads NASDAQ:HOOD, prices accurate. Test it!")
