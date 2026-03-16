import streamlit as st
import pandas as pd
from anonymizer import SARAnonymizer
from generator import SARGenerator
from database import SARDatabase
from monitor import FraudMonitor

# 1. PAGE SETUP
st.set_page_config(page_title="Barclays SAR Automator", layout="wide")

# 2. INITIALIZE BACKEND (Cached for performance)
@st.cache_resource
def init_system():
    # These load the AI models and Database connections once
    return SARAnonymizer(), SARGenerator(), SARDatabase(), FraudMonitor()

anonymizer, generator, db, monitor = init_system()

# 3. HEADER & BRANDING
st.title("🛡️ SAR Automation & Compliance Dashboard")
st.markdown("### *Barclays Hack o Hire | Automated AML Detection System*")
st.divider()

# 4. SIDEBAR: AUTOMATED BATCH PROCESSING
st.sidebar.header("📂 Batch Data Processing")
st.sidebar.write("Upload a CSV file to automatically detect and report fraud patterns.")
uploaded_file = st.sidebar.file_uploader("Upload Transaction Log", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if st.sidebar.button("🚀 Run Global Fraud Scan"):
        with st.spinner("Analyzing patterns..."):
            # The 'monitor' automatically finds fraud, masks it, and generates AI reports
            alerts = monitor.auto_scan(uploaded_file)
            
            if alerts:
                st.sidebar.error(f"🚨 {len(alerts)} Frauds Automatically Detected!")
                st.sidebar.success("All reports filed to MongoDB.")
            else:
                st.sidebar.success("✅ No suspicious patterns found.")

# 5. MAIN DASHBOARD: MANUAL ENTRY & ANALYSIS
col1, col2 = st.columns(2)

with col1:
    st.header("📥 Manual Case Entry")
    raw_text = st.text_area(
        "Paste individual transaction logs for immediate analysis:", 
        height=250,
        placeholder="e.g., Aradhya Ranjan moved $15,000 via wire transfer to Mumbai..."
    )
    
    if st.button("Analyze & Save Report", type="primary"):
        if raw_text:
            with st.spinner("Processing through AI Pipeline..."):
                # A. PRIVACY: Mask the data
                masked = anonymizer.mask_data(raw_text)
                # B. AI: Generate the narrative
                narrative = generator.generate_narrative(masked)
                # C. DATABASE: Save the record
                report_id = db.save_report(raw_text, masked, narrative)
                
                # Show results in Col 2 via session state or immediate display
                st.session_state['latest_report'] = {
                    "id": report_id,
                    "masked": masked,
                    "narrative": narrative
                }
        else:
            st.warning("Please enter text to analyze.")

with col2:
    st.header("📤 Audit & AI Output")
    if 'latest_report' in st.session_state:
        report = st.session_state['latest_report']
        st.success(f"Successfully Filed! ID: {report['id']}")
        
        with st.expander("🛡️ View Privacy Audit (Masked Data)"):
            st.code(report['masked'])
            
        st.markdown("#### 🤖 AI-Generated Compliance Narrative")
        st.info(report['narrative'])
    else:
        st.write("Results will appear here after analysis.")

# 6. VISUAL TRACKING (Shows if a CSV is uploaded)
if uploaded_file:
    st.divider()
    st.subheader("🕵️ Automated Entity Tracking (Aggregation)")
    
    # Logic to track people across different transaction rows
    tracking_df = df.groupby('customer_name')['amount'].agg(['sum', 'count']).reset_index()
    tracking_df.columns = ['Customer Name', 'Total Daily Volume', 'Transaction Count']
    
    # Highlight rows that break the $10,000 rule
    def highlight_fraud(row):
        return ['background-color: #fce4e4' if row['Total Daily Volume'] >= 10000 else '' for _ in row]

    st.dataframe(tracking_df.style.apply(highlight_fraud, axis=1), use_container_width=True)

# 7. FOOTER
st.divider()
st.caption("Privacy Notice: All processing occurs locally using Ollama (Llama 3.2) and Microsoft Presidio. No data leaves this machine.")