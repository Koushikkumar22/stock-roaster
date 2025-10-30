import streamlit as st
import yfinance as yf
import pandas as pd
import os
import google.generativeai as genai
from datetime import datetime
import ssl
import warnings

# --- SSL FIX (bypass local self-signed certificate issues) ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- Ignore InsecureRequestWarnings ---
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Stock Roaster 🔥", layout="centered")

st.title("🔥 Stock Roaster")
st.caption("Enter a ticker and get a short, funny roast based on recent price action.")

# --- Gemini API Key Handling ---
def get_gemini_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_key()

if not GEMINI_API_KEY:
    st.warning("🚨 Gemini API key not found. Please set it as an environment variable or in Streamlit secrets.")
    st.stop()

# --- Configure Gemini ---
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

    with st.spinner("Fetching data and crafting a killer roast..."):
        try:
            # --- Fetch data with SSL bypass ---
            ssl._create_default_https_context = ssl._create_unverified_context
            t = yf.Ticker(ticker)
            hist = t.history(period=period, interval="1d")
            
            if hist.empty:
                st.error(f"❌ No data found for **{ticker}**. Try a valid symbol or include suffix (e.g., .NS).")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
            st.stop()

        # --- Compute stats ---
        last_close = float(hist["Close"].iloc[-1])
        first_close = float(hist["Close"].iloc[0])
        pct_change = ((last_close - first_close) / first_close) * 100
        mean_vol = int(hist["Volume"].mean()) if "Volume" in hist.columns else None
        latest_date = hist.index[-1].strftime("%Y-%m-%d")

        summary = (
            f"Ticker: {ticker}\n"
            f"Latest close: {last_close:.2f}\n"
            f"Period: {period}\n"
            f"Period change: {pct_change:.2f}%\n"
            f"Latest date: {latest_date}\n"
        )
        if mean_vol:
            summary += f"Average daily volume: {mean_vol}\n"

        # --- Display Data ---
        st.subheader("📊 Price Chart")
        st.line_chart(hist["Close"], height=300)

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
            "Savage": "Make a savage, biting one-liner roast.",
            "Playful": "Make a light-hearted, funny one-liner roast.",
            "Dry": "Make a short, dry, witty one-liner roast."
        }

        prompt = f"""
You are a sarcastic financial commentator. Using the stock data below, write a short (1-2 sentences) {roast_instructions[tone]}
Do NOT include financial advice or predictions. Keep it clever, funny, and concise.

--- STOCK DATA ---
{summary}
---
Roast:
"""

        # --- Call Gemini API ---
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            roast_text = response.text.strip()
        except Exception as e:
            st.error(f"❌ Gemini API Error: {e}")
            st.stop()

        # --- Display Roast ---
        st.subheader("👑 The Verdict: Roast Time!")
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 12px; border: 2px solid #FF4B4B; 
                    background-color: #ffeaea; margin-top:10px;">
            <p style="font-size: 1.2em; font-style: italic; color: #800000; margin: 0;">{roast_text}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🕵️ Debug Info"):
            st.code(prompt)
            st.write(hist.tail(5))
