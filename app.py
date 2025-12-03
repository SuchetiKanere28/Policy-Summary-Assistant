import streamlit as st
import tempfile
import os
from pathlib import Path
import asyncio
import time

# Import utilities
from utils.document_processor import DocumentProcessor
from utils.summarizer import PolicySummarizer
from utils.entity_extractor import EntityExtractor
from utils.compilance_checker import ComplianceChecker
from utils.report_generator import ReportGenerator

# Page config
st.set_page_config(
    page_title="AI Policy Summary Assistant",
    page_icon="📄",
    layout="wide"
)

# Title
st.title("📄 AI Policy Summary Assistant")
st.markdown("**Upload any insurance policy for instant AI analysis**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    summary_length = st.slider("Summary Length", 50, 300, 150)
    chunk_size = st.slider("Chunk Size", 500, 2000, 1000)
    
    st.markdown("---")
    st.markdown("### 📁 Supported Files:")
    st.markdown("- PDF Documents")
    st.markdown("- Word Documents (.docx)")
    
    st.markdown("---")
    st.markdown("### ⚡ Features:")
    st.markdown("• 🤖 AI Summarization")
    st.markdown("• 🔍 Entity Extraction")
    st.markdown("• ✅ Compliance Check")
    st.markdown("• 📊 Readability Score")
    st.markdown("• 📥 Export Reports")

# Main content
uploaded_file = st.file_uploader(
    "Choose an insurance policy document",
    type=['pdf', 'docx'],
    help="Upload PDF or Word file"
)

if uploaded_file is not None:
    # File info
    col1, col2 = st.columns(2)
    with col1:
        st.metric("File", uploaded_file.name)
    with col2:
        st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
    
    # Process button
    if st.button("🚀 Analyze Document", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                file_path = tmp_file.name
            
            try:
                start_time = time.time()
                
                # Initialize
                processor = DocumentProcessor()
                file_type = 'pdf' if uploaded_file.name.lower().endswith('.pdf') else 'docx'
                
                # Extract text
                raw_text = processor.extract_text(file_path, file_type)
                
                if not raw_text or len(raw_text.strip()) < 50:
                    st.error("❌ Could not extract text. File might be empty or scanned.")
                    os.unlink(file_path)
                    st.stop()
                
                # Process text
                clean_text = processor.normalize_text(raw_text)
                chunks = processor.smart_chunk(clean_text, chunk_size)
                
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Summarization
                status_text.text("🤖 Generating AI summary...")
                summarizer = PolicySummarizer()
                chunk_summaries = asyncio.run(summarizer.summarize_policy_async(chunks, summary_length))
                final_summary = summarizer.generate_final_summary(chunk_summaries)
                progress_bar.progress(25)
                
                # Step 2: Entity extraction
                status_text.text("🔍 Extracting policy information...")
                extractor = EntityExtractor()
                entities = extractor.extract_all_entities(clean_text)
                progress_bar.progress(50)
                
                # Step 3: Compliance check
                status_text.text("✅ Checking compliance...")
                checker = ComplianceChecker()
                compliance = checker.check_policy_compliance(clean_text)
                recommendations = checker.get_recommendations(compliance)
                progress_bar.progress(75)
                
                # Step 4: Readability
                status_text.text("📊 Analyzing readability...")
                readability = ReportGenerator.calculate_readability(final_summary)
                progress_bar.progress(100)
                
                processing_time = time.time() - start_time
                status_text.text(f"✅ Analysis complete in {processing_time:.1f} seconds!")
                
                # Display results in tabs
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🔍 Details", "✅ Compliance", "📤 Export"])
                
                with tab1:
                    st.subheader("AI-Generated Summary")
                    st.markdown(final_summary)
                    
                    # Stats
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Original Text", f"{len(clean_text):,} chars")
                    with col_b:
                        st.metric("Summary", f"{len(final_summary.split())} words")
                    with col_c:
                        st.metric("Readability", f"{readability['flesch_reading_ease']:.1f}")
                
                with tab2:
                    st.subheader("Extracted Information")
                    
                    if entities:
                        # Display in columns
                        cols = st.columns(3)
                        items = list(entities.items())
                        
                        for i, (key, value) in enumerate(items):
                            with cols[i % 3]:
                                st.metric(
                                    key.replace('_', ' ').title(),
                                    value
                                )
                    else:
                        st.info("No specific information extracted. The document might not have standard formatting.")
                
                with tab3:
                    st.subheader("Compliance Analysis")
                    
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("Score", f"{compliance['compliance_score']}/100")
                    with col_y:
                        st.metric("Status", compliance['status'])
                    
                    # Section presence
                    st.markdown("**Document Sections:**")
                    section_cols = st.columns(4)
                    sections = list(compliance['section_presence'].items())
                    
                    for i, (section, present) in enumerate(sections):
                        with section_cols[i % 4]:
                            if present:
                                st.success(f"✅ {section}")
                            else:
                                st.warning(f"⚠️ {section}")
                    
                    # Recommendations
                    st.markdown("**Recommendations:**")
                    for rec in recommendations:
                        st.info(rec)
                
                with tab4:
                    st.subheader("Export Results")
                    
                    # Generate reports
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        # PDF Report
                        pdf_file = ReportGenerator.generate_pdf_report(final_summary, entities, compliance)
                        with open(pdf_file, "rb") as f:
                            st.download_button(
                                "📥 Download PDF Report",
                                f,
                                file_name=os.path.basename(pdf_file),
                                mime="application/pdf",
                                use_container_width=True
                            )
                    
                    with col_e2:
                        # Text Report
                        text_report = ReportGenerator.generate_text_report(final_summary, entities, compliance)
                        st.download_button(
                            "📥 Download Text Report",
                            text_report,
                            file_name="policy_summary.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    st.success("✅ Reports ready for download!")
                
                # Cleanup
                os.unlink(file_path)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if os.path.exists(file_path):
                    os.unlink(file_path)

else:
    # Welcome screen
    st.info("👆 **Upload a policy document to begin**")
    
    # Demo
    with st.expander("🎯 Try with sample text", expanded=False):
        sample = st.text_area(
            "Paste policy text to test:",
            height=150,
            value="""Policy Number: INS-2024-001
Effective Date: January 1, 2024
Premium: $1,200 annually
Coverage Limit: $100,000
Deductible: $500

This policy provides automobile insurance coverage. The insured agrees to pay premiums. Claims must be reported within 30 days."""
        )
        
        if st.button("Test with sample"):
            with st.spinner("Testing..."):
                try:
                    processor = DocumentProcessor()
                    summarizer = PolicySummarizer()
                    extractor = EntityExtractor()
                    
                    clean_text = processor.normalize_text(sample)
                    chunks = processor.smart_chunk(clean_text, 800)
                    chunk_summaries = asyncio.run(summarizer.summarize_policy_async(chunks, 100))
                    summary = summarizer.generate_final_summary(chunk_summaries)
                    entities = extractor.extract_all_entities(clean_text)
                    
                    st.success("Test successful!")
                    st.markdown("**Summary:**")
                    st.write(summary[:500] + "...")
                    
                    if entities:
                        st.markdown("**Extracted:**")
                        for key, value in entities.items():
                            st.write(f"- {key}: {value}")
                            
                except Exception as e:
                    st.error(f"Test error: {e}")
    
    # Features
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🤖 Smart AI")
        st.markdown("Uses advanced NLP to understand policy documents")
    
    with col2:
        st.markdown("### ⚡ Fast Processing")
        st.markdown("Analyzes documents in seconds, not hours")
    
    with col3:
        st.markdown("### 📊 Clear Insights")
        st.markdown("Provides actionable information and recommendations")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
    "AI Policy Summary Assistant • Built with Streamlit & Hugging Face • "
    "Model: DistilBART-CNN"
    "</div>",
    unsafe_allow_html=True
)