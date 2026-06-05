import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import tempfile
from naturalization_layer.document_parser import parse_document
from naturalization_layer.rules_engine import analyze_text_rules, should_run_ppl_heuristic
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

.tag-protected {
    background-color: #e8f4fd;
    color: #0071e3;
}

.tag-normal {
    background-color: #f5f5f7;
    color: #86868b;
}

.card-stats {
    font-size: 0.8rem;
    color: #86868b;
    margin-top: 0.5rem;
    border-top: 1px solid #f5f5f7;
    padding-top: 0.5rem;
    display: flex;
    gap: 15px;
    align-items: center;
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

/* Custom Scrollbar for manuscript viewer */
.manuscript-viewer::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
.manuscript-viewer::-webkit-scrollbar-track {
    background: transparent;
}
.manuscript-viewer::-webkit-scrollbar-thumb {
    background: #d2d2d7;
    border-radius: 3px;
}
.manuscript-viewer::-webkit-scrollbar-thumb:hover {
    background: #86868b;
}

/* Sticky right column for manuscript viewer */
.manuscript-viewer {
    position: -webkit-sticky;
    position: sticky;
    top: 2rem;
    max-height: 80vh;
    overflow-y: auto;
    padding: 1.5rem;
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.015);
    line-height: 1.8;
    color: #1d1d1f;
    font-size: 1.05rem;
}

/* Highlights for manuscript */
.highlight-high {
    background-color: #ffeef0;
    border-bottom: 2px solid #ff3b30;
    color: #ff3b30;
    font-weight: 500;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
}
.highlight-high:hover {
    background-color: #ffd1d6;
}

.highlight-medium {
    background-color: #fff9e6;
    border-bottom: 2px solid #ff9500;
    color: #b25900;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
}
.highlight-medium:hover {
    background-color: #ffe8b3;
}

.highlight-protected {
    background-color: #e8f4fd;
    border-bottom: 2px solid #0071e3;
    color: #0071e3;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
}
.highlight-protected:hover {
    background-color: #cfe8fc;
}

