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
    stats = db.get_stats()
    st.metric("Total Reports Filed", stats["total"])
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🔴 High",   stats["high_risk"])
    col_b.metric("🟡 Medium", stats["medium_risk"])
    col_c.metric("🟢 Low",    stats["low_risk"])
    if st.button("🔄 Refresh Stats", use_container_width=True):
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_manual, tab_batch, tab_log = st.tabs(
    ["📥 Manual Case Entry", "🕵️ Batch Scan Results", "📋 Audit Log"]
)


# ── TAB 1: Manual Case Entry ──────────────────────────────────────────────
with tab_manual:
    col_input, col_output = st.columns(2, gap="large")

    with col_input:
        st.subheader("Enter Transaction Details")
        raw_text = st.text_area(
            "Paste individual transaction log for immediate analysis:",
            height=220,
            placeholder=(
                "e.g. Aradhya Ranjan transferred $14,500 in 3 wire transfers "
                "to an overseas account in Mumbai. Contact: aradhya@bank.com, "
                "+91-9876543210. Transactions occurred within 90 minutes."
            ),
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            analyze_btn = st.button("🔍 Analyze & File Report", type="primary", use_container_width=True)
        with col_btn2:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)
            if clear_btn:
                st.session_state.pop("latest_report", None)
                st.rerun()

        # ── Pipeline progress display ──────────────────────────────────────
        if analyze_btn:
            if not raw_text.strip():
                st.warning("Please enter transaction text first.")
            else:
                progress = st.progress(0, text="Starting pipeline...")
                status_placeholder = st.empty()

                try:
                    # Step 1: Detect entities
                    progress.progress(10, text="🔍 Detecting PII entities...")
                    detected = anonymizer.get_detected_entities(raw_text)

                    # Step 2: Mask PII
                    progress.progress(30, text="🔒 Masking PII with Presidio...")
                    masked = anonymizer.mask_data(raw_text)

                    # Step 3: Risk scoring
                    progress.progress(50, text="📊 Scoring risk level...")
                    risk = scorer.score(raw_text)

                    # Step 4: Generate AI narrative
                    progress.progress(65, text="🤖 Generating SAR narrative with Llama 3.2...")
                    narrative = generator.generate_narrative(masked)

                    # Step 5: Save to DB
                    progress.progress(90, text="💾 Saving to MongoDB...")
                    report_id = db.save_report(
                        raw_data=raw_text,
                        masked_text=masked,
                        ai_narrative=narrative,
                        risk_level=risk["level"],
                        risk_score=risk["score"],
                        risk_flags=risk["flags"],
                    )

                    progress.progress(100, text="✅ Complete!")

                    st.session_state["latest_report"] = {
                        "id": str(report_id),
                        "masked": masked,
                        "narrative": narrative,
                        "risk": risk,
                        "detected_entities": detected,
                    }

                except Exception as e:
                    progress.empty()
                    st.error(f"Pipeline failed: {e}")

    # ── Output column ──────────────────────────────────────────────────────
    with col_output:
        st.subheader("Audit & AI Output")

        if "latest_report" in st.session_state:
            report = st.session_state["latest_report"]
            risk   = report["risk"]

            # Report ID
            st.success(f"✅ Report Filed — ID: `{report['id']}`")

            # Risk score gauge
            risk_color_map = {"High": "red", "Medium": "orange", "Low": "green"}
            st.markdown(f"**Risk Level:** :{risk_color_map.get(risk['level'], 'gray')}[{risk['level']}]  ({risk['score']}/100)")
            st.progress(risk["score"] / 100)

            if risk["flags"]:
                with st.expander("🚩 Risk Flags Triggered"):
                    for flag in risk["flags"]:
                        st.markdown(f"• {flag}")

            # PII audit
            with st.expander("🔒 Privacy Audit — Masked Input"):
                st.code(report["masked"], language=None)
                entities = report.get("detected_entities", [])
                if entities:
                    st.markdown("**Entities detected and removed:**")
                    tags_html = " ".join(
                        f'<span class="pii-tag">{e["entity_type"]}</span>'
                        for e in entities
                    )
                    st.markdown(tags_html, unsafe_allow_html=True)

            # AI Narrative
            st.markdown("#### 🤖 AI-Generated Compliance Narrative")
            st.info(report["narrative"])

            # Status update
            new_status = st.selectbox(
                "Update case status:",
                ["Flagged for Review", "Under Investigation", "Filed to FinCEN", "Closed — No Action"],
                key="status_select",
            )
            if st.button("Update Status", use_container_width=True):
                success = db.update_status(report["id"], new_status)
                if success:
                    st.success(f"Status updated to: {new_status}")
                else:
                    st.info(f"Status noted (DB offline): {new_status}")

        else:
            st.info("Results will appear here after analysis.")


