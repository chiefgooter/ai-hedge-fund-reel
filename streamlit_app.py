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

# Grok key is safely in secrets – never exposed
GROK_API_KEY = st.secrets["GROK_API_KEY"]

symbol = st.sidebar.selectbox("Symbol", ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "BTC-USD", "IWM", "GLD"], index=0)
interval = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h"], index=0)
lookback = st.sidebar.slider("Candles to analyze", 30, 150, 80)

@st.cache_data(ttl=60)
def get_data():
    return yf.download(symbol, period="5d", interval=interval, progress=False)

data = get_data()
if data.empty:
    st.error("No data – try again in a few seconds")
    st.stop()

def get_ai_decision():
    csv_data = data.tail(lookback)[['Open','High','Low','Close','Volume']].round(4).to_csv()
    prompt = f"""
You are an elite hedge-fund team combining Ray Dalio, Paul Tudor Jones, and George Soros.

Symbol: {symbol} | Timeframe: {interval} | Price: ${data['Close'].iloc[-1]:.2f}
Last {lookback} candles:
{csv_data}

Return ONLY valid JSON:
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
        content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"action": "hold", "size_usd": 0, "confidence": 0, "reason": f"API error: {str(e)}"}

col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'], high=data['High'],
                                         low=data['Low'], close=data['Close'])])
    fig.update_layout(height=650, title=f"{symbol} Live Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🚀 Instant AI Signal")
    if st.button("Get Trade Recommendation", type="primary", use_container_width=True):
        with st.spinner("Thinking like Dalio + Soros + Jones..."):
            decision = get_ai_decision()
            st.session_state.decision = decision
            st.session_state.time = datetime.now().strftime("%H:%M:%S")

    if "decision" in st.session_state:
        d = st.session_state.decision
        st.markdown(f"### **{d['action'].upper()} ${d['size_usd']:,}**")
        st.metric("Confidence", f"{d['confidence']*100:.1f}%")
        st.success(d['reason'])
        st.caption(f"Generated at {st.session_state.time}")

        copy_text = f"AI Hedge Fund Signal\n{symbol} → {d['action'].upper()} ${d['size_usd']:,}\n\"{d['reason']}\"\n#{symbol.replace('-','')} #AItrading #hedgefund"
        st.code(copy_text, language=None)

if st.checkbox("Auto-refresh every 30s"):
    time.sleep(30)
    st.rerun()
