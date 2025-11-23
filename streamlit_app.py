import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

st.set_page_config(page_title="AI Hedge Fund Agent", layout="wide")
st.title("AI Hedge Fund Agent – Live & Working")

# Your key (already in secrets – this line just reads it)
GROK_API_KEY = st.secrets["GROK_API_KEY"]
st.sidebar.success("Key loaded from secrets!")

symbol = st.sidebar.selectbox("Symbol", ["SPY","QQQ","NVDA","AAPL","TSLA","BTC-USD"], index=2)
interval = st.sidebar.selectbox("Timeframe", ["5m","15m","1h"], index=0)

@st.cache_data(ttl=60)
def get_data():
    df = yf.download(symbol, period="5d", interval=interval, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)
    return df.dropna()

data = get_data()

def get_signal():
    prompt = f"""You are a world-class hedge fund team (Dalio + Soros + Jones).

Symbol: {symbol}
Timeframe: {interval}
Current price: ${data['Close'].iloc[-1]:.2f}

Last 60 candles (OHLCV):
{data.tail(60)[['Open','High','Low','Close','Volume']].round(4).to_csv(index=True)}

Return ONLY this exact JSON (no extra text, no markdown):
{{
  "action": "buy" or "sell" or "hold",
  "size_usd": 25000,
  "confidence": 0.96,
  "reason": "one short sentence"
}}
"""

    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "grok-beta",
                "temperature": 0.1,
                "max_tokens": 200
            },
            timeout=20
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"].strip()
        # Clean any markdown or extra spaces
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"action":"hold","size_usd":0,"confidence":0,"reason":f"API error: {str(e)[:60]}"}

col1, col2 = st.columns([2.3, 1])

with col1:
    fig = go.Figure(go.Candlestick(
        x=data.index[-300:],
        open=data['Open'][-300:], high=data['High'][-300:],
        low=data['Low'][-300:], close=data['Close'][-300:]
    ))
    fig.update_layout(height=700, xaxis_rangeslider_visible=False, title=f"{symbol} – {interval}")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Instant AI Signal")
    if st.button("Get Trade Signal", type="primary", use_container_width=True):
        with st.spinner("Grok is thinking..."):
            signal = get_signal()
            st.session_state.signal = signal

    if "signal" in st.session_state:
        s = st.session_state.signal
        action = s["action"].upper()
        emoji = "BUY" if action == "BUY" else "SELL" if action == "SELL" else "HOLD"
        st.markdown(f"### {emoji} **{action} ${s['size_usd']:,}**")
        st.metric("Confidence", f"{s['confidence']*100:.1f}%")
        st.success(s["reason"])

        copy = f"AI Hedge Fund Signal\n{symbol} → {action} ${s['size_usd']:,}\n\"{s['reason']}\"\n#AItrading #hedgefund"
        st.code(copy, language=None)
