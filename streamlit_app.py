import streamlit as st
import yfinance as yf
import pandas as pd
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import ssl

# --- SSL FIX (bypass local self-signed certificate issues) ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- Page Setup ---
st.set_page_config(page_title="Stock Roaster 🔥", layout="centered")

st.title("🔥 Stock Roaster")
st.caption("Enter a ticker and get a funny, brutal, or sarcastic roast based on recent price action.")

# --- Gemini API Key Handling ---
def get_gemini_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_key()

if not GEMINI_API_KEY:
    st.warning("🚨 **Gemini API key not found.** Please set `GEMINI_API_KEY` locally or in Streamlit secrets.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- Input Section ---
col1, col2 = st.columns([3, 1])

with col1:
    ticker = st.text_input("Ticker (e.g., AAPL, RELIANCE.NS, TCS.NS)", value="AAPL").strip().upper()

with col2:
    period = st.selectbox("Period", ["1mo", "3mo", "6mo"], index=0)

tone = st.radio("Roast tone", ["Savage", "Playful", "Dry"], index=0, horizontal=True)

st.info("⚠️ For entertainment only — not financial advice.")

# --- Main Roast Button ---
if st.button("Roast it! 🎤"):
    if not ticker:
        st.error("Please enter a stock ticker.")
        st.stop()

    with st.spinner("Fetching data and cooking up a spicy roast..."):
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period, interval="1d")
            if hist.empty:
                st.error(f"❌ No data found for {ticker}. Try a different one or add `.NS` for Indian stocks.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
            st.stop()

        # --- Compute basic stats ---
        last_close = float(hist["Close"].iloc[-1])
        first_close = float(hist["Close"].iloc[0])
        pct_change = ((last_close - first_close) / first_close) * 100
        mean_vol = int(hist["Volume"].mean()) if "Volume" in hist.columns else None
        latest_date = hist.index[-1].strftime("%Y-%m-%d")

        summary = (
            f"Ticker: {ticker}\n"
            f"Latest close: {last_close:.2f}\n"
            f"Period: {period}\n"
            f"Change over period: {pct_change:.2f}%\n"
            f"Latest date: {latest_date}\n"
        )
        if mean_vol:
            summary += f"Avg daily volume: {mean_vol}\n"

        # --- Display Data ---
        st.subheader("📊 Price Chart")
        st.line_chart(hist["Close"])

        st.subheader("📈 Quick Stats")
        change_style = "green" if pct_change >= 0 else "red"
        st.markdown(f"""
        * **Latest Close:** ${last_close:,.2f}  
        * **{period} Change:** :{"chart_with_upwards_trend" if pct_change >= 0 else "chart_with_downwards_trend"}: 
          <span style="color:{change_style}; font-weight:bold;">{pct_change:+.2f}%</span>  
        * **Latest Date:** {latest_date}
        """, unsafe_allow_html=True)

        # --- Roast Prompt ---
        roast_instructions = {
            "Savage": "Make it brutally honest, sarcastic, and meme-worthy. Think Twitter-level savagery.",
            "Playful": "Make it funny, friendly, and creative with emojis and pop-culture references.",
            "Dry": "Make it witty and subtle — like a Wall Street analyst with dark humor."
        }

        prompt = f"""
You are a hilarious, sarcastic stock market commentator.
Using the stock data below, create 3-5 short roasts (1–2 sentences each).
Each roast should have a different tone (sarcastic, Gen Z meme, corporate roast, optimistic denial, etc.).
Keep them short, funny, and original — no financial advice, no generic text.

DATA TO ROAST:
{summary}

Tone to lean toward: {roast_instructions[tone]}

Format the output like:
1. 🥶 [Roast line]
2. 📉 [Roast line]
3. 💀 [Roast line]
---
Now roast:
"""

        # --- Call Gemini API ---
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            roast_text = response.text.strip()
        except Exception as e:
            st.error(f"❌ Gemini API Error: {e}")
            st.stop()

        # --- Display Roast ---
        st.subheader("🔥 The Roast Wall 🔥")
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 12px; border: 2px solid #ff4b4b; background-color: #fff1f1;">
            <pre style="font-size: 1.1em; color: #800000; white-space: pre-wrap;">{roast_text}</pre>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🧠 Debug: Show Prompt & Raw Data"):
            st.code(prompt)
            st.write(hist.tail(5))
