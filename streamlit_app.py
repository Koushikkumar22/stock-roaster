import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import ssl
import plotly.graph_objects as go

# --- SSL FIX ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- Page Setup ---
st.set_page_config(page_title="🔥 Stock Roaster", layout="centered")

st.title("🔥 Stock Roaster")
st.caption("Enter a ticker and get a short, funny roast based on its performance and industry trends.")

# --- Gemini API Key ---
def get_gemini_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_key()

if not GEMINI_API_KEY:
    st.warning("🚨 Gemini API key not found. Please set GEMINI_API_KEY in environment or Streamlit secrets.")
    st.stop()

# --- Input UI ---
col1, col2 = st.columns([3, 1])

with col1:
    ticker = st.text_input("Ticker (e.g., AAPL, RELIANCE.NS, TCS.NS)", value="AAPL").strip().upper()

with col2:
    period = st.selectbox("Period", ["1mo", "3mo", "6mo"], index=0)

tone = st.radio("Roast tone", ["Savage", "Playful", "Dry"], index=0, horizontal=True)

st.info("⚠️ For entertainment only. Not financial advice! \n\n💡 Tip: For Indian stocks, use `.NS` at the end (e.g., RELIANCE.NS, TCS.NS)")

# --- Button Action ---
if st.button("Roast it! 🎤"):
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

        # --- Company info ---
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

        # --- Roast Prompt ---
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

        # --- Gemini API Call ---
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

        # --- 🔥 Roast Wall ---
        st.subheader("🔥 The Roast Wall 🔥")
        st.markdown(f"""
        <div style="background-color:#fff3f3; padding:25px; border-radius:15px; border:2px solid #ff4b4b;
                    font-size:1.1em; color:#2b2b2b; line-height:1.6; margin-bottom:25px;">
        {roast_text}
        </div>
        """, unsafe_allow_html=True)

        # --- 📊 Improved Price Chart (Plotly) ---
        st.subheader("📊 Price Chart")

        hist["MA20"] = hist["Close"].rolling(20).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist["Close"],
            mode="lines", name="Close Price",
            line=dict(color="#007bff", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist["MA20"],
            mode="lines", name="20-day Avg",
            line=dict(color="#ff9900", width=1.5, dash="dot")
        ))

        fig.update_layout(
            title=f"{company_name} ({ticker}) Stock Price",
            xaxis_title="Date",
            yaxis_title="Price (₹ / $)",
            template="plotly_white",
            plot_bgcolor="#f9f9f9",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- 📈 Quick Stats ---
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

        with st.expander("🧠 Raw Data"):
            st.write(hist.tail(10))
