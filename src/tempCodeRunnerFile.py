"""
main.py
-------
Streamlit UI for the SAR Automation & Compliance Dashboard.

Run with:
    streamlit run main.py
"""

import streamlit as st
import pandas as pd
from anonymizer import SARAnonymizer
from generator import SARGenerator
from database import SARDatabase
from monitor import FraudMonitor
from risk import RiskScorer


# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Barclays SAR Automator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .risk-high   { color: #E24B4A; font-weight: 600; }
    .risk-medium { color: #EF9F27; font-weight: 600; }
    .risk-low    { color: #639922; font-weight: 600; }
    .metric-card { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; }
    .pii-tag     { background: #e8f4f8; border-radius: 4px; padding: 2px 8px;
                   font-size: 0.8em; margin: 2px; display: inline-block; }
</style>
""", unsafe_allow_html=True)


# ── Initialise backend (cached so models load only once) ───────────────────
@st.cache_resource(show_spinner="Loading AI models and database connections...")
def init_system():
    anon    = SARAnonymizer()
    gen     = SARGenerator()
    db      = SARDatabase()
    monitor = FraudMonitor()
    scorer  = RiskScorer()
    return anon, gen, db, monitor, scorer

anonymizer, generator, db, monitor, scorer = init_system()


# ── Header ─────────────────────────────────────────────────────────────────
st.title("🛡️ SAR Automation & Compliance Dashboard")
st.markdown("#### *Barclays Hack o Hire — Automated AML Detection System*")

# Show DB connection status
db_status = "🟢 MongoDB Connected" if db.connected else "🔴 MongoDB Offline (reports saved locally)"
st.caption(db_status)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Batch Processing
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("📂 Batch Data Processing")
    st.write("Upload a CSV to automatically scan for structuring fraud.")
    st.markdown("""
    **Required CSV columns:**
    - `customer_name` — customer full name
    - `amount` — transaction amount (USD)

    **Optional columns:**
    - `date`, `branch`, `type`
    """)

    uploaded_file = st.file_uploader("Upload Transaction Log", type="csv")

    if uploaded_file:
        preview_df = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)  # Reset after preview read
        st.caption(f"{len(preview_df)} transactions loaded")
        st.dataframe(preview_df.head(5), use_container_width=True)

        if st.button("🚀 Run Global Fraud Scan", type="primary", use_container_width=True):
            with st.spinner("Scanning for fraud patterns..."):
                try:
                    alerts = monitor.auto_scan(uploaded_file)
                    if alerts:
                        st.error(f"🚨 {len(alerts)} fraud pattern(s) detected!")
                        st.success("Reports filed to database.")
                        st.session_state["batch_alerts"] = alerts
                    else:
                        st.success("✅ No suspicious patterns found.")
                        st.session_state["batch_alerts"] = []
                except Exception as e:
                    st.error(f"Scan failed: {e}")

    st.divider()

    # ── Live stats ──────────────────────────────────────────────────────────
    st.header("📊 Database Stats")