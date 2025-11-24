import streamlit as st
import requests
import json

st.set_page_config(page_title="AI Hedge Fund Agent", layout="wide")
st.title("AI Hedge Fund Agent – Multi-Strategy Pro Edition")

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
st.sidebar.success("OpenAI key loaded")

# Symbol & timeframe (TradingView format)
symbol_map = {"NVDA":"NASDAQ:NVDA","SPY":"NYSE:SPY","QQQ":"NASDAQ:QQQ","AAPL":"NASDAQ:AAPL","TSLA":"NASDAQ:TSLA","BTC":"BINANCE:BTCUSDT"}
name = st.sidebar.selectbox("Symbol", list(symbol_map.keys()), index=0)
symbol = symbol_map[name]
interval = st.sidebar.selectbox("Timeframe", ["5","15","60"], index=0)

# TradingView chart
st.components.v1.html(f"""
<div class="tradingview-widget-container" style="height:660px;width:100%">
  <div id="tvchart"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
  new TradingView.widget({{
    "width": "100%",
    "height": 660,
    "symbol": "{symbol}",
    "interval": "{interval}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "studies": ["RSI@tv-basicstudies","MACD@tv-basicstudies","Volume@tv-basicstudies"],
    "container_id": "tvchart"
  }});
  </script>
</div>
""", height=680)

# MULTI-STRATEGY AI ENGINE
def get_strategies():
    prompt = f"""You are a $10B hedge fund desk (citadel + millennium level).

Analyze {name} on the {interval}-minute chart RIGHT NOW.

Detect the exact setup you see (e.g. bull flag, cup & handle, VWAP reclaim, gamma flip breakout, consolidation breakout, double bottom, etc.).

Give me 3 different professional trade ideas with:
- Strategy name
- Pattern recognized
- Direction (long/short)
- Exact entry price or zone
- Target 1 / Target 2
- Stop loss
- Risk/reward ratio
- Confidence %

Return ONLY valid JSON like this (no markdown):
[
  {{"name":"Aggressive Breakout","pattern":"Bull Flag","direction":"long","entry":"$194.80 – $195.00","target1":"$198","target2":"$202","stop":"$193.50","rr":"3.4:1","confidence":94}},
  {{"name":"Conservative Pullback","pattern":"VWAP Reclaim","direction":"long","entry":"$193.20","target1":"$196.50","target2":"$200","stop":"$191.80","rr":"4.1:1","confidence":88}},
  {{"name":"Scalp Fade","pattern":"Overbought Rejection","direction":"short","entry":"$195.50","target1":"$194","target2":"$192.50","stop":"$196.80","rr":"2.8:1","confidence":76}}
]
If no edge → return empty array []."""

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],
                  "temperature":0.1,"max_tokens":600},
            timeout=20)
        text = r.json()["choices"][0]["message"]["content"]
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except:
        return []

col1, col2 = st.columns([3,1])
with col2:
    st.markdown("### Multi-Strategy Desk")
    if st.button("ANALYZE CHART", type="primary", use_container_width=True):
        with st.spinner("Desk is live..."):
            strategies = get_strategies()
            st.session_state.strategies = strategies

    if "strategies" in st.session_state and st.session_state.strategies:
        for i, s in enumerate(st.session_state.strategies, 1):
            dir_emoji = "LONG" if s["direction"]=="long" else "SHORT"
            color = "#00ff00" if s["direction"]=="long" else "#ff0066"
            st.markdown(f"### {i}. **{dir_emoji} {s['name']}**")
            st.markdown(f"<p style='color:orange;'><b>{s['pattern']}</b></p>", unsafe_allow_html=True)
            st.write(f"**Entry:** {s['entry']}")
            st.write(f"**T1:** {s['target1']} | **T2:** {s['target2']}")
            st.write(f"**Stop:** {s['stop']} → R:R **{s['rr']}**")
            st.metric("Confidence", s["confidence"], f"{s['confidence']}%")
            st.divider()

        copy = "\n".join([f"{name} {s['direction'].upper()} | {s['name']} ({s['pattern']})\nEntry {s['entry']} → T1 {s['target1']} | Stop {s['stop']}" 
                          for s in st.session_state.strategies])
        st.code(copy + f"\n#AIHedgeFund #Trading", language=None)
    else:
        st.info("No high-conviction edge right now")

st.success("Multi-strategy version ready – this is the one that gets 1M+ views")
