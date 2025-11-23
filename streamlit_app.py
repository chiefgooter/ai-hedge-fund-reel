import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime
import time

st.set_page_config(page_title="AI Hedge Fund Agent", layout="wide")
st.title("AI Hedge Fund Agent (Exact Viral Reel – Fixed & Working)")

# Key loading (already working for you)
try:
    GROK_API_KEY = st.secrets["GROK_API_KEY"]
    st.sidebar.success("Key loaded from secrets!")
except:
    st.warning("No secrets found – using sidebar fallback")
    GROK_API_KEY = st.sidebar.text_input("Grok API Key", type="password")
    if not GROK_API_KEY.startswith("gsk_"):
        st.stop()

# Settings
symbol = st.sidebar.selectbox("Symbol", ["SPY","QQQ","AAPL","NVDA","TSLA","BTC-USD"], index=0)
interval = st.sidebar.selectbox("Timeframe", ["5m","15m","30m","1h"], index=0)
lookback = st.sidebar.slider("Candles", 30, 120, 80)

# FETCH DATA + FIX MultiIndex issue
@st.cache_data(ttl=60)
def get_data():
    df = yf.download(symbol, period="5d", interval=interval, progress=False)
    # ← THIS LINE FIXES THE ERROR
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1) if df.columns.nlevels > 1 else df
    df = df.dropna()
    return df

data = get_data()
if len(data) < 10:
    st.error("Not enough data – try a different symbol/timeframe")
    st.stop()

# AI DECISION
def get_ai_decision():
    csv_data = data.tail(lookback)[['Open','High','Low','Close','Volume']].round(4).to_csv()
    prompt = f"""You are Ray Dalio + Paul Tudor Jones + George Soros combined.

Symbol: {symbol} | Timeframe: {interval} | Current price: ${data['Close'].iloc[-1]:.2f}
Last {lookback} candles:
{csv_data}

Return ONLY valid JSON:
{{"action":"buy","size_usd":25000,"confidence":0.94,"reason":"one crisp sentence"}}
OR hold if no edge.
"""

    try:
        r = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROK_API_KEY}"},
            json={"model": "grok-beta", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2},
            timeout=25
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        return json.loads(content)
    except Exception as e:
        return {"action":"hold","size_usd":0,"confidence":0,"reason":f"Error: {str(e)[:80]}"}

# LAYOUT
col1, col2 = st.columns([2.2, 1])

with col1:
    fig = go.Figure(go.Candlestick(
        x=data.index[-200:],
        open=data['Open'][-200:], high=data['High'][-200:],
        low=data['Low'][-200:], close=data['Close'][-200:]
    ))
    fig.update_layout(height=680, xaxis_rangeslider_visible=False, title=f"{symbol} – {interval}")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Instant AI Signal")
    if st.button("Get Trade Signal", type="primary", use_container_width=True):
        with st.spinner("Grok is analyzing..."):
            decision = get_ai_decision()
            st.session_state.decision = decision
            st.session_state.time = datetime.now().strftime("%H:%M:%S")

    if "decision" in st.session_state:
        d = st.session_state.decision
        action = d.get("action", "hold").upper()
        color = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
        st.markdown(f"### {color} **{action} ${d.get('size_usd',0):,}**")
        st.metric("Confidence", f"{d.get('confidence',0)*100:.1f}%")
        st.success(d.get("reason","No reason returned"))
        st.caption(f"Generated at {st.session_state.time}")

        copy_text = f"AI Hedge Fund Live Signal\n{symbol} → {action} ${d.get('size_usd',0):,}\n\"{d.get('reason')}\"\n#AItrading #hedgefund"
        st.code(copy_text, language=None)

# Auto-refresh option
if st.sidebar.checkbox("Auto-refresh every 30s"):
    time.sleep(30)
    st.rerun()
