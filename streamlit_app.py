import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import ssl

# --- SSL FIX ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- Modern Page Setup ---
st.set_page_config(page_title="🔥 Stock Roaster", layout="wide")

# --- Custom CSS for Modern Look ---
st.markdown("""
    <style>
    /* Background gradient */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
        font-family: 'Poppins', sans-serif;
    }

    /* Title styling */
    .title {
        font-size: 3em;
        text-align: center;
        background: linear-gradient(90deg, #ff4b4b, #ff9966);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.3em;
    }

    /* Caption */
    .caption {
        text-align: center;
        color: #ddd;
        margin-bottom: 2em;
        font-size: 1.1em;
    }

    /* Input card */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 25px rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.15);
        margin-bottom: 2em;
    }

    /* Roast box */
    .roast-box {
        background: rgba(255, 77, 77, 0.12);
        border: 1px solid #ff4b4b;
        padding: 25px;
        border-radius: 20px;
        font-size: 1.1em;
        color: #fff;
        box-shadow: 0 4px 25px rgba(255, 75, 75, 0.2);
    }

    /* Button style */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #ff4b4b, #ff9966);
        color: white;
        border: none;
        padding: 0.7em 1.5em;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.1em;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: scale(1.03);
        background: linear-gradient(90deg, #ff9966, #ff4b4b);
    }

    /* Chart section */
    .chart-container {
        background: rgba(255,255,255,0.08);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Stats section */
    .stats {
        background: rgba(255,255,255,0.06);
        border-radius: 15px;
        padding: 15px 25px;
        margin-top: 20px;
        color: #eee;
        border-left: 5px solid #ff4b4b;
    }

    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<div class='title'>🔥 Stock Roaster</div>", unsafe_allow_html=True)
st.markdown("<div class='caption'>Enter a ticker and let AI roast it based on its performance and industry trends 😎</div>", unsafe_allow_html=True)

# --- Gemini API Key ---
def get_gemini_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_key()

if not GEMINI_API_KEY:
    st.warning("🚨 Gemini API key not found. Please set GEMINI_API_KEY in environment or Streamlit secrets.")
    st.stop()

# --- Input Section ---
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    ticker = st.text_input("📈 Ticker Symbol", value="AAPL").strip().upper()

with col2:
    period = st.selectbox("🕒 Period", ["1mo", "3mo", "6mo"], index=0)

with col3:
    tone = st.selectbox("🎭 Tone", ["Savage", "Playful", "Dry"], index=0)

st.info("⚠️ For entertainment only. Not financial advice.")
st.markdown("</div>", unsafe_allow_html=True)

# --- Roast Button ---
roast = st.button("🎤 Roast It!")

if roast:
    if not ticker:
        st.error("Please enter a ticker symbol.")
        st.stop()

    with st.spinner("Fetching stock data & cooking your roast... 🍳"):
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period, interval="1d")
            info = t.info

            if hist.empty:
                st.error(f"❌ No data for {ticker}. Try another or include .NS for Indian stocks.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
            st.stop()

        # --- Stats ---
        last_close = float(hist["Close"].iloc[-1])
        first_close = float(hist["Close"].iloc[0])
        pct_change = ((last_close - first_close) / first_close) * 100
        mean_vol = int(hist["Volume"].mean()) if "Volume" in hist.columns else None
        latest_date = hist.index[-1].strftime("%Y-%m-%d")

        company_name = info.get("shortName", ticker)
        sector = info.get("sector", "Unknown Sector")
        industry = info.get("industry", "Unknown Industry")
        market_cap = info.get("marketCap", None)
        market_cap_str = f"{market_cap/1e9:.2f}B" if market_cap else "N/A"

        summary = (
            f"Company: {company_name}\n"
            f"Ticker: {ticker}\n"
            f"Sector: {sector}\n"
            f"Industry: {industry}\n"
            f"Market Cap: {market_cap_str}\n"
            f"Latest close: {last_close:.2f}\n"
            f"Period: {period}\n"
            f"Period change: {pct_change:.2f}%\n"
            f"Latest date: {latest_date}\n"
        )
        if mean_vol:
            summary += f"Average daily volume: {mean_vol}\n"

        roast_styles = {
            "Savage": "Make it brutally savage, darkly funny, and use clever finance/industry references.",
            "Playful": "Make it light-hearted, witty, and sprinkle finance-related humor.",
            "Dry": "Make it sarcastic, short, and deadpan funny."
        }

        prompt = f"""
You are a finance roast comedian.
Roast the company below based on its stock performance, sector, and industry.

Rules:
- Write 3 distinct one-liners.
- Include emojis and viral tweet-like humor.
- Avoid any sensitive or financial advice.

Tone: {roast_styles[tone]}

DATA:
{summary}

Now roast them:
"""

        try:
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                params={"key": GEMINI_API_KEY},
                timeout=30
            )

            if response.status_code != 200:
                st.error(f"❌ Gemini API Error: {response.status_code} - {response.text}")
                st.stop()

            data = response.json()
            roast_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        except Exception as e:
            st.error(f"❌ Gemini API Error: {e}")
            st.stop()

        # --- Roast Display ---
        st.markdown("<h3 style='text-align:center;'>🔥 The Roast Wall 🔥</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='roast-box'>{roast_text}</div>", unsafe_allow_html=True)

        # --- Chart Section ---
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("📊 Price Chart")
        st.line_chart(hist["Close"])
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Quick Stats ---
        st.markdown("<div class='stats'>", unsafe_allow_html=True)
        color = "#00ff88" if pct_change >= 0 else "#ff4b4b"
        st.markdown(
            f"""
            **Company:** {company_name}  
            **Sector:** {sector}  
            **Industry:** {industry}  
            **Market Cap:** {market_cap_str}  
            **{period} Change:** <span style='color:{color}; font-weight:bold;'>{pct_change:+.2f}%</span>  
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("🧠 Raw Data"):
            st.write(hist.tail(10))
