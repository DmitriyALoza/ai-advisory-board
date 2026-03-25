import os
import sys

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.state import init_state

load_dotenv()

st.set_page_config(
    page_title="AI Advisory Board",
    layout="wide",
)

init_state()

st.title("AI Advisory Board")
st.caption("Multi-agent investor simulation for fundraising strategy")

st.markdown(
    """
This project runs a structured, iterative advisory loop inspired by ArchAI's pattern:
- Four investor agents review your startup materials from distinct lenses.
- A supervisor agent critiques the board's output across iterations.
- The supervisor consolidates final guidance into an executive recommendation with advantages,
  disadvantages, and the optimal route to pursue.
- Sessions are persisted to SQLite and can be reloaded from Board Chat.
"""
)

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.subheader("Board Members")
    st.markdown("- **Maya Chen (Market Maven):** growth strategy, TAM, GTM velocity")
    st.markdown("- **Daniel Ross (Finance Hawk):** unit economics, runway, forecast integrity")
    st.markdown("- **Priya Nair (Product Operator):** product execution, retention, team capability")
    st.markdown("- **Owen Brooks (Risk Guardian):** downside, compliance, concentration, security")

    st.subheader("Supported Documents")
    st.markdown("Upload `.pdf`, `.pptx`, `.ppt`, `.docx`, `.txt`, and `.md` files in Board Chat.")
    st.caption("Legacy `.ppt` conversion requires LibreOffice (`soffice`) installed on your machine.")

with col2:
    st.subheader("How To Use")
    st.markdown("1. Open **Board Chat** from the sidebar pages list.")
    st.markdown("2. Upload pitch deck, forecasts, and supporting docs.")
    st.markdown("3. Ask the board for feedback or decision support.")
    st.markdown("4. Review individual investor messages and the supervisor summary.")

st.divider()
st.info("Use the **Board Chat** page to start a session.")