# ── TAB 2: Batch Scan Results ─────────────────────────────────────────────
with tab_batch:
    st.subheader("Automated Batch Scan Results")

    alerts = st.session_state.get("batch_alerts")

    if alerts is None:
        st.info("Upload a CSV in the sidebar and click 'Run Global Fraud Scan' to see results here.")

    elif len(alerts) == 0:
        st.success("✅ No suspicious patterns detected in the uploaded file.")

    else:
        st.error(f"🚨 {len(alerts)} fraud pattern(s) detected and reported.")

        # Summary metrics
        m1, m2, m3 = st.columns(3)
        total_flagged_amount = sum(a["total"] for a in alerts)
        high_risk_count = sum(1 for a in alerts if a["risk_level"] == "High")
        m1.metric("Cases Flagged",         len(alerts))
        m2.metric("Total Flagged Volume",  f"${total_flagged_amount:,.2f}")
        m3.metric("High Risk Cases",       high_risk_count)

        st.divider()

        # Individual alerts
        for i, alert in enumerate(alerts):
            risk_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(alert["risk_level"], "⚪")
            with st.expander(
                f"{risk_color} {alert['name']} — ${alert['total']:,.2f} "
                f"({alert['transaction_count']} transactions) — {alert['risk_level']} Risk"
            ):
                st.markdown(f"**Report ID:** `{alert['report_id']}`")
                st.markdown(f"**Risk Score:** {alert['risk_score']}/100")
                st.markdown("**AI-Generated Narrative:**")
                st.info(alert["narrative"])

    st.divider()

    # ── Entity aggregation table (if CSV uploaded) ─────────────────────────
    if uploaded_file:
        st.subheader("🕵️ Entity Aggregation Table")
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            if "customer_name" in df.columns and "amount" in df.columns:
                df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                tracking_df = (
                    df.groupby("customer_name")["amount"]
                    .agg(["sum", "count"])
                    .reset_index()
                )
                tracking_df.columns = ["Customer Name", "Total Daily Volume ($)", "Transaction Count"]
                tracking_df["Risk"] = tracking_df["Total Daily Volume ($)"].apply(
                    lambda x: "🔴 High" if x >= 25000 else ("🟡 Medium" if x >= 10000 else "🟢 Low")
                )
                tracking_df["SAR Required"] = tracking_df["Total Daily Volume ($)"].apply(
                    lambda x: "Yes" if x >= 10000 else "No"
                )

                def highlight_fraud(row):
                    color = ""
                    if row["Total Daily Volume ($)"] >= 25000:
                        color = "background-color: #fce4e4"
                    elif row["Total Daily Volume ($)"] >= 10000:
                        color = "background-color: #fff3cd"
                    return [color] * len(row)

                st.dataframe(
                    tracking_df.style.apply(highlight_fraud, axis=1),
                    use_container_width=True,
                )
        except Exception as e:
            st.warning(f"Could not render aggregation table: {e}")


# ── TAB 3: Audit Log ──────────────────────────────────────────────────────
with tab_log:
    st.subheader("Audit Log — MongoDB (Reports Collection)")

    if not db.connected:
        st.warning("MongoDB is offline. No stored reports to display.")
    else:
        reports = db.get_all_reports(limit=50)
        if not reports:
            st.info("No reports filed yet.")
        else:
            log_data = []
            for r in reports:
                log_data.append({
                    "Report ID":   r.get("_id", "—"),
                    "Timestamp":   str(r.get("timestamp", "—"))[:19],
                    "Risk Level":  r.get("risk_level", "—"),
                    "Risk Score":  r.get("risk_score", "—"),
                    "Status":      r.get("status", "—"),
                })
            log_df = pd.DataFrame(log_data)
            st.dataframe(log_df, use_container_width=True)

            if st.button("📥 Export to CSV"):
                csv_data = log_df.to_csv(index=False)
                st.download_button(
                    label="Download Audit Log",
                    data=csv_data,
                    file_name="sar_audit_log.csv",
                    mime="text/csv",
                )


# ── Footer ─────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "🔒 Privacy Notice: All processing is local. "
    "Ollama (Llama 3.2) runs on-device. "
    "Microsoft Presidio masks PII before any AI processing. "
    "No customer data leaves this machine."
)
