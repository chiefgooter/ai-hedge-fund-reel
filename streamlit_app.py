import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime
import time

st.set_page_config(page_title="AI Hedge Fund Agent – Reel Edition", layout="wide")
st.title("🤖 AI Hedge Fund Agent (Exact Viral Reel – No Trading)")

# SAFE KEY LOADING: Tries secrets first, then sidebar input (fallback for deployment)
try:
    GROK_API_KEY = st.secrets["GROK_API_KEY"]
    st.sidebar.success("✅ Key loaded from secrets!")
except:
    GROK_API_KEY = st.sidebar.text_input("Grok API Key (x.ai)", type="password", help="Paste your key here if secrets fail")
    if not GROK_API_KEY:
        st.warning("👆 Add your Grok API key in the sidebar to get signals!")
        st.stop()

# SETTINGS
symbol = st.sidebar.selectbox("Symbol", ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "BTC-USD", "IWM", "GLD"], index=0)
interval = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h"], index=0)
lookback = st.sidebar.slider("Candles to analyze", 30, 150, 80)

# FETCH DATA
@st.cache_data(ttl=60)  # Refresh max once per minute
def get_data():
    return yf.download(symbol, period="5d", interval=interval, progress=False)

data = get_data()
if data.empty:
    st.error("No data – check symbol or try again")
    st.stop()

# AI BRAIN
def get_ai_decision():
    csv_data = data.tail(lookback)[['Open','High','Low','Close','Volume']].round(4).to_csv()

    prompt = f"""
You are an elite hedge-fund team combining Ray Dalio (risk-parity), Paul Tudor Jones (macro momentum), and George Soros (reflexivity).

Symbol: {symbol} | Timeframe: {interval} | Current price: ${data['Close'].iloc[-1]:.2f}
Last {lookback} candles:
{csv_data}

Return ONLY valid JSON – nothing else:
{{
  "action": "buy" | "sell" | "hold",
  "size_usd": 25000,
  "confidence": 0.94,
  "reason": "one crisp sentence explaining the exact edge right now"
}}
"""

    try:
        r = requests.post("https://api.x.ai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                          json={"model": "grok-beta", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2},
                          timeout=25)
        r.raise_for_status()  # Raise error on bad response
        content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"action": "hold", "size_usd": 0, "confidence": 0, "reason": f"API error: {str(e)[:100]}..."}

# MAIN UI
col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'], high=data['High'],
                                 low=data['Low'], close=data['Close']))
    fig.update_layout(height=650, title=f"{symbol} – Live Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🚀 AI Decision Engine")
    if st.button("Get Latest Trade Signal", type="primary", use_container_width=True):
        with st.spinner("Grok is thinking like Dalio + Soros + Jones..."):
            decision = get_ai_decision()
            st.session_state.last_decision = decision
            st.session_state.last_time = datetime.now().strftime("%H:%M:%S")

    if 'last_decision' in st.session_state:
        d = st.session_state.last_decision
        st.markdown(f"### **{d['action'].upper()}**")
        st.metric("Size", f"${d['size_usd']:,}")
        st.metric("Confidence", f"{d['confidence']*100:.1f}%")
        st.success(d['reason'])
        st.caption(f"Generated at {st.session_state.last_time}")

        # Copy-paste for socials
        copy_text = f"AI Hedge Fund Signal\n{symbol} → {d['action'].upper()} ${d['size_usd']:,}\n\"{d['reason']}\"\nConfidence {d['confidence']*100:.0f}%\n#AItrading #hedgefund"
        st.code(copy_text, language=None)

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh every 30 seconds"):
    time.sleep(30)
    st.rerun()
