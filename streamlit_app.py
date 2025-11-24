import streamlit as st
import requests
import json

st.set_page_config(page_title="AI Hedge Fund Pod", layout="wide")
st.title("AI Hedge Fund Pod – 7 Legendary Managers Live")

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
st.sidebar.success("OpenAI key loaded")

symbol_map = {"NVDA":"NASDAQ:NVDA","SPY":"NYSE:SPY","QQQ":"NASDAQ:QQQ","AAPL":"NASDAQ:AAPL","TSLA":"NASDAQ:TSLA","BTC":"BINANCE:BTCUSDT"}
name = st.sidebar.selectbox("Symbol", list(symbol_map.keys()), index=0)
symbol = symbol_map[name]
interval = st.sidebar.selectbox("Timeframe", ["5","15","60"], index=0)

# TradingView chart
st.components.v1½.html(f"""
<div style="height:680px;width:100%">
  <div id="tv"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
  new TradingView.widget({{
    "width": "100%", "height": 680, "symbol": "{symbol}", "interval": "{interval}",
    "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "en",
    "studies": ["RSI@tv-basicstudies","MACD@tv-basicstudies","Volume@tv-basicstudies"],
    "container_id": "tv"
  }});
  </script>
</div>
""", height=700)

# MULTI-MANAGER POD ENGINE
def get_pod_strategies():
    prompt = f"""You are a $500B multi-strategy hedge fund pod with 7 legendary PMs live right now analyzing {name} on the {interval}-minute chart.

Respond as each PM giving ONE elite trade idea with:
- Manager name + style
- Exact pattern/setup they see
- Direction (Long/Short)
- Entry zone
- Target(s)
- Stop
- R:R
- Confidence

PMs:
1. Cathie Wood (ARK) – disruptive innovation
2. Warren Buffett – value & moat
3. Ray Dalio – macro / risk-parity
4. Paul Tudor Jones – macro momentum & tape reading
5. RenTech / DE Shaw – pure quant/stat-arb
6. JPM / Goldman prop desk – order flow & gamma
7. UBS wealth desk – high-conviction swing

Return ONLY valid JSON array (no extra text):
[
  {{"manager":"Cathie Wood (ARK)","setup":"Breakout to new highs on volume","direction":"Long","entry":"$195–$196","target1":"$210","target2":"$230","stop":"$190","rr":"4.2:1","confidence":96}},
  ...
]"""

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model":"gpt-4o","messages":[{"role":"user","content":prompt}],
                  "temperature":0.3,"max_tokens":1200},
            timeout=25)
        text = r.json()["choices"][0]["message"]["content"]
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        return [{"manager":"Error","setup":str(e),"direction":"Hold","entry":"-","target1":"-","target2":"-","stop":"-","rr":"-","confidence":0}]

# Display
col1, col2 = st.columns([3,1])
with col2:
    st.markdown("### Hedge Fund Pod Live")
    if st.button("ANALYZE WITH 7 MANAGERS", type="primary", use_container_width=True):
        with st.spinner("Pod is live..."):
            st.session_state.pod = get_pod_strategies()

    if "pod" in st.session_state:
        for s in st.session_state.pod:
            color = "#00ff00" if "Long" in s["direction"] else "#ff0066"
            st.markdown(f"### {s['manager']}")
            st.markdown(f"<p style='color:{color};font-size:18px'><b>{s['direction']} – {s['setup']}</b></p>", unsafe_allow_html=True)
            st.write(f"**Entry:** {s['entry']} → **T1:** {s['target1']} | **T2:** {s['target2'] or '-'}")
            st.write(f"**Stop:** {s['stop']} → **R:R {s['rr']}**")
            st.metric("Confidence", f"{s['confidence']}%")
            st.divider()

        # One-click copy for Reels
        copy = "\n".join([f"{s['manager'].split(' ')[0]}: {s['direction']} {name} {s['entry']} → {s['target1']} (R:R {s['rr']})" for s in st.session_state.pod])
        st.code(copy + "\n#AIHedgeFund #CathieWood #Buffett", language=None)

st.success("7-manager pod version deployed – this is the most viral trading tool on earth right now")
