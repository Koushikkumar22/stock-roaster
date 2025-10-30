import streamlit as st
import requests

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Stock Roaster 🔥", page_icon="🔥", layout="wide")

# ---------------------- CUSTOM CSS ----------------------
st.markdown("""
<style>
body {
    background-color: #0d0d0d;
    color: #f0f0f0;
    font-family: 'Segoe UI', sans-serif;
}

h1, h2, h3, h4 {
    color: #ff4b4b;
    text-shadow: 0 0 10px rgba(255, 75, 75, 0.4);
}

div.stButton > button {
    background-color: #ff4b4b;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    padding: 0.6rem 1.2rem;
    transition: all 0.3s ease-in-out;
}
div.stButton > button:hover {
    background-color: #ff7777;
    transform: scale(1.05);
}

textarea {
    background-color: #1a1a1a !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}

.css-1cpxqw2 {
    background-color: #111 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- HEADER ----------------------
st.title("🔥 Stock Roaster: Where Boring Stocks Get Burned 🔥")
st.markdown("Enter your favorite (or most hated) stock below and let AI roast it mercilessly!")

# ---------------------- GEMINI CONFIG ----------------------
def get_gemini_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return st.text_input("🔑 Enter your Gemini API Key:", type="password")

GEMINI_API_KEY = get_gemini_key()

# ---------------------- INPUT ----------------------
user_stock = st.text_input("📈 Enter Stock Name or Symbol (e.g., TCS, INFY, RELIANCE):", placeholder="Type here...")
intensity = st.slider("🔥 Roast Intensity", 1, 10, 6, help="Higher means more savage roasting!")

# ---------------------- GEMINI API FUNCTION ----------------------
def generate_roast(stock_name, intensity_level):
    if not GEMINI_API_KEY:
        return "❌ Please enter your Gemini API key."

    prompt = f"""
    You are a savage and funny stock market roaster.
    Roast the stock '{stock_name}' with wit, sarcasm, and intelligence.
    Intensity level: {intensity_level}/10
    Keep it market-themed, short (4-6 lines), and entertaining.
    """

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            },
            params={"key": GEMINI_API_KEY},
            timeout=20
        )

        if response.status_code != 200:
            return f"❌ Gemini API Error: {response.status_code} - {response.text}"

        data = response.json()
        roast_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return roast_text.strip()

    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching data: {e}"

# ---------------------- GENERATE ROAST ----------------------
if st.button("🔥 Roast This Stock"):
    if user_stock.strip() == "":
        st.warning("Please enter a stock name first!")
    else:
        with st.spinner("Cooking up some spicy roast... 🍳"):
            roast_text = generate_roast(user_stock, intensity)
        if roast_text:
            st.success("🔥 Roast Ready!")

            st.subheader("🔥 The Roast Wall 🔥")
            st.markdown(f"""
            <div style="
                padding: 25px;
                border-radius: 14px;
                border: 2px solid #ff4b4b;
                background-color: #2c0000;
                box-shadow: 0 0 15px rgba(255,75,75,0.3);
            ">
                <pre style="
                    font-size: 1.15em;
                    font-weight: 600;
                    color: #ffdddd;
                    line-height: 1.5;
                    white-space: pre-wrap;
                ">{roast_text}</pre>
            </div>
            """, unsafe_allow_html=True)

# ---------------------- FOOTER ----------------------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit + Gemini API | © 2025 Stock Roaster")
