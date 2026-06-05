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

st.set_page_config(page_title="Academic Russian Naturalizer", layout="wide")
st.title("🇷🇺 Academic Russian Style Diagnostics & Naturalization")

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "Qwen3-4B-Q5_K_M.gguf")

# Sidebar for Model Status
st.sidebar.header("Model Management")
if not os.path.exists(MODEL_PATH):
    st.sidebar.warning("Model file not found locally.")
    if st.sidebar.button("Download Qwen3 4B GGUF Model (3.2GB)"):
        progress_bar = st.sidebar.progress(0.0)
        status_text = st.sidebar.empty()
        
        def update_progress(pct):
            progress_bar.progress(pct)
            status_text.text(f"Downloading: {pct*100:.1f}%")
            
        with st.spinner("Downloading model from ModelScope... Please wait."):
            download_model(MODEL_PATH, progress_callback=update_progress)
        st.sidebar.success("Model downloaded successfully!")
else:
    st.sidebar.success("Qwen 3B GGUF Model is loaded.")

# File Uploader
uploaded_file = st.file_uploader("Upload draft (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])

if uploaded_file is not None:
    # Save to temp file to read
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Track A: Structural Diagnostics")
        st.metric("Sentence Count", rules_res["sentence_count"])
        st.metric("Cliché Detections", rules_res["cliche_matches"])
        if rules_res["matched_cliches"]:
            st.write("Matched clichés:", rules_res["matched_cliches"])
            
    # LLM Diagnostics if model exists
    if os.path.exists(MODEL_PATH):
        st.subheader("🧠 Track B & C: Model PPL & Academic Rewriting")
        if st.button("Run Deep Analysis"):
            engine = PPLEngine(MODEL_PATH)
            judge = StyleJudge(engine.llm)
            
            results = []
            for s in rules_res["sentences"]:
                ppl = engine.evaluate_sentence_ppl(s)
                suggestion = "-"
                # Check for low PPL (unnatural smoothness)
                if ppl < 10.0 or any(c in s.lower() for c in rules_res["matched_cliches"]):
                    diag = judge.diagnose_sentence(s)
                    suggestion = diag.get("rewrite_suggestion", "-")
                results.append({"Sentence": s, "PPL": f"{ppl:.2f}", "Rewrite Suggestion": suggestion})
                
            st.table(results)
    else:
        st.warning("Please download the Qwen model in the sidebar to enable deep PPL and rewrite suggestions.")