.highlight-normal {
    color: #1d1d1f;
    padding: 2px 4px;
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

# Scanning Control Parameters
scan_mode = "Hybrid Probe (混合模式)"
heuristic_depth = "Smart Probe (均衡模式)"
min_words = 6
smart_words = 12
fast_words = 18
early_exit_tokens = 6
early_exit_threshold = 30.0

if model_loaded:
    with st.sidebar.expander("⚙️ Advanced Scanner Settings (扫描模式与阈值调优)", expanded=True):
        st.markdown("### 1. 扫描模式选择")
        scan_mode = st.radio(
            "Scanning Mode (扫描模式)",
            ["Hybrid Probe (混合模式)", "Heuristic Only (仅启发式)", "Early-Exit Only (仅早期退出)"],
            index=0,
            help="""
            - 混合模式 (默认且推荐)：先通过启发式字数/套话过滤句子，对通过者进行模型前缀探测，若自然则提前退出。兼顾算力与精度。
            - 仅启发式：纯文本分析，通过句长与模板匹配，完全跳过前缀快速退出探测。
            - 仅早期退出：除公式与超短句外全量送入模型，完全依赖前缀 token 的 PPL 进行早期退出。
            """
        )
        st.caption("**💡 混合模式**：最省算力且兼顾精度。**仅启发式**：仅靠字数和套话过滤。**仅早期退出**：纯模型快速退出。")
        
        st.markdown("### 2. Heuristic 过滤深度 (选项1)")
        heuristic_depth = st.selectbox(
            "Heuristic Filter Depth (过滤深度)",
            ["Smart Probe (均衡模式)", "Deep Scan (全量深检)", "Fast Check (极速模式)"],
            index=0,
            help="""
            - 均衡模式 (默认)：仅扫描中长句（字数 >= smart_words）或包含 AI 套话的句子。
            - 全量深检：除极短句外，全量句子深度扫描。
            - 极速模式：仅扫描超长句（字数 >= fast_words）或包含 AI 套话的句子。
            """
        )
        st.caption("**💡 均衡模式**：均衡中长句与套话句。**全量深检**：除极短句外全扫描。**极速模式**：仅扫特长句。")
        
        st.markdown("### 3. 字数与模型阈值自定义")
        with st.container():
            min_words = st.slider(
                "Min words (豁免超短句字数)", 
                1, 30, 6,
                help="小于此字数的句子（如单句词组）被视为过于简单，直接豁免，不进入大模型。"
            )
            smart_words = st.slider(
                "Smart Probe threshold (均衡模式触发字数)", 
                5, 40, 12,
                help="均衡模式下，句子字数达到此值时触发 PPL 模型探测。"
            )
            fast_words = st.slider(
                "Fast Check threshold (极速模式触发字数)", 
                10, 50, 18,
                help="极速模式下，句子字数达到此值时才触发 PPL 模型探测。"
            )
            
            st.markdown("---")
            st.markdown("**早期退出模型阈值 (选项2)**")
            early_exit_tokens = st.slider(
                "Early-exit tokens (前缀探针字数)", 
                1, 20, 6,
                help="仅计算句子开头的这一数量的 Token。如果前缀表现非常自然，则视为安全退出。"
            )
            early_exit_threshold = st.slider(
                "Early-exit PPL threshold", 
                10.0, 100.0, 30.0, step=5.0,
                help="前缀 PPL 大于此值（越大于自然）时，触发早期退出。推荐值为 30.0。"
            )

mode_map = {
    "Hybrid Probe (混合模式)": "Hybrid",
    "Heuristic Only (仅启发式)": "Heuristic",
    "Early-Exit Only (仅早期退出)": "Early-Exit"
}
depth_map = {
    "Smart Probe (均衡模式)": "Smart Probe",
    "Deep Scan (全量深检)": "Deep Scan",
    "Fast Check (极速模式)": "Fast Check"
}
selected_mode = mode_map[scan_mode]
selected_depth = depth_map[heuristic_depth]

# File Uploader
uploaded_file = st.file_uploader("Upload your document draft (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])

if uploaded_file is not None:
    # Clear cache if uploading a new file
    if st.session_state.get("last_uploaded_file_name") != uploaded_file.name:
        st.session_state["last_uploaded_file_name"] = uploaded_file.name
        if "analysis_results" in st.session_state:
            del st.session_state["analysis_results"]
            
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
        
    try:
        text = parse_document(tmp_path)
    finally:
        os.unlink(tmp_path)
        
    st.info(f"Loaded {len(text)} characters from {uploaded_file.name}")
    
    # Run fast Rules Heuristics (Track A)
    rules_res = analyze_text_rules(text)
    
    if "analysis_results" not in st.session_state:
        st.markdown("---")
        if model_loaded:
            st.subheader("🧠 Deep Diagnostics Scanner")
            st.warning("Deep Diagnostics is ready to run. This will evaluate sentence complexity, predictability (PPL), and execute stylistic corrections.")
            if st.button("Run Deep Analysis"):
                with st.spinner("Running local token-level diagnostics with Qwen3..."):
                    engine = PPLEngine(MODEL_PATH)
                    judge = StyleJudge(engine.llm)
                    
                    results = []
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()
                    
                    # Live update placeholders
                    live_metrics_placeholder = st.empty()
                    live_issues_placeholder = st.empty()
                    
                    live_issues_list = []
                    scanned_count = 0
                    skipped_count = 0
                    early_exit_count = 0
                    suspicious_count = 0
                    
                    for i, s in enumerate(rules_res["sentences"]):
                        progress_pct = (i + 1) / len(rules_res["sentences"])
                        progress_bar.progress(progress_pct)
                        status_text.markdown(f"**⏳ 正在扫描第 {i+1}/{len(rules_res['sentences'])} 句：** *\"{s[:120]}...\"*")
                        
                        if len(s.strip()) < 5:
                            continue
                        
                        diag_rules = rules_res["sentence_diagnostics"][i]
                        
                        # 1. Check Heuristic Filter (Mode 1 & Mode 3)
                        run_ppl = True
                        if selected_mode in ["Heuristic", "Hybrid"]:
                            run_ppl = should_run_ppl_heuristic(
                                diag_rules, 
                                selected_depth,
                                min_words=min_words,
                                smart_words=smart_words,
                                fast_words=fast_words
                            )
                            
                        ppl = None
                        was_early_exited = False
                        is_suspicious = False
                        issues = []
                        safe_to_rewrite = True
                        
                        if not run_ppl:
                            skipped_count += 1
                        else:
                            scanned_count += 1
                            # 2. Check Early-Exit Probe (Mode 2 & Mode 3)
                            ee_tokens = early_exit_tokens if selected_mode in ["Early-Exit", "Hybrid"] else 0
                            ee_threshold = early_exit_threshold if selected_mode in ["Early-Exit", "Hybrid"] else 0.0
                            
                            ppl, was_early_exited = engine.evaluate_sentence_ppl(
                                s, 
                                early_exit_tokens=ee_tokens, 
                                early_exit_threshold=ee_threshold
                            )
                            
                            if was_early_exited:
                                early_exit_count += 1
                                is_suspicious = False
                            else:
                                is_suspicious = ppl < 15.0 or len(diag_rules["cliches_found"]) > 0 or len(diag_rules["genitive_chains"]) > 0 or diag_rules["nv_ratio"] > 4.0
                                
                                if is_suspicious:
                                    diag = judge.diagnose_sentence(s, stats=diag_rules, ppl=ppl)
                                    issues = diag.get("issues", [])
                                    safe_to_rewrite = diag.get("safe_to_rewrite", True)
                                    
                                    if issues:
                                        suspicious_count += 1
                                        live_issues_list.append({
                                            "text": s,
                                            "ppl": ppl,
                                            "issues": issues,
                                            "diag_rules": diag_rules
                                        })
                        
                        # Update live metrics placeholder
                        with live_metrics_placeholder.container():
                            st.markdown("### 📊 实时分析指标 (Live Metrics)")
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("已扫描句子 (Scanned)", scanned_count)
                            c2.metric("算力豁免 (Skipped)", skipped_count)
                            c3.metric("首部早期退出 (Early Exited)", early_exit_count)
                            c4.metric("已发现风险句 (Issues)", suspicious_count)
                            
                        # Update live issue cards
                        if live_issues_list:
                            with live_issues_placeholder.container():
                                st.markdown("### ⚠️ 实时诊断流 (Live Diagnostic Stream)")
                                # Show last 3 issues to keep UI snappy
                                for item in live_issues_list[-3:]:
                                    for issue in item["issues"]:
                                        issue_type = issue.get("issue_type", "style_risk").replace("_", " ").upper()
                                        severity = issue.get("severity", "medium").lower()
                                        explanation_zh = issue.get("explanation_zh", "")
                                        rewrite_suggestion = issue.get("rewrite_suggestion", "")
                                        
                                        tag_class = "tag-high" if severity == "high" else "tag-normal"
                                        ppl_str = f"{item['ppl']:.2f}" if item["ppl"] is not None else "N/A"
                                        
                                        st.markdown(f"""
                                        <div class="sentence-card">
                                            <div class="card-header">
                                                <span class="card-tag {tag_class}">{issue_type} ({severity.upper()})</span>
                                                <span class="score-badge">PPL: {ppl_str}</span>
                                            </div>
                                            <div class="text-original" style="border-left: 3px solid #ff3b30;">
                                                <strong>Original draft:</strong><br>"{item['text']}"
                                            </div>
                                            <div style="margin-top: 10px; font-size: 0.85rem; color: #1d1d1f; background-color: #fff9f9; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                                                <strong>诊断解释 (ZH):</strong> {explanation_zh}
                                            </div>
                                            <div class="text-rewrite">
                                                <strong>✨ Recommended Academic Rewrite:</strong><br>{rewrite_suggestion}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                        results.append({
                            "index": i,
                            "text": s,
                            "ppl": ppl,
                            "was_early_exited": was_early_exited,
                            "run_ppl": run_ppl,
                            "diag_rules": diag_rules,
                            "is_suspicious": is_suspicious,
                            "issues": issues,
                            "safe_to_rewrite": safe_to_rewrite
                        })
                    
                    st.session_state["analysis_results"] = results
                    status_text.empty()
                    progress_bar.empty()
                    live_metrics_placeholder.empty()
                    live_issues_placeholder.empty()
                    st.rerun()
        else:
            st.warning("Please download the Qwen3 model in the sidebar to enable deep PPL and rewrite suggestions.")
            
    # Display Results if Cached
    if "analysis_results" in st.session_state:
        results = st.session_state["analysis_results"]
        
        # Calculate statistics
        total_sents = len(results)
        skipped_sents = sum(1 for r in results if not r["run_ppl"])
        early_exited_sents = sum(1 for r in results if r["was_early_exited"])
        suspicious_sents = sum(1 for r in results if r["is_suspicious"] and r["issues"])
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sentences", total_sents)
        with col2:
            st.metric("Heuristic Skipped (算力豁免)", skipped_sents)
        with col3:
            st.metric("Early Exited (早期退出)", early_exited_sents)
        with col4:
            st.metric("Detected Issues (诊断风险句)", suspicious_sents)
            
        # 2. Main layout: Dual Columns
        st.markdown("---")
        left_col, right_col = st.columns([5, 7])
        
        with left_col:
            st.markdown("### 🔍 Filter Diagnostics")
            severity_filter = st.multiselect(
                "Filter by Severity (按严重度筛选)", 
                ["high", "medium", "low"], 
                default=["high", "medium", "low"]
            )
            issue_type_filter = st.multiselect(
                "Filter by Issue Type (按问题类型筛选)", 
                ["ai_generated_suspicion", "machine_translation_cliche", "style_heavy", "semantic_redundancy", "other_risk"],
                default=["ai_generated_suspicion", "machine_translation_cliche", "style_heavy"]
            )
            keyword_search = st.text_input("Search keyword in original draft (关键字搜索)").strip().lower()
            
            # Show filterable issue cards
            st.markdown("### 📋 Diagnostic Cards")
            
            # Filter results in memory
            visible_card_indices = set()
            for r in results:
                if keyword_search and keyword_search not in r["text"].lower():
                    continue
                
                if r["is_suspicious"] and r["issues"]:
                    matched_issues = []
                    for issue in r["issues"]:
                        sev = issue.get("severity", "medium").lower()
                        itype = issue.get("issue_type", "other_risk").lower()
                        if sev in severity_filter and itype in issue_type_filter:
                            matched_issues.append(issue)
                    
                    if matched_issues:
                        visible_card_indices.add(r["index"])
                        
                        for issue in matched_issues:
                            issue_type = issue.get("issue_type", "style_risk").replace("_", " ").upper()
                            severity = issue.get("severity", "medium").lower()
                            explanation_zh = issue.get("explanation_zh", "")
                            explanation_ru = issue.get("explanation_ru", "")
                            evidence = issue.get("evidence", "")
                            rewrite_suggestion = issue.get("rewrite_suggestion", "")
                            
                            tag_class = "tag-high" if severity == "high" else "tag-normal"
                            
                            evidence_html = f"<div><strong>Evidence:</strong> <code style='color: #ff3b30;'>{evidence}</code></div>" if evidence else ""
                            ppl_str = f"{r['ppl']:.2f}" if r["ppl"] is not None else "N/A"
                            
                            st.markdown(f"""
                            <div class="sentence-card" id="card_{r['index']}">
                                <div class="card-header">
                                    <span class="card-tag {tag_class}">{issue_type} ({severity.upper()})</span>
                                    <span class="score-badge">PPL: {ppl_str}</span>
                                </div>
                                <div class="text-original" style="border-left: 3px solid #ff3b30;">
                                    <strong>Original draft:</strong><br>"{r['text']}"
                                </div>
                                <div style="margin-top: 10px; font-size: 0.85rem; color: #1d1d1f; background-color: #fff9f9; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                                    {evidence_html}
                                    <div style="margin-top: 5px;"><strong>诊断解释 (ZH):</strong> {explanation_zh}</div>
                                    <div style="margin-top: 5px; color: #6e6e73;"><strong>Explanation (RU):</strong> {explanation_ru}</div>
                                </div>
                                <div class="text-rewrite">
                                    <strong>✨ Recommended Academic Rewrite:</strong><br>{rewrite_suggestion}
                                </div>
                                <div class="card-stats">
                                    <span>📊 N/V: {r['diag_rules']['nv_ratio']}</span>
                                    <span>🔒 Passive: {r['diag_rules']['passive_count']}</span>
                                    <a href="#doc_sent_{r['index']}" style="margin-left: auto; text-decoration: none; color: #0071e3; font-weight: 500;">Locate in Draft ↑</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
            if not visible_card_indices:
                st.info("No issue cards match the active filters.")
                
            if st.button("Reset Analysis Cache (清除分析缓存)"):
                if "analysis_results" in st.session_state:
                    del st.session_state["analysis_results"]
                st.rerun()
                
        with right_col:
            st.markdown("### 📝 Sticky Manuscript Viewer")
            
            # Construct highlighted HTML
            html_content = []
            for r in results:
                if r["index"] in visible_card_indices:
                    severity = "medium"
                    for issue in r["issues"]:
                        if issue.get("severity", "medium").lower() == "high":
                            severity = "high"
                            break
                    
                    highlight_class = "highlight-high" if severity == "high" else "highlight-medium"
                    html_content.append(f"""<a href="#card_{r['index']}" style="color: inherit; text-decoration: none;"><span class="{highlight_class}" id="doc_sent_{r['index']}" title="Click to view card details">{r['text']}</span></a>""")
                elif r["diag_rules"].get("is_protected", False):
                    html_content.append(f"""<span class="highlight-protected" id="doc_sent_{r['index']}" title="Protected Formula/Ref">{r['text']}</span>""")
                else:
                    html_content.append(f"""<span class="highlight-normal" id="doc_sent_{r['index']}">{r['text']}</span>""")
            
            full_html = " ".join(html_content)
            
            st.markdown(f"""
            <div class="manuscript-viewer">
                {full_html}
            </div>
            """, unsafe_allow_html=True)
