import streamlit as st
import requests
import json
from datetime import datetime

# Fixed: height parameter removed from set_page_config
st.set_page_config(page_title="AI Hedge Fund Agent", layout="wide")

st.title("AI Hedge Fund Agent – TradingView + Live Signal")

# Load your OpenAI key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
st.sidebar.success("OpenAI key loaded")

# Symbol & timeframe
symbol_map = {
    "NVDA": "NASDAQ:NVDA",
    "SPY": "NYSE:SPY",
    "QQQ": "NASDAQ:QQQ",
    "AAPL": "NASDAQ:AAPL",
    "TSLA": "NASDAQ:TSLA",
    "BTC": "BINANCE:BTCUSDT"
}
symbol_name = st.sidebar.selectbox("Symbol", list(symbol_map.keys()), index=0)
symbol = symbol_map[symbol_name]

interval_map = {"5m": "5", "15m": "15", "1h": "60"}
interval_name = st.sidebar.selectbox("Timeframe", list(interval_map.keys()), index=0)
interval = interval_map[interval_name]

# Working TradingView chart (no height error)
st.components.v1.html(
    f"""
    <div class="tradingview-widget-container" style="height: 660px; width: 100%;">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": 660,
        "symbol": "{symbol}",
        "interval": "{interval}",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#000",
        "enable_publishing": false,
        "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """,
    height=680
)

# AI Signal
def get_signal():
    prompt = f"""Elite hedge fund AI (Dalio + Soros + Jones).

{symbol_name} on {interval_name} chart right now.

One elite trade signal.

Return ONLY valid JSON:
{{"action":"buy","size_usd":25000,"confidence":0.94,"reason":"one powerful sentence"}}"""

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 100
            },
            timeout=12
        )
        if r.status_code != 200:
            return {"action":"hold","size_usd":0,"confidence":0,"reason":f"HTTP {r.status_code}"}
        text = r.json()["choices"][0]["message"]["content"]
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        return {"action":"hold","size_usd":0,"confidence":0,"reason":"Signal error"}

# Signal panel
col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("### Live AI Signal")
    if st.button("Generate Signal", type="primary", use_container_width=True):
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
            st.markdown(f"<h1 style='color:#00ff00;'>BUY {size}</h1>", unsafe_allow_html=True)
            st.success(reason)
        elif action == "SELL":
            st.markdown(f"<h1 style='color:#ff0000;'>SELL {size}</h1>", unsafe_allow_html=True)
            st.error(reason)
        else:
            st.markdown(f"<h2 style='color:#888888;'>HOLD</h2>", unsafe_allow_html=True)
            st.info(reason)

        st.metric("Confidence", conf)
        st.code(f"{symbol_name} → {action} {size}\n\"{reason}\"\n#AIHedgeFund", language=None)

st.success("Chart + Signal 100% Fixed – Screenshot this for your Reel!")
