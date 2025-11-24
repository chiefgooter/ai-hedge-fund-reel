import streamlit as st
import requests
import json

st.set_page_config(page_title="AI Hedge Fund Pod", layout="wide")
st.title("AI Hedge Fund Pod — 7 Legendary Managers Live")

# Your OpenAI key (already in secrets)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
st.sidebar.success("OpenAI key loaded")

# FREE TEXT SYMBOL INPUT — Type anything!
user_symbol = st.sidebar.text_input("Enter Symbol (e.g. NVDA, TSLA, BTCUSD, AAPL)", value="NVDA").upper()

# Auto-detect exchange prefix
if user_symbol.endswith("USD") or user_symbol in ["BTC", "ETH", "SOL"]:
    symbol = f"BINANCE:{user_symbol}T" if not user_symbol.startswith("BINANCE:") else user_symbol
elif len(user_symbol) <= 4 and user_symbol.isalpha():
    symbol = f"NASDAQ:{user_symbol}"  # default to NASDAQ for short tickers
    if user_symbol in ["SPY", "DIA", "IWM"]:
        symbol = f"NYSE:{user_symbol}"
else:
    symbol = user_symbol  # allow full format like NASDAQ:NVDA

interval = st.sidebar.selectbox("Timeframe (minutes)", ["5", "15", "60"], index=0)

# TradingView Chart — ANY SYMBOL
st.components.v1.html(f"""
<div style="height:680px; width:100%;">
  <div id="tv_chart"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
  new TradingView.widget({{
    "width": "100%",
    "height": 680,
    "symbol": "{symbol}",
    "interval": "{interval}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#000",
    "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "Volume@tv-basicstudies"],
    "container_id": "tv_chart"
  }});
  </script>
</div>
""", height=700)

# 7-MANAGER HEDGE FUND POD
def get_pod_analysis():
    prompt = f"""You are a $500B multi-strategy hedge fund with 7 legendary portfolio managers analyzing {user_symbol} on the {interval}-minute chart RIGHT NOW.

Each manager gives ONE high-conviction trade idea based on their style.

Managers & styles:
1. Cathie Wood (ARK) – disruptive tech & moonshots
2. Warren Buffett – deep value & economic moat
3. Ray Dalio – macro cycles & risk-parity
4. Paul Tudor Jones – momentum & tape reading
5. Jim Simons (RenTech) – pure quant/statistical edge
6. JPMorgan Prop Desk – order flow & gamma positioning
7. UBS Wealth – high-conviction structural swing

Return ONLY valid JSON array (no extra text, no markdown):
[
  {{"manager":"Cathie Wood (ARK)","style":"Disruptive Growth","direction":"Long","setup":"Breakout on volume","entry":"$194.50–$195.20","target1":"$205","target2":"$220","stop":"$191","rr":"4.8:1","confidence":96}},
  {{"manager":"Warren Buffett","style":"Value & Moat","direction":"Long","setup":"Trading below intrinsic value","entry":"Current levels","target1":"$240","target2":"$280","stop":"$175","rr":"6:1","confidence":92}},
  ...
]
Always return 7 ideas. If no edge from one manager, say "No position" with direction "Hold"."""

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 1400
            },
            timeout=30)
        if r.status_code != 200:
            return [{"manager": "API Error", "direction": "Hold", "setup": f"HTTP {r.status_code}", "entry": "-", "target1": "-", "stop": "-", "rr": "-", "confidence": 0}]
        text = r.json()["choices"][0]["message"]["content"].strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return [{"manager": "Error", "direction": "Hold", "setup": str(e)[:100], "entry": "-", "target1": "-", "stop": "-", "rr": "-", "confidence": 0}]

# Display Panel
col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("### Live Pod Analysis")
    if st.button("ANALYZE WITH 7 MANAGERS", type="primary", use_container_width=True):
        with st.spinner("7 legends are analyzing..."):
            st.session_state.pod = get_pod_analysis()

    if "pod" in st.session_state:
        for s in st.session_state.pod:
            color = "#00ff88" if "Long" in s.get("direction", "") else "#ff0066" if "Short" in s.get("direction", "") else "#888888"
            st.markdown(f"### {s.get('manager', 'Unknown')}")
            st.markdown(f"<p style='color:{color};font-size:19px'><b>{s.get('direction', 'Hold')} — {s.get('setup', 'No setup')}</b></p>", unsafe_allow_html=True)
            st.write(f"**Entry:** {s.get('entry', '-')}")
            st.write(f"**T1:** {s.get('target1', '-')} | **T2:** {s.get('target2', '-')} | **Stop:** {s.get('stop', '-')}")
            st.write(f"**R:R:** {s.get('rr', '-')} | Confidence: **{s.get('confidence', 0)}%**")
            st.divider()

        # Copy for Reels
        copy_text = "\n".join([f"{s.get('manager','?').split(' ')[0]}: {s.get('direction','?')} {user_symbol} @ {s.get('entry','?')} → {s.get('target1','?')}" for s in st.session_state.pod])
        st.code(copy_text + f"\n#AIHedgeFund #CathieWood #Buffett #{user_symbol}", language=None)

st.success("Now supports ANY symbol + 7-manager pod always delivers — this is the viral beast")
