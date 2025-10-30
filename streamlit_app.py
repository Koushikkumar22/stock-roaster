import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import ssl

# --- SSL FIX (bypass local self-signed certificate issues) ---
# NOTE: This line is often necessary in certain corporate or constrained environments.
ssl._create_default_https_context = ssl._unverified_context

# --- Page Setup: Modern Look ---
# Set page title, layout, and a modern icon.
st.set_page_config(
    page_title="🎤 Stock Roaster Pro",
    layout="wide", # Changed to wide layout for better use of space
    initial_sidebar_state="collapsed",
    icon="🔥"
)

# --- Title and Description Container ---
# Using a custom style for a clean, centered title block
st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🔥 Stock Roaster Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1em;'>Enter a ticker and get a short, funny roast based on recent price action.</p>", unsafe_allow_html=True)
st.divider()

# --- Gemini API Key (keep original logic) ---
def get_gemini_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_key()

if not GEMINI_API_KEY:
    st.warning("🚨 Gemini API key not found. Please set GEMINI_API_KEY in environment or Streamlit secrets.")
    # In a real deployed app, you might stop here, but keeping it running for editing.

# --- Input UI using a Form for clean grouping ---
with st.form(key='roast_form'):
    st.subheader("Configuration ⚙️")
    col1, col2, col3 = st.columns([3, 1, 3])

    with col1:
        ticker = st.text_input(
            "Ticker (e.g., AAPL, RELIANCE.NS)",
            value="AAPL",
            placeholder="Enter Ticker Symbol"
        ).strip().upper()

    with col2:
        # ADDED '5d' for one week and changed label to 'Period'
        period = st.selectbox("Period", ["5d", "1mo", "3mo", "6mo", "1y"], index=2)

    with col3:
        # Use a horizontal radio button group for a cleaner look
        tone = st.radio("Roast Tone", ["Savage 😈", "Playful 😂", "Dry 😒"], index=0, horizontal=True)

    st.markdown("---")
    # Custom button styling using st.form's submit button
    submit_button = st.form_submit_button(label="Roast it! 🎤", type="primary")

st.info("⚠️ For entertainment only. Not financial advice!")


# --- Button Action (Logic remains the same) ---
if submit_button:
    if not ticker:
        st.error("Please enter a ticker symbol.")
        # Use return instead of st.stop() for better flow in Streamlit
        st.stop()
        
    if not GEMINI_API_KEY:
        st.error("Cannot proceed without a Gemini API Key.")
        st.stop()
        
    # Map tone selection back to the simple string for the prompt
    selected_tone = tone.split(' ')[0] # e.g., "Savage 😈" -> "Savage"

    with st.spinner("Fetching data & crafting your roast..."):
        try:
            # 1. Data Fetching
            t = yf.Ticker(ticker)
            hist = t.history(period=period, interval="1d")
            
            if hist.empty:
                st.error(f"❌ No data found for **{ticker}**. Try another or check the spelling/suffix (e.g., `.NS` for NSE stocks).")
                st.stop()
                
        except Exception as e:
            st.error(f"❌ Error fetching data for **{ticker}**: {e}")
            st.stop()

        # 2. Stats Calculation
        last_close = float(hist["Close"].iloc[-1])
        first_close = float(hist["Close"].iloc[0])
        pct_change = ((last_close - first_close) / first_close) * 100
        mean_vol = int(hist["Volume"].mean()) if "Volume" in hist.columns else None
        latest_date = hist.index[-1].strftime("%Y-%m-%d")

        # 3. Stats Display (Modern st.metric)
        st.markdown("## 📊 Quick Performance Review")
        
        # Determine color and icon for the metric
        delta_color = "green" if pct_change >= 0 else "inverse"
        change_sign = "+" if pct_change >= 0 else ""

        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.metric(label="Latest Close Price", value=f"${last_close:,.2f}")
        
        with col_stats2:
            # Use st.metric's delta feature for a cleaner look
            st.metric(
                label=f"{period} Change", 
                value=f"{change_sign}{pct_change:.2f}%",
                delta=f"{change_sign}{pct_change:.2f}%",
                delta_color=delta_color
            )
        
        with col_stats3:
            if mean_vol:
                 st.metric(label="Avg. Daily Volume", value=f"{mean_vol:,.0f}")
            else:
                 st.metric(label="Data As Of", value=latest_date)

        st.line_chart(hist["Close"], use_container_width=True)
        st.markdown("---")


        # 4. Prepare Prompt and API Call
        
        summary = (
            f"Ticker: {ticker}\n"
            f"Latest close: {last_close:.2f}\n"
            f"Period: {period}\n"
            f"Period change: {pct_change:.2f}%\n"
            f"Latest date: {latest_date}\n"
        )
        if mean_vol:
            summary += f"Average daily volume: {mean_vol:,.0f}\n"

        prompt = f"""
You are a finance roast comedian.
Using the stock data below, write **3 short, funny one-liner roasts** in the {selected_tone.lower()} style.
The tone should be {selected_tone.lower()}.
Avoid giving financial advice or serious tone. Use emojis, humor, and clever wordplay.
The response must only contain the 3 roasts, each on a new line, and nothing else.

DATA:
{summary}

Roasts:
"""

        # Using the recommended model and standard API structure
        API_MODEL = "gemini-2.5-flash-preview-09-2025" 
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{API_MODEL}:generateContent?key={GEMINI_API_KEY}"
        
        try:
            # Use System Instruction for better control over the persona and format
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {
                    "parts": [{
                        "text": "You are a professional comedian specializing in savage, playful, and dry financial roasts. Your entire output must be 3 distinct, hilarious, one-line roasts based ONLY on the provided stock data. Use modern, popular internet humor and lots of relevant emojis. Do not use any introductory or concluding text."
                    }]
                }
            }
            
            response = requests.post(
                API_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                st.error(f"❌ Gemini API Error: {response.status_code} - Check the console for details.")
                st.json(response.json())
                st.stop()

            data = response.json()
            roast_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        except Exception as e:
            st.error(f"❌ Gemini API Error during generation: {e}")
            st.stop()

        # 5. Display Roast (Modern Card Look)
        st.markdown("## 🎤 The Roast Wall 🎤")
        
        # Using a custom div with a more modern card style using markdown + HTML/CSS
        st.markdown(f"""
        <style>
            .roast-card {{
                background-color: #f7f7f7; /* Light gray background */
                padding: 30px;
                border-radius: 12px;
                border-left: 5px solid #ff4b4b; /* Accent border (red) */
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Subtle shadow */
                font-size: 1.2em;
                line-height: 1.8;
                color: #2c3e50; /* Darker text */
                font-family: 'Arial', sans-serif;
                white-space: pre-wrap; /* Preserve line breaks from LLM output */
            }}
            .roast-card p {{
                margin: 0 0 15px 0;
                font-style: italic;
            }}
        </style>
        <div class="roast-card">
            {roast_text.replace('\n', '<p>•&nbsp; ')}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")

        with st.expander("🧠 Debug: Show Prompt & Raw Data"):
            st.code(prompt, language="text")
            st.markdown("### Data Head/Tail")
            st.dataframe(hist.tail(5))
