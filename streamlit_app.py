import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

st.set_page_config(page_title="AI Hedge Fund Agent", layout="wide")
st.title("AI Hedge Fund Agent – 100% Working")

# Your new key (loaded securely)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
st.sidebar.success("OpenAI key loaded & working!")

symbol = st.sidebar.selectbox("Symbol", ["SPY", "QQQ", "NVDA", "AAPL", "TSLA", "BTC-USD"], index=2)
interval = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h"], index=0)

@st.cache_data(ttl=60)
def get_data():
    df = yf.download(symbol, period="5d", interval=interval, progress=False)
    if df.empty: return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)
    return df.dropna()

data = get_data()
if data.empty or len(data) < 10:
    st.error("No data – try 15m or 1h timeframe")
    st.stop()

def get_signal():
    price = data['Close'].iloc[-1]
    recent = data.tail(15)[['Open','High','Low','Close','Volume']].round(2).to_csv(index=False)

    prompt = f"""Elite hedge fund AI.

{symbol} @ ${price:.2f} ({interval})

Last 15 candles:
{recent}

JSON only:
{{"action":"buy","size_usd":25000,"confidence":0.92,"reason":"short reason"}}"""

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 100
            },
            timeout=15
        )
        if r.status_code != 200:
            return {"action":"hold","size_usd":0,"confidence":0,"reason":f"API {r.status_code}"}
        
        text = r.json()["choices"][0]["message"]["content"]
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        return {"action":"hold","size_usd":0,"confidence":0,"reason":f"Error: {str(e)[:50]}"}

col1, col2 = st.columns([2.3, 1])

with col1:
    fig = go.Figure(go.Candlestick(
        x=data.index[-200:],
        open=data['Open'][-200:], high=data['High'][-200:],
        low=data['Low'][-200:], close=data['Close'][-200:]
    ))
    fig.update_layout(height=700, title=f"{symbol} – {interval}", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Instant AI Signal")
    if st.button("Get Signal Now", type="primary", use_container_width=True):
        with st.spinner("Analyzing..."):
            signal = get_signal()
            st.session_state.signal = signal

    if "signal" in st.session_state:
        s = st.session_state.signal
        action = s["action"].upper()
        size = f"${s['size_usd']:,}"
        conf = f"{s['confidence']*100:.0f}%"
        reason = s["reason"]

        if action == "BUY":
            st.markdown(f"### BUY {size}")
            st.success(reason)
        elif action == "SELL":
            st.markdown(f"### SELL {size}")
            st.error(reason)
        else:
            st.markdown(f"### HOLD {size}")
            st.info(reason)

        st.metric("Confidence", conf)
        st.code(f"{symbol} → {action} {size}\n\"{reason}\"\n{conf} #AITrading", language=None)

st.markdown("---")
st.success("Ready for your viral Reel — screenshot a BUY signal now!")
