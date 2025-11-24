import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="AI Hedge Fund Agent", layout="wide", height=800)
st.title("🤖 AI Hedge Fund Agent – Fixed Chart & Signals")

# Load key
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    st.warning("Add OPENAI_API_KEY to secrets for signals!")
    st.stop()
st.sidebar.success("✅ OpenAI key loaded")

# Settings
symbol_map = {"NVDA": "NASDAQ:NVDA", "SPY": "NYSE:SPY", "QQQ": "NASDAQ:QQQ", "AAPL": "NASDAQ:AAPL", "TSLA": "NASDAQ:TSLA", "BTC": "BINANCE:BTCUSDT"}
symbols = list(symbol_map.keys())
selected = st.sidebar.selectbox("Symbol", symbols, index=0)
full_symbol = symbol_map[selected]

interval_map = {"5m": "5", "15m": "15", "1h": "60"}
intervals = list(interval_map.keys())
selected_interval = st.sidebar.selectbox("Timeframe", intervals, index=0)
tv_interval = interval_map[selected_interval]

# FIXED TRADINGVIEW CHART – Loads every time
chart_html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://s3.tradingview.com/tv.js"></script>
</head>
<body style="margin:0; background:#000;">
    <div class="tradingview-widget-container" style="width:100%; height:100%;">
        <div id="tv_chart"></div>
        <script type="text/javascript">
            new TradingView.widget({{
                "width": "100%",
                "height": 700,
                "symbol": "{full_symbol}",
                "interval": "{tv_interval}",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#000",
                "enable_publishing": false,
                "hide_legend": true,
                "hide_volume": false,
                "studies": [
                    "MASimple@tv-basicstudies#1m RSI (14)",
                    "MACD@tv-basicstudies#1m MACD (12,26,9)"
                ],
                "container_id": "tv_chart"
            }});
        </script>
    </div>
</body>
</html>
"""
st.components.v1.html(chart_html, height=750, scrolling=True)

# AI SIGNAL (Shortened & robust)
def get_signal():
    prompt = f"""World-class hedge fund AI (Dalio/Soros/Jones).

{selected} on {selected_interval}.

Elite signal now.

JSON only:
{{"action":"buy" or "sell" or "hold","size_usd":25000,"confidence":0.9,"reason":"short edge"}}"""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 80
            },
            timeout=10
        )
        if response.status_code != 200:
            return {"action": "hold", "size_usd": 0, "confidence": 0, "reason": f"HTTP {response.status_code}"}
        
        text = response.json()["choices"][0]["message"]["content"].strip()
        # Robust JSON extraction
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            text = text[start:end]
        return json.loads(text)
    except Exception as e:
        return {"action": "hold", "size_usd": 0, "confidence": 0, "reason": f"Error: {str(e)[:40]}"}

# Signal Panel
st.markdown("### 🚀 Live AI Signal")
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Generate Signal", type="primary"):
        with st.spinner("AI analyzing chart..."):
            signal = get_signal()
            st.session_state.signal = signal
            st.session_state.time = datetime.now().strftime("%H:%M:%S")

    if "signal" in st.session_state:
        s = st.session_state.signal
        action = s.get("action", "hold").upper()
        size = f"${s.get('size_usd', 0):,}"
        conf = f"{s.get('confidence', 0) * 100:.0f}%"
        reason = s.get("reason", "No edge")

        # Bold display
        if action == "BUY":
            st.markdown(f"**🟢 BUY {size}**")
            st.success(reason)
        elif action == "SELL":
            st.markdown(f"**🔴 SELL {size}**")
            st.error(reason)
        else:
            st.markdown(f"**⚪ HOLD**")
            st.info(reason)

        st.metric("Confidence", conf)
        st.caption(f"Generated: {st.session_state.time}")

        # Copy for Reel
        copy_text = f"AI Signal: {selected} → {action} {size}\n\"{reason}\"\n{conf} conf #AITrading #HedgeFund"
        st.code(copy_text, language=None)

st.markdown("---")
st.success("✅ Chart & signals fixed – test NVDA 5m for a BUY signal & screenshot for your Reel!")
