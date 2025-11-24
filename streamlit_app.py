import streamlit as st
from datetime import datetime
import requests
import json

st.set_page_config(page_title="AI Hedge Fund Agent", layout="wide")
st.title("AI Hedge Fund Agent – TradingView Edition")

# Your OpenAI key (already in secrets)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
st.sidebar.success("OpenAI key loaded")

symbol = st.sidebar.selectbox("Symbol", ["NASDAQ:NVDA", "SP:SPX", "NASDAQ:QQQ", "NYSE:SPY", "NASDAQ:AAPL", "NASDAQ:TSLA"], index=0)
interval = st.sidebar.selectbox("Timeframe", ["5", "15", "60"], help="Minutes", index=0)

# ——— TRADINGVIEW CHART (looks PRO) ———
st.markdown(f"""
<div class="tradingview-widget-container" style="height: 660px;">
  <div id="tradingview_chart"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "width": "100%",
    "height": 640,
    "symbol": "{symbol}",
    "interval": "{interval}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": false,
    "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
""", unsafe_allow_html=True)

# ——— AI SIGNAL ENGINE ———
def get_signal():
    prompt = f"""You are Ray Dalio + Paul Tudor Jones + George Soros.

{symbol.split(":")[1]} on {interval}min chart right now.

Give me one elite trade signal.

Return ONLY valid JSON:
{{
  "action": "buy" or "sell" or "hold",
  "size_usd": 25000,
  "confidence": 0.94,
  "reason": "one powerful sentence"
}}"""

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 120
            },
            timeout=12
        )
        text = r.json()["choices"][0]["message"]["content"]
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        return {"action":"hold","size_usd":0,"confidence":0,"reason":f"API error"}

# ——— SIGNAL PANEL ———
col_left, col_right = st.columns([1.8, 1.2])

with col_right:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)  # spacing
    if st.button("GET LIVE SIGNAL", type="primary", use_container_width=True):
        with st.spinner("Thinking like a $100B fund..."):
            signal = get_signal()
            st.session_state.signal = signal

    if "signal" in st.session_state:
        s = st.session_state.signal
        action = s["action"].upper()
        size = f"${s['size_usd']:,}"
        conf = f"{s['confidence']*100:.0f}%"

        if action == "BUY":
            st.markdown(f"<h1 style='color:#00ff00;'>BUY {size}</h1>", unsafe_allow_html=True)
            st.success(s["reason"])
        elif action == "SELL":
            st.markdown(f"<h1 style='color:#ff0066;'>SELL {size}</h1>", unsafe_allow_html=True)
            st.error(s["reason"])
        else:
            st.markdown(f"<h2 style='color:#888;'>HOLD {size}</h2>", unsafe_allow_html=True)
            st.info(s["reason"])

        st.metric("Confidence", conf)
        st.code(f"{symbol.split(':')[1]} → {action} {size}\n\"{s['reason']}\"\n#AIHedgeFund #Trading", language=None)

# Footer
st.markdown("---")
st.markdown("**This is the exact look that’s going viral on Instagram right now**")
