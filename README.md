# 🔥 Stock Roaster

A fun Streamlit application that fetches stock data and uses the Gemini API to generate a funny, personalized roast of the stock's recent performance.

## 🛠️ Local Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)<your-username>/stock-roaster.git
    cd stock-roaster
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Set your Gemini API Key:**
    Get a key from [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key).

    ```bash
    # For Linux/Mac
    export GEMINI_API_KEY="YOUR_KEY_HERE"
    # For Windows (Command Prompt)
    set GEMINI_API_KEY=YOUR_KEY_HERE
    ```

4.  **Run the application:**
    ```bash
    streamlit run streamlit_app.py
    ```

## 🚀 Deployment

The app can be hosted for free on **Streamlit Community Cloud**.

1.  Push your code to a **public GitHub repository**.
2.  Go to the [Streamlit Community Cloud](https://share.streamlit.io/) and create a new app.
3.  **Crucially:** Add your `GEMINI_API_KEY` as a secret in the app settings.

    In the Streamlit Cloud interface, click **"Advanced settings"** -> **"Secrets"** and add an entry:
    ```
    GEMINI_API_KEY="YOUR_KEY_HERE"
    ```