import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import ssl

# --- SSL FIX (bypass local self-signed certificate issues) ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- Page Setup ---
st.set_page_config(page_title="🔥 Stock Roaster", layout="centered")
st.title("🔥 Stock Roaster")
st.caption("Type a company name — get a chart and a spicy roast about its stock performance. 😎")

# --- Gemini API Key ---
def get_gemini_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_key()

if not GEMINI_API_KEY:
    st.warning("🚨 Gemini API key not found. Please set GEMINI_API_KEY in environment or Streamlit secrets.")
    st.stop()

# --- Helper: Find ticker from company name ---
def get_ticker_from_name(query):
    """Search Yahoo Finance for a company name and return its best ticker match."""
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if "quotes" in data and len(data["quotes"]) > 0:
            return data["quotes"][0]["symbol"]
        return None
    except Exception:
        return None

# --- Input UI ---
col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_input("Company Name or Ticker (e.g., Apple, Infosys, Tesla)", value="Apple").strip()

with col2:
    period = st.selectbox("Period", ["1mo", "3mo", "6mo"], index=0)

tone = st.radio("Roast tone", ["Savage", "Playful", "Dry"], index=0, horizontal=True)

st.info("⚠️ For entertainment only. Not financial advice!")

# --- Button Action ---
if st.button("Roast it! 🎤"):
    if not user_input:
        st.error("Please enter a company name or ticker.")
        st.stop()

    with st.spinner("Finding the stock and cooking your roast... 🍳"):
        # Try to get ticker
        ticker = user_input.upper()
        if not any(char.isdigit() for char in ticker):  # probably a name
            found_ticker = get_ticker_from_name(user_input)
            if found_ticker:
                ticker = found_ticker
            else:
                st.error(f"❌ Couldn’t find a ticker for '{user_input}'. Try another name.")
                st.stop()

        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period, interval="1d")
            info = t.info  # Fetch metadata about the company

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
        market_cap_str = f"${market_cap/1e9:.2f}B" if market_cap else "N/A"

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

        # --- Gemini Roast Prompt ---
        roast_styles = {
            "Savage": "Make it brutally savage, darkly funny, and use clever finance/industry references.",
            "Playful": "Make it light-hearted, witty, and sprinkle finance-related humor.",
            "Dry": "Make it sarcastic, short, and deadpan funny."
        }

        prompt = f"""
You are a finance roast comedian and market analyst.
Your goal is to roast the company below based on its stock performance, sector, and industry.

Instructions:
- Write **3 distinct one-liner roasts**.
- Be specific: reference its **industry trends, business reputation, or recent stock behavior**.
- Each roast must use emojis and feel like a viral tweet or meme caption.
- Avoid any financial advice or sensitive content.
- Tone style: {roast_styles[tone]}

DATA:
{summary}

Now roast them:
"""

        # --- Gemini API Call (2.5 Flash) ---
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

        # --- Display Roast Wall ---
        st.markdown(
            f"""
            <div style="
                background-color:#fff3f3;
                padding:25px;
                border-radius:15px;
                border:2px solid #ff4b4b;
                font-size:1.1em;
                color:#2b2b2b;
                line-height:1.6;
                margin-bottom:25px;
            ">
            <h3 style="text-align:center;">🔥 The Roast Wall 🔥</h3>
            {roast_text}
            </div>
            """,
            unsafe_allow_html=True
        )

        # --- Chart & Stats ---
        st.subheader("📊 Price Chart")
        st.line_chart(hist["Close"])

        st.subheader("📈 Quick Stats")
        color = "green" if pct_change >= 0 else "red"
        st.markdown(
            f"* **Company:** {company_name}\n"
            f"* **Sector:** {sector}\n"
            f"* **Industry:** {industry}\n"
            f"* **Market Cap:** {market_cap_str}\n"
            f"* **{period} Change:** <span style='color:{color}; font-weight:bold;'>{pct_change:+.2f}%</span>\n",
            unsafe_allow_html=True
        )

        with st.expander("🧠 Debug: Show Prompt & Raw Data"):
            st.code(prompt)
            st.write(hist.tail(5))
