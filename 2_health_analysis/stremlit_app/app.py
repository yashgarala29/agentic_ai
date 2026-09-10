import os
from pathlib import Path
import streamlit as st
from dotenv import find_dotenv, load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv(find_dotenv())

# Page configuration
st.set_page_config(
    page_title="Health Report Analyzer & Diet Planner",
    page_icon="🩺",
    layout="wide"
)

# Custom styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .status-card {
        padding: 1rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 4px solid #1E88E5;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🩺 Health Report Analyzer & Diet Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Extract clinical test metrics, identify anomalies, and receive a customized Indian diet plan.</div>', unsafe_allow_html=True)

# Helper function to parse LLM response
def get_response_text(response):
    if hasattr(response, "text") and response.text:
        return response.text
    if isinstance(response.content, str):
        return response.content
    if isinstance(response.content, list):
        texts = [
            item.get("text", "") 
            for item in response.content 
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        if texts:
            return "\n".join(texts)
    return str(response.content)

# Initialize LLM
@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(model="gemma-4-31b-it")

# Path to sample health report if available
sample_report_path = Path(__file__).parent.parent / "health_report.txt"

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings & Actions")
    if sample_report_path.exists():
        if st.button("📋 Load Sample Health Report", use_container_width=True):
            with open(sample_report_path, "r", encoding="utf-8") as f:
                st.session_state["report_input"] = f.read()
            st.success("Sample report loaded!")

    if st.button("🧹 Clear Input", use_container_width=True):
        st.session_state["report_input"] = ""
        st.session_state.pop("extraction_result", None)
        st.session_state.pop("diet_result", None)
        st.rerun()

    st.markdown("---")
    st.markdown("""
    **Model**: `gemma-4-31b-it`  
    **Framework**: LangChain + Streamlit  
    
    *Note: This tool provides dietary suggestions based on lab markers and is not a substitute for professional medical advice.*
    """)

# Input Area
report_text = st.text_area(
    "Paste Health / Blood Test Report:",
    value=st.session_state.get("report_input", ""),
    height=240,
    placeholder="Paste patient health report text here (e.g., Complete Blood Count, Lipid Panel, Metabolic Panel)...",
    key="report_input"
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    analyze_clicked = st.button("🔬 Analyze Report", type="primary", use_container_width=True)

if analyze_clicked:
    if not report_text.strip():
        st.warning("⚠️ Please paste a health report or click 'Load Sample Health Report' first.")
    else:
        try:
            llm = get_llm()

            with st.spinner("⏳ Analyzing health report and classifying test values..."):
                extraction_prompt = f"""
you are a medical data extractor.
From the blood report below, extract all test values and classify each one as HIGH, LOW, or NORMAL based on the reference range provided in the report.
Format your response as:
- Test Name: value | status: HIGH, LOW, or NORMAL | Reference: range

Blood Report:
{report_text}
"""
                extraction_response = llm.invoke(extraction_prompt)
                extracted_value = get_response_text(extraction_response)
                st.session_state["extraction_result"] = extracted_value

            with st.spinner("🥗 Generating health summary and Indian diet plan..."):
                diet_prompt = f"""
you are a clinical nutritionist specializing in Indian dietary habits.
Based on the blood work analysis below, write:
1. A short health summary in 3 lines explaining the patient's condition in simple language.
2. A short, practical Indian diet plan having two sections:
   (1) Food to avoid
   (2) Food to eat more of
Do not include any other sections in the diet plan.

Blood work analysis:
{extracted_value}
"""
                diet_response = llm.invoke(diet_prompt)
                diet_value = get_response_text(diet_response)
                st.session_state["diet_result"] = diet_value

            st.success("✅ Analysis and Diet Plan generated successfully!")

        except Exception as e:
            st.error(f"❌ An error occurred during analysis: {str(e)}")

# Display Results
if "extraction_result" in st.session_state and "diet_result" in st.session_state:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Lab Value Extraction", "🩺 Health Summary & Diet Plan", "📄 Full Combined Report"])

    with tab1:
        st.subheader("Extracted Test Values & Classifications")
        st.markdown(st.session_state["extraction_result"])

    with tab2:
        st.subheader("Clinical Summary & Personalized Indian Diet Plan")
        st.markdown(st.session_state["diet_result"])

    with tab3:
        combined_report = f"""# Medical Health Analysis & Diet Plan

## 1. Extracted Lab Values
{st.session_state['extraction_result']}

## 2. Health Summary & Diet Plan
{st.session_state['diet_result']}
"""
        st.download_button(
            label="📥 Download Full Report (.md)",
            data=combined_report,
            file_name="health_analysis_diet_plan.md",
            mime="text/markdown",
        )
        st.text_area("Full Output", value=combined_report, height=350)
