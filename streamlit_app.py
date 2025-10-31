import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import ssl

# --- SSL FIX ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- Page Setup ---
st.set_page_config(page_title="🔥 Stock Roaster", page_icon="🔥", layout="centered")

# --- Custom CSS for Modern UI ---
st.markdown("""
    <style>
    /* Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #f5f5f5;
        font-family: 'Inter', sans-serif;
    }

    /* Title Styling */
    .title {
        text-align: center;
        font-size: 3rem !important;
        font-weight: 800;
        color: #ff4b4b;
        text-shadow: 0 0 25px rgba(255,75,75,0.6);
        margin-bottom: 0;
    }

    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #cfcfcf;
        margin-top: 5px;
        margin-bottom: 40px;
    }

    /* Input Box */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 1px solid #555;
        background-color: #1e1e1e;
        color: white;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #ff4b4b, #ff8c00);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 12px;
        padding: 0.6em 1.2em;
        font-size: 1em;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(255, 120, 50, 0.7);
    }

    /* Roast Box */
    .roast-box {
        background-color: rgba(255,255,255,0.1);
        border: 2px solid #ff4b4b;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        color: #fff;
        font-size: 1.1rem;
        line-height: 1.6;
        box-shadow: 0 0 15px rgba(255,75,75,0.3);
    }

    /* Info Box */
    .info-box {
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 10px 15px;
        font-size: 0.9rem;
        color: #ccc;
        margin-bottom: 15px;
    }

    /* Chart + Stats section */
    .section-title {
        color: #ffd580;
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 20px;
    }

    /* Expander background */
    .streamlit-expanderHeader {
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1 class='title'>🔥 Stock Roaster</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Enter a stock ticker and get a funny AI roast based on its performance — for fun, not financial advice!</p>", unsafe_allow_html=True)

# --- Gemini API Key ---
def get_gemini_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_key()

if not GEMINI_API_KEY:
    st.warning("🚨 Gemini API key not found. Please set GEMINI_API_KEY in environment or Streamlit secrets.")
    st.stop()

# --- Input Area ---
with st.container():
    st.markdown("<div class='info-box'>💡 Tip: For Indian stocks, add <b>.NS</b> — e.g. RELIANCE.NS, TCS.NS</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("🎯 Ticker", value="AAPL").strip().upper()
    with col2:
        period = st.selectbox("⏱️ Period", ["1mo", "3mo", "6mo"], index=0)
    tone = st.radio("🎭 Roast Style", ["Savage", "Playful", "Dry"], index=0, horizontal=True)

# --- Action Button ---
if st.button("Roast it! 🎤"):
    if not ticker:
        st.error("Please enter a ticker symbol.")
        st.stop()

    with st.spinner("Cooking up your roast... 🍳"):
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
            "Savage": "Make it brutally savage, darkly funny, and clever with finance/industry puns.",
            "Playful": "Make it witty, light-hearted, and meme-worthy.",
            "Dry": "Make it sarcastic, short, and deadpan funny."
        }

        prompt = f"""
You are a finance roast comedian and market analyst.
Your goal is to roast the company below based on its stock performance, sector, and industry.

Instructions:
- Write **3 distinct one-liner roasts**.
- Each roast should feel like a viral tweet (use emojis).
- Avoid financial advice.
- Tone style: {roast_styles[tone]}

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
            roast_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            st.error(f"❌ Gemini API Error: {e}")
            st.stop()

        # --- Roast Wall ---
        st.markdown("<h3 class='section-title'>🔥 The Roast Wall 🔥</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='roast-box'>{roast_text}</div>", unsafe_allow_html=True)

        # --- Chart & Stats ---
        st.markdown("<h3 class='section-title'>📊 Price Chart</h3>", unsafe_allow_html=True)
        st.line_chart(hist["Close"])

        st.markdown("<h3 class='section-title'>📈 Quick Stats</h3>", unsafe_allow_html=True)
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

        with st.expander("🧠 View Recent Data"):
            st.write(hist.tail(10))
