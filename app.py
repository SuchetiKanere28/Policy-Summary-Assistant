import streamlit as st
import tempfile
import os
from datetime import datetime
import asyncio
import re
import matplotlib.pyplot as plt
#from agents.summary_agent import PolicySummaryAgent
from fpdf import FPDF
from agents.summary_agent import PolicySummaryAgent
from agents.file_processor import FileProcessor
from config import config
from io import BytesIO

def generate_pdf_bytes(summary_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, summary_text)
    
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


# ---------------------------------
# Page Config
# ---------------------------------
st.set_page_config(
    page_title="Policy Summary Assistant | ValueMomentum Prototype",
    page_icon="🤖",
    layout="wide"
)

# ---------------------------------
# Custom CSS for elegant UI
# ---------------------------------
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(120deg, #004e92, #000428);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0px 3px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.8rem;
        color: #003366;
    }
    .stDownloadButton>button {
        background-color: #004e92 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1rem !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------
# Cache Agent
# ---------------------------------
@st.cache_resource
def get_agent():
    return PolicySummaryAgent()

agent = get_agent()

# ---------------------------------
# Sidebar
# ---------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/1f/ValueMomentum_logo.svg", width=180)
    st.title("💼 Policy Summary Assistant")
    st.caption("AI-powered summarization for enterprise insurance documents")

    st.markdown("""
    ### How It Works
    1️⃣ Upload a PDF/DOCX file  
    2️⃣ Click *Generate Summary*  
    3️⃣ Explore results via smart tabs  

    ---
    """)

# ---------------------------------
# Header
# ---------------------------------
st.markdown("""
<div class="main-header">
    <h1>🤖 Policy Summary Assistant</h1>
    <p>Enterprise-grade AI summarization, policy intelligence, and risk/compliance dashboard</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📂 Upload Policy Document (PDF or DOCX)", type=['pdf', 'docx'])

# ---------------------------------
# Helper to generate PDF summary
# ---------------------------------
def generate_pdf(summary_text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, summary_text)
    pdf.output(filename)


# ---------------------------------
# Entity Extraction Helper
# ---------------------------------
def extract_entities(text: str):
    """Extract basic metadata and entities from policy text"""
    entities = []

    # Policy Number
    policy_no = re.findall(r'(?:Policy\s*Number|Policy\s*No\.?)\s*[:\-]?\s*([A-Z0-9\-\/]+)', text, re.IGNORECASE)
    if policy_no:
        entities.append(("Policy Number", policy_no[0]))

    # Effective / Start Date
    eff_date = re.findall(r'(?:Effective\s*Date|Start\s*Date)\s*[:\-]?\s*([A-Za-z0-9 ,/-]+)', text, re.IGNORECASE)
    if eff_date:
        entities.append(("Effective Date", eff_date[0]))

    # Expiry / End Date
    end_date = re.findall(r'(?:Expiry\s*Date|End\s*Date)\s*[:\-]?\s*([A-Za-z0-9 ,/-]+)', text, re.IGNORECASE)
    if end_date:
        entities.append(("End Date", end_date[0]))

    # Premium
    premium = re.findall(r'(?:Premium\s*Amount|Total\s*Premium)\s*[:\-]?\s*₹?([\d,]+)', text, re.IGNORECASE)
    if premium:
        entities.append(("Premium Amount (₹)", premium[0]))

    # Coverage / Sum Insured
    coverage = re.findall(r'(?:Coverage\s*Limit|Sum\s*Insured)\s*[:\-]?\s*₹?([\d,]+)', text, re.IGNORECASE)
    if coverage:
        entities.append(("Coverage Limit (₹)", coverage[0]))

    # Insured Name / Organization
    insured = re.findall(r'(?:Insured\s*Name|Proposer|Policyholder)\s*[:\-]?\s*([A-Za-z ]+)', text, re.IGNORECASE)
    if insured:
        entities.append(("Insured / Policyholder", insured[0].strip()))

    return entities


# ---------------------------------
# Risk & Compliance Checker
# ---------------------------------
def check_compliance(summary_text: str):
    """Simple rule-based compliance checks for key insurance clauses"""
    checks = []
    rules = {
        "Third-party liability coverage": ["third party", "liability"],
        "Claim procedure": ["claim", "procedure"],
        "Coverage limits": ["limit", "coverage", "insured sum"],
        "Exclusions": ["exclusion", "not covered"],
        "Policy period": ["effective date", "expiry date", "policy period"]
    }

    for clause, keywords in rules.items():
        if any(k in summary_text.lower() for k in keywords):
            checks.append((clause, "✅ Present"))
        else:
            checks.append((clause, "⚠️ Possibly Missing"))

    return checks


# ---------------------------------
# Processing Section
# ---------------------------------
if uploaded_file and st.button("🚀 Generate Summary", use_container_width=True):
    with st.spinner("AI is analyzing and summarizing your policy document..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        async def run_summary():
            return await agent.summarize_policy_document(
                tmp_path,
                'pdf' if uploaded_file.type == 'application/pdf' else 'docx'
            )

        result = asyncio.run(run_summary())
        os.unlink(tmp_path)

    if result["success"]:
        st.success("✅ Policy summary generated successfully!")

        # Tabs layout — added new Risk & Compliance + Metadata tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📘 Overview", "🔍 Key Findings", "📝 Academic Summary", "🛡️ Risk & Compliance Insights", "📊 Metadata & Entities"
        ])

        # ---------------------------
        # Tab 1: Overview
        # ---------------------------
        with tab1:
            st.subheader("📄 Document Overview")
            col1, col2, col3 = st.columns(3)
            col1.metric("📄 Original Word Count", f"{result['original_length']}")
            col2.metric("🧠 Summary Word Count", f"{result['word_count']}")
            col3.metric("⚙️ Processing Time", f"{result['processing_time']} sec")

            st.markdown(f"**File:** `{uploaded_file.name}`  \n**Generated On:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown("---")

            # Removed: Executive Snapshot heading and 3 lines

        # ---------------------------
        # Tab 2: Key Findings
        # ---------------------------
        with tab2:
            st.subheader("🔑 Extracted Key Findings")
            st.info("Key thematic insights detected across your policy document.")
            if result.get("key_findings"):
                for point in result["key_findings"]:
                    st.markdown(f"✅ {point}")
            else:
                st.warning("No specific key findings detected.")

        # ---------------------------
        # Tab 3: Academic Summary + Dynamic Policy Sections
        # ---------------------------
        with tab3:
            st.subheader("📝 Section-wise Academic Summary")

            for section, content in result.get("sections", {}).items():
                with st.expander(f"📘 {section}", expanded=True):
                    st.markdown(" ".join(content))

            st.markdown("---")
            st.markdown("## 📑 Extracted Policy Sections")

            policy_sections = result.get("policy_sections", {})

            if policy_sections:
                for title, content in policy_sections.items():
                    with st.expander(f"📄 {title.title()}", expanded=False):
                        st.markdown(content)
            else:
                st.info("No specific policy sections detected.")

            # Download options
            st.markdown("---")
            st.download_button(
                "💾 Download Summary as Text",
                result["summary"],
                file_name=f"policy_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

            pdf_path = f"policy_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            def generate_pdf(summary_text, filename):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                safe_text = (
                    summary_text.replace("’", "'")
                    .replace("‘", "'")
                    .replace("“", '"')
                    .replace("”", '"')
                    .replace("–", "-")
                    .replace("—", "-")
                )

                pdf.multi_cell(0, 10, safe_text)
                pdf.output(filename)


            

        # ---------------------------
        # Tab 4: Risk & Compliance Insights
        # ---------------------------
        with tab4:
            st.subheader("🛡️ Policy Risk & Compliance Insights")
            st.info("The following checks evaluate presence of critical policy clauses and compliance keywords.")

            checks = check_compliance(result["summary"])
            for clause, status in checks:
                color = "green" if "✅" in status else "orange"
                st.markdown(f"<p style='color:{color};font-weight:600'>{status} — {clause}</p>", unsafe_allow_html=True)

        # ---------------------------
        # Tab 5: Metadata & Entities
        # ---------------------------
        with tab5:
            st.subheader("📊 Extracted Entities and Policy Metadata")
            st.caption("Automatically extracted structured data from the document.")
            entities = extract_entities(result["summary"])
            if entities:
                st.table(entities)
            else:
                st.warning("No specific entities detected. Ensure document contains identifiable policy metadata.")

    else:
        st.error(f"❌ {result['error']}")

