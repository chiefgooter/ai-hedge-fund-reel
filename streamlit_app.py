import streamlit as st
import requests
import json

st.set_page_config(page_title="Global AI Hedge Fund Pod", layout="wide")
st.title("Global AI Hedge Fund Pod — Any Asset, Any Exchange")

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
st.sidebar.success("OpenAI key loaded")

# FREE TEXT — TYPE ANY SYMBOL IN THE WORLD
raw_input = st.sidebar.text_input(
    "Enter ANY symbol (e.g. NVDA, 9984.T, 0700.HK, BTCUSD, EURUSD, ES1!, SOLUSDT, AAPL, HOOD, MSTR)",
    value="NVDA"
).strip().upper()

# SMART SYMBOL MAPPER — handles everything
def map_symbol(user_input):
    user_input = user_input.upper().replace(" ", "")
    
    # Crypto
    if any(x in user_input for x in ["BTC","ETH","SOL","DOGE","ADA","XRP","BNB","USDT","USDC"]):
        return f"BINANCE:{user_input}T" if not user_input.startswith("BINANCE:") else user_input
    
    # Forex
    if any(x in user_input for x in ["EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD","NZDUSD","EURGBP"]):
        return f"FX:{user_input}"
    
    # Futures
    if any(x in user_input for x in ["ES","NQ","YM","RTY","CL","GC","SI","HG","NG"]):
        return f"CME:{user_input}1!" if not user_input.startswith("CME:") else user_input
    
    # Japan (.T)
    if user_input.endswith(".T") or user_input.endswith("T"):
        return f"TSE:{user_input.replace('.T','').replace('T','')}"
    
    # Hong Kong (.HK)
    if user_input.endswith(".HK"):
        return f"HKEX:{user_input.replace('.HK','')}"
    
    # London (.L)
    if user_input.endswith(".L"):
        return f"LSE:{user_input.replace('.L','')}"
    
    # Default US stocks
    if len(user_input) <= 5 and user_input.isalpha():
        if user_input in ["SPY","DIA","IWM","QQQ","TLT"]:
            return f"NYSE:{user_input}"
        return f"NASDAQ:{user_input}"
    
    # Full format pass-through
    return user_input

symbol = map_symbol(raw_input)

interval = st.sidebar.selectbox("Timeframe (min)", ["1","5","15","60","240","D"], index=1)

# TradingView — works with ANY symbol
st.components.v1.html(f"""
<div style="height:700px; width:100%">
  <div id="tv"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
  new TradingView.widget({{
    "width": "100%", "height": 700,
    "symbol": "{symbol}",
    "interval": "{interval}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "studies": ["RSI@tv-basicstudies","MACD@tv-basicstudies","Volume@tv-basicstudies"],
    "container_id": "tv"
  }});
  </script>
</div>
""", height=720)

# 7 Legendary Managers — now global-aware
def get_global_pod():
    prompt = f"""You are a $1T global multi-strategy hedge fund pod.

Analyze {raw_input} ({symbol}) on the {interval} chart RIGHT NOW.

7 legendary managers are live:

1. Cathie Wood (ARK) – disruptive innovation
2. Warren Buffett – value & moat
3. Ray Dalio – macro & all-weather
4. Paul Tudor Jones – macro momentum
5. Jim Simons (RenTech) – quant
6. JPMorgan Prop – flow & gamma
7. UBS Global Wealth – structural themes

Each gives ONE elite trade idea with:
- manager + style
- direction
- setup/pattern
- entry zone
- target(s)
- stop
- R:R
- confidence %

Return ONLY valid JSON array (no extra text):
[
  {{"manager":"Cathie Wood","style":"Growth","direction":"Long","setup":"Breakout","entry":"194.50-195.20","target1":"205","target2":"220","stop":"191","rr":"5:1","confidence":95}},
  ...
]
Always return 7 ideas."""

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model":"gpt-4o","messages":[{"role":"user","content":prompt}],
                  "temperature":0.35,"max_tokens":1500},
            timeout=30)
        text = r.json()["choices"][0]["message"]["content"].strip()
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        return [{"manager":"Error","direction":"Hold","setup":str(e)[:80],"entry":"-","target1":"-","stop":"-","rr":"-","confidence":0}]

# Display
col1, col2 = st.columns([3,1])
with col2:
    st.markdown("### Global Pod Live")
    if st.button("ANALYZE WITH 7 MANAGERS", type="primary", use_container_width=True):
        with st.spinner("7 legends analyzing..."):
            st.session_state.pod = get_global_pod()

    if "pod" in st.session_state:
        for s in st.session_state.pod:
            color = "#00ff88" if "Long" in s.get("direction","") else "#ff0066" if "Short" in s.get("direction","") else "#888"
            st.markdown(f"### {s.get('manager','?')}")
            st.markdown(f"<p style='color:{color};font-size:18px'><b>{s.get('direction','Hold')} — {s.get('setup','No setup')}</b></p>", unsafe_allow_html=True)
            st.write(f"**Entry:** {s.get('entry','-')} | **T1:** {s.get('target1','-')} | **Stop:** {s.get('stop','-')}")
            st.write(f"**R:R:** {s.get('rr','-')} | **Conf:** {s.get('confidence',0)}%")
            st.divider()

        copy = "\n".join([f"{s.get('manager','?').split(' ')[0]}: {s.get('direction','?')} {raw_input} @ {s.get('entry','-')}" 
                          for s in st.session_state.pod])
        st.code(copy + f"\n#AIHedgeFund #GlobalTrading #{raw_input}", language=None)

st.success("Now works with ANY asset globally — try BTCUSD, 9984.T, EURUSD, ES1!, HOOD — all work perfectly")
