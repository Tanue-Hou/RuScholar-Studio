import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import tempfile
from naturalization_layer.document_parser import parse_document
from naturalization_layer.rules_engine import analyze_text_rules
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge
from naturalization_layer.model_downloader import download_model

# Apple-inspired Custom CSS Styling
APPLE_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Main layout defaults */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: #f5f5f7;
    color: #1d1d1f;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #d2d2d7 !important;
}

/* Titles and Headers */
h1, h2, h3, h4 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #1d1d1f !important;
    font-weight: 600 !important;
    letter-spacing: -0.022em !important;
}

h1 {
    font-size: 2.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* Subtitles */
.subtitle {
    color: #86868b;
    font-size: 1.25rem;
    font-weight: 400;
    margin-bottom: 2rem;
    letter-spacing: -0.011em;
}

/* Button Styling (Apple Pill Blue Button) */
.stButton>button {
    background-color: #0071e3 !important;
    color: white !important;
    border-radius: 980px !important;
    border: none !important;
    padding: 10px 24px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

.stButton>button:hover {
    background-color: #0077ed !important;
    box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25) !important;
    transform: translateY(-1px);
}

.stButton>button:active {
    transform: translateY(0);
}

/* File Upload Area */
[data-testid="stFileUploadDropzone"] {
    border: 1px dashed #d2d2d7 !important;
    border-radius: 16px !important;
    background-color: #ffffff !important;
    padding: 2rem !important;
    transition: all 0.2s ease !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: #0071e3 !important;
    background-color: #fbfbfd !important;
}

/* Metrics Dashboard Cards */
div[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

div[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: #0071e3 !important;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: #86868b !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Premium Card container for sentence diagnostics */
.sentence-card {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.015);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.sentence-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.03);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid #f5f5f7;
    padding-bottom: 0.5rem;
}

.card-tag {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 980px;
}

.tag-high {
    background-color: #ffeef0;
    color: #ff3b30;
}

.tag-normal {
    background-color: #f5f5f7;
    color: #86868b;
}

.text-original {
    font-size: 0.95rem;
    color: #1d1d1f;
    margin-bottom: 1rem;
    line-height: 1.5;
    background-color: #fafafa;
    padding: 10px 14px;
    border-radius: 8px;
    border-left: 3px solid #ff3b30;
}

.text-rewrite {
    font-size: 1rem;
    color: #1d1d1f;
    font-weight: 500;
    line-height: 1.5;
    background-color: #f5fbf6;
    padding: 12px 16px;
    border-radius: 8px;
    border-left: 3px solid #34c759;
}

.score-badge {
    font-family: monospace;
    font-weight: 600;
    font-size: 0.85rem;
    color: #86868b;
}
</style>
"""

st.set_page_config(page_title="Academic Russian Naturalizer", layout="wide")
st.markdown(APPLE_STYLE, unsafe_allow_html=True)

# Application Header
st.title("Academic Russian Style Diagnostics")
st.markdown("<div class='subtitle'>Local, premium intelligence for naturalizing translationese and uniform phrasing.</div>", unsafe_allow_html=True)

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "Qwen3-4B-Q5_K_M.gguf")
EXPECTED_SIZE = 2889513184

model_loaded = os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) == EXPECTED_SIZE

# Sidebar Configuration & Downloader
st.sidebar.header("Model Management")
if not model_loaded:
    st.sidebar.warning("Model file not found or incomplete locally.")
    if st.sidebar.button("Download Qwen3 4B GGUF Model (3.2GB)"):
        progress_bar = st.sidebar.progress(0.0)
        status_text = st.sidebar.empty()
        
        def update_progress(pct):
            progress_bar.progress(pct)
            status_text.text(f"Downloading: {pct*100:.1f}%")
            
        with st.spinner("Downloading model from ModelScope... Please wait."):
            download_model(MODEL_PATH, progress_callback=update_progress)
        st.sidebar.success("Model downloaded successfully! Please refresh or rerun the app.")
        st.rerun()
else:
    st.sidebar.success("Qwen3 4B GGUF Model is fully loaded and ready.")

# File Uploader
uploaded_file = st.file_uploader("Upload your document draft (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
        
    try:
        text = parse_document(tmp_path)
    finally:
        os.unlink(tmp_path)
        
    st.info(f"Loaded {len(text)} characters from {uploaded_file.name}")
    
    # Run Rules Heuristics
    rules_res = analyze_text_rules(text)
    
    st.markdown("---")
    st.subheader("📊 Track A: Structural Diagnostics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Sentence Count", rules_res["sentence_count"])
    with col2:
        st.metric("Cliché Detections", rules_res["cliche_matches"])
    with col3:
        st.metric("Length Variance", f"{rules_res['length_variance']:.1f}")
        
    if rules_res["matched_cliches"]:
        st.markdown(f"**Detected cliché patterns:** `{', '.join(rules_res['matched_cliches'])}`")
            
    # LLM Diagnostics
    st.markdown("---")
    if model_loaded:
        st.subheader("🧠 Track B & C: Model PPL & Academic Rewriting")
        if st.button("Run Deep Analysis"):
            with st.spinner("Running local token-level diagnostics with Qwen3..."):
                engine = PPLEngine(MODEL_PATH)
                judge = StyleJudge(engine.llm)
                
                for s in rules_res["sentences"]:
                    if len(s.strip()) < 5:
                        continue
                    ppl = engine.evaluate_sentence_ppl(s)
                    
                    is_suspicious = ppl < 10.0 or any(c in s.lower() for c in rules_res["matched_cliches"])
                    
                    if is_suspicious:
                        diag = judge.diagnose_sentence(s)
                        suggestion = diag.get("rewrite_suggestion", "")
                        
                        tag_html = '<span class="card-tag tag-high">AI / Translationese Risk</span>'
                        rewrite_section = f"""
                        <div class="text-rewrite">
                            <strong>✨ Recommended Academic Rewrite:</strong><br>{suggestion}
                        </div>
                        """
                    else:
                        suggestion = "-"
                        tag_html = '<span class="card-tag tag-normal">Natural Russian</span>'
                        rewrite_section = ""
                        
                    # Render Beautiful Card
                    st.markdown(f"""
                    <div class="sentence-card">
                        <div class="card-header">
                            {tag_html}
                            <span class="score-badge">PPL Score: {ppl:.2f}</span>
                        </div>
                        <div class="text-original">
                            <strong>Original draft:</strong><br>"{s}"
                        </div>
                        {rewrite_section}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("Please download the Qwen3 model in the sidebar to enable deep PPL diagnostics and rewrite suggestions.")
