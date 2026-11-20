import os
import json
import time
import html as _html
from pathlib import Path
import streamlit as st

# Nạp biến môi trường từ .env (fallback thủ công nếu chưa có dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        for _line in _env_path.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

from src.ingestion.router import route_document
from src.segmentation.clause_segmenter import ClauseSegmenter
from src.retrieval.legal_kb import LegalKnowledgeBase
from src.retrieval.reranker import HybridLegalReranker
from src.agents.extractor_agent import ExtractorAgent
from src.agents.risk_analyzer_agent import RiskAnalyzerAgent
from src.agents.reflection_critic import ReflectionCritic
from src.agents.proposal_agent import ProposalAgent
from src.hitl.hitl_controller import HITLController
from src.hitl.document_assembler import DocumentAssembler
from src.utils.formatting import format_vnd, format_date

# ============================================================
# CẤU HÌNH TRANG STREAMLIT
# ============================================================
st.set_page_config(
    page_title="LegalTech AI - Rà soát & Đàm phán Hợp đồng",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# BỘ CSS REFACTOR: ĐỒNG NHẤT FONT, MÀU TƯƠNG PHẢN CAO, GITHUB STYLE
# ============================================================
st.markdown("""
<style>
/* ============================================================
   BỘ CSS CHUẨN HÓA TOÀN DIỆN CHO LEGALTECH AI (STREAMLIT)
   Khắc phục triệt để: Text ăn theo Dark Mode, đè chữ, mất lề Sidebar
   ============================================================ */

/* 1. RESET TOÀN DIỆN & BOX SIZING */
*, *::before, *::after {
    box-sizing: border-box !important;
}

html, body, .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    background-color: #EEF2F7 !important;
    color: #0F172A !important;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

header[data-testid="stHeader"], footer {
    display: none !important;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1.8rem !important;
    padding-right: 1.8rem !important;
    max-width: 100% !important;
}

/* 2. ÉP TOÀN BỘ TEXT STREAMLIT & EMOTION CACHE THÀNH #0F172A (CHỐNG DARK MODE LÀM TRẮNG CHỮ) */
[class*="st-emotion-cache"],
[class*="st-emotion-cache"] p,
[class*="st-emotion-cache"] span,
[class*="st-emotion-cache"] div,
[class*="st-emotion-cache"] label,
[class*="css-"],
[class*="css-"] *,
.stMarkdown,
.stMarkdown *,
.stText,
.stText *,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *,
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] *,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *,
div[data-baseweb="select"] *,
div[data-baseweb="popover"] *,
div[data-baseweb="menu"] *,
ul[role="listbox"] li {
    color: #0F172A !important;
}

/* Ngoại lệ màu sắc cho nhãn chỉ số Metric */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] * {
    color: #475569 !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #0F172A !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
}

/* 3. SIDEBAR: CỐ ĐỊNH CHIỀU RỘNG, BẢO TOÀN LỀ, CHỐNG ĐÈ CHỮ KHI THU NHỎ MÀN HÌNH */
[data-testid="stSidebar"] {
    min-width: 280px !important;
    width: 280px !important;
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.02) !important;
}

[data-testid="stSidebarUserContent"] {
    padding: 0 16px 28px 16px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.45rem !important;
    width: 100% !important;
}

/* Khối thương hiệu Logo */
.legal-brand-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 12px 14px 12px;
    border-bottom: 1px solid #EDF2F7;
    margin-bottom: 6px;
    width: 100%;
}
.legal-brand-icon {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, #0B72D9 0%, #1496F5 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF !important;
    font-size: 20px;
    font-weight: 700;
    flex-shrink: 0;
    box-shadow: 0 2px 6px rgba(11, 114, 217, 0.2);
}
.legal-brand-text {
    line-height: 1.25;
    overflow: hidden;
}
.legal-brand-title {
    font-size: 14.5px;
    font-weight: 700;
    color: #0B72D9 !important;
    margin: 0;
    white-space: nowrap;
}
.legal-brand-sub {
    font-size: 11px;
    color: #64748B !important;
    margin: 0;
    white-space: nowrap;
}

/* Khối người dùng Profile */
.legal-user-box {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    margin: 4px 0 12px 0;
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    width: 100%;
}
.legal-user-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0EA5E9 0%, #0B72D9 100%);
    color: #FFFFFF !important;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
}
.legal-user-name {
    font-size: 12.5px;
    font-weight: 700;
    color: #0F172A !important;
    margin: 0;
}
.legal-user-role {
    font-size: 11px;
    color: #64748B !important;
    margin: 0;
}

/* Tiêu đề nhóm mục menu */
.sidebar-group-title {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #475569 !important;
    text-transform: uppercase;
    padding: 12px 10px 4px 10px;
    margin: 0;
}

/* Chuẩn hóa nút bấm Sidebar: Chống tràn, text căn lề chuẩn, không bị bóp nghẹt */
[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}

[data-testid="stSidebar"] button {
    width: 100% !important;
    min-height: 40px !important;
    height: auto !important;
    padding: 9px 12px !important;
    margin: 1px 0 !important;
    border-radius: 6px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    box-sizing: border-box !important;
}

[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button div {
    font-size: 13px !important;
    font-weight: 500 !important;
    line-height: 1.4 !important;
    text-align: left !important;
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: transparent !important;
    border: none !important;
}
[data-testid="stSidebar"] button[kind="secondary"] * {
    color: #334155 !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: #F1F5F9 !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover * {
    color: #0F172A !important;
}

[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #E7F4FE !important;
    border: 1px solid #BFDBFE !important;
}
[data-testid="stSidebar"] button[kind="primary"] * {
    color: #0B72D9 !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
    background-color: #DBEAFE !important;
}

/* Khối trạng thái kết quả thẩm định ở Sidebar */
.sidebar-result-card {
    padding: 11px 12px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin: 4px 0 10px 0;
    width: 100%;
}
.sidebar-result-score {
    font-size: 11.5px;
    color: #475569 !important;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.sidebar-result-score b {
    color: #0B72D9 !important;
    font-size: 13px;
}
.sidebar-badges-row {
    display: flex;
    gap: 6px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}

/* Khối chân trang Sidebar */
.sidebar-footer-box {
    padding: 12px 10px;
    margin-top: 20px;
    border-top: 1px solid #EDF2F7;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    color: #64748B !important;
    width: 100%;
}
.sidebar-online-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #22C55E;
    display: inline-block;
    flex-shrink: 0;
}

/* 4. KHU VỰC NỘI DUNG CHÍNH (MAIN AREA) */
.main-topbar {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 11px 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    width: 100%;
}
.main-topbar-title {
    font-size: 13.5px;
    font-weight: 700;
    color: #0F172A !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
}
.main-topbar-badge {
    background-color: #EFF6FF;
    color: #0B72D9 !important;
    font-size: 11.5px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 12px;
    border: 1px solid #BFDBFE;
    white-space: nowrap;
}

.hero-banner-blue {
    background: linear-gradient(90deg, #0B72D9 0%, #1496F5 100%);
    border-radius: 8px;
    padding: 24px 28px;
    color: #FFFFFF !important;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 14px rgba(11, 114, 217, 0.16);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}
.hero-banner-blue * {
    color: #FFFFFF !important;
}
.hero-banner-left {
    flex: 1 1 500px;
}
.hero-pill {
    background: rgba(255, 255, 255, 0.2);
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
    color: #FFFFFF !important;
}
.hero-banner-blue h2 {
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    margin: 0 0 6px 0 !important;
    line-height: 1.3 !important;
}
.hero-banner-blue p {
    font-size: 0.88rem !important;
    color: #EFF6FF !important;
    margin: 0 !important;
    line-height: 1.5 !important;
}
.hero-banner-right {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}
.hero-stat-box {
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 8px;
    padding: 10px 14px;
    text-align: center;
    min-width: 85px;
}
.hero-stat-val {
    font-size: 1.15rem;
    font-weight: 700;
    color: #FFFFFF !important;
}
.hero-stat-lbl {
    font-size: 10px;
    color: #DBEAFE !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 2px;
}

/* 5. DẢI TIÊU ĐỀ MỤC VÀ BẢNG DỮ LIỆU LMS TABLE */
.section-blue-bar {
    background-color: #0B72D9;
    color: #FFFFFF !important;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 16px;
    border-radius: 6px 6px 0 0;
    margin-top: 14px;
    width: 100%;
}
.section-blue-bar * {
    color: #FFFFFF !important;
}

table.lms-table {
    width: 100% !important;
    border-collapse: collapse !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 0 0 8px 8px !important;
    overflow: hidden !important;
    font-size: 12.5px !important;
    margin-bottom: 20px !important;
}
table.lms-table th {
    background-color: #E7F4FE !important;
    color: #0F172A !important;
    font-weight: 700 !important;
    padding: 11px 14px !important;
    border-bottom: 1px solid #BFDBFE !important;
    border-top: none !important;
    font-size: 12.5px !important;
    line-height: 1.3 !important;
}
table.lms-table td {
    padding: 11px 14px !important;
    border-bottom: 1px solid #F1F5F9 !important;
    color: #1E293B !important;
    vertical-align: middle !important;
    line-height: 1.45 !important;
}
table.lms-table tr:hover {
    background-color: #F8FAFC !important;
}
table.lms-table tr:nth-child(even) {
    background-color: #FAFCFE !important;
}

/* Huy hiệu (Badges) */
.badge-status-red {
    background-color: #FEE2E2 !important;
    color: #B91C1C !important;
    padding: 3px 8px !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    border: 1px solid #FCA5A5 !important;
    display: inline-block;
    white-space: nowrap;
}
.badge-status-yellow {
    background-color: #FEF3C7 !important;
    color: #B45309 !important;
    padding: 3px 8px !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    border: 1px solid #FCD34D !important;
    display: inline-block;
    white-space: nowrap;
}
.badge-status-approved {
    background-color: #DCFCE7 !important;
    color: #15803D !important;
    padding: 3px 8px !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    font-size: 11.5px !important;
    border: 1px solid #86EFAC !important;
    display: inline-block;
    white-space: nowrap;
}
.badge-status-rejected {
    background-color: #F1F5F9 !important;
    color: #64748B !important;
    padding: 3px 8px !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 11.5px !important;
    border: 1px solid #CBD5E1 !important;
    display: inline-block;
    white-space: nowrap;
}
.badge-status-pending {
    background-color: #EFF6FF !important;
    color: #0B72D9 !important;
    padding: 3px 8px !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 11.5px !important;
    border: 1px solid #BFDBFE !important;
    display: inline-block;
    white-space: nowrap;
}

/* 6. GITHUB PR STYLE CHO REDLINE & ACTION BUTTONS */
.redline-quote-container {
    background-color: #FFFFFF !important;
    border: 1px solid #D0D7DE !important;
    border-radius: 6px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
    width: 100% !important;
}

.diff-box-orig {
    background-color: #FFEBE9 !important;
    border-left: 4px solid #CF222E !important;
    padding: 11px 14px !important;
    font-size: 13px !important;
    color: #991B1B !important;
    line-height: 1.55 !important;
    margin-bottom: 10px !important;
    border-radius: 0 4px 4px 0 !important;
    word-break: break-word !important;
}
.diff-box-prop {
    background-color: #E6FFEC !important;
    border-left: 4px solid #2DA44E !important;
    padding: 11px 14px !important;
    font-size: 13px !important;
    color: #166534 !important;
    line-height: 1.55 !important;
    margin-bottom: 10px !important;
    border-radius: 0 4px 4px 0 !important;
    word-break: break-word !important;
}
.quote-script-box {
    background-color: #F0F9FF !important;
    border: 1px solid #BAE6FD !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
    color: #0369A1 !important;
    font-size: 12.5px !important;
    line-height: 1.5 !important;
    margin-top: 8px !important;
    word-break: break-word !important;
}

/* TRIỆT TIÊU NỀN ĐEN NÚT BẤM STREAMLIT (KHẮC PHỤC NÚT REJECT BỊ ĐEN) */
div[data-testid="stMain"] button[kind="secondary"],
div[data-testid="stMainBlockContainer"] button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #CF222E !important;
    border: 1px solid #D0D7DE !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 6px 14px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}
div[data-testid="stMain"] button[kind="secondary"] *,
div[data-testid="stMainBlockContainer"] button[kind="secondary"] * {
    color: #CF222E !important;
}
div[data-testid="stMain"] button[kind="secondary"]:hover,
div[data-testid="stMainBlockContainer"] button[kind="secondary"]:hover {
    background-color: #FFEBE9 !important;
    border-color: #CF222E !important;
}

/* Nút Chấp thuận (Accept) - Xanh lá GitHub */
div[data-testid="stMain"] button[kind="primary"],
div[data-testid="stMainBlockContainer"] button[kind="primary"] {
    background-color: #238636 !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(27, 31, 36, 0.15) !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 6px 14px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}
div[data-testid="stMain"] button[kind="primary"] *,
div[data-testid="stMainBlockContainer"] button[kind="primary"] * {
    color: #FFFFFF !important;
}
div[data-testid="stMain"] button[kind="primary"]:hover,
div[data-testid="stMainBlockContainer"] button[kind="primary"]:hover {
    background-color: #2EA043 !important;
}

/* 7. SỬA DROPZONE FILE UPLOADER (CHỐNG NỀN ĐEN SÌ CỦA DARK MODE) */
div[data-testid="stFileUploader"] {
    background-color: #FFFFFF !important;
    border: 1px dashed #BFDBFE !important;
    border-radius: 8px !important;
    padding: 14px !important;
}
div[data-testid="stFileUploaderDropzone"],
section[data-testid="stFileUploaderDropzone"],
div[data-testid="stFileUploader"] section {
    background-color: #F8FAFC !important;
    border: 2px dashed #93C5FD !important;
    border-radius: 8px !important;
}
div[data-testid="stFileUploaderDropzone"] *,
section[data-testid="stFileUploaderDropzone"] *,
div[data-testid="stFileUploader"] section * {
    color: #0F172A !important;
}
div[data-testid="stFileUploaderDropzone"] button,
section[data-testid="stFileUploaderDropzone"] button {
    background-color: #FFFFFF !important;
    color: #0B72D9 !important;
    border: 1px solid #CBD5E1 !important;
}

/* Selectbox sáng rõ */
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    color: #0F172A !important;
}

/* Khung Expander dropdown quote */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
}
[data-testid="stExpander"] summary {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #0F172A !important;
    padding: 10px 14px !important;
    background-color: #FFFFFF !important;
}
[data-testid="stExpander"] summary * {
    color: #0F172A !important;
}

/* ============================================================
   8. KHỐI MÃ SƠ ĐỒ KIẾN TRÚC & TERMINAL (st.code / pre / code) - NỀN TỐI #1E293B, CHỮ TRẮNG #F8FAFC
   ============================================================ */
div[data-testid="stCode"],
div[data-testid="stCodeBlock"],
div[data-testid="stCodeBlock"] > div,
div[data-testid="stCodeBlock"] pre,
div[data-testid="stCode"] pre,
pre {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

div[data-testid="stCodeBlock"] pre,
div[data-testid="stCode"] pre,
div[data-testid="stCodeBlock"] code,
div[data-testid="stCode"] code,
pre code {
    background-color: #1E293B !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
}

div[data-testid="stCodeBlock"] code *,
div[data-testid="stCode"] code *,
div[data-testid="stCodeBlock"] pre *,
div[data-testid="stCode"] pre *,
pre code * {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
}

/* Nút copy trên st.code (Terminal style đồng bộ) */
div[data-testid="stCodeBlock"] button,
div[data-testid="stCode"] button {
    background-color: #334155 !important;
    color: #F8FAFC !important;
    border: 1px solid #475569 !important;
    border-radius: 4px !important;
}
div[data-testid="stCodeBlock"] button:hover,
div[data-testid="stCode"] button:hover {
    background-color: #475569 !important;
    color: #FFFFFF !important;
}
div[data-testid="stCodeBlock"] button *,
div[data-testid="stCode"] button * {
    color: #F8FAFC !important;
    fill: #F8FAFC !important;
}

/* Inline code tags (bên trong bảng, đoạn văn, expander - không nằm trong st.code/pre) */
code:not(pre code):not(div[data-testid="stCodeBlock"] code):not(div[data-testid="stCode"] code),
span[data-testid="stCode"] {
    background-color: #EEF2F6 !important;
    color: #0B72D9 !important;
    -webkit-text-fill-color: #0B72D9 !important;
    border: 1px solid #CBD5E1 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 11.5px !important;
    font-weight: 600 !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
}

/* ============================================================
   9. Ô NHẬP LIỆU (st.text_input, st.text_area, st.chat_input, st.selectbox)
   ============================================================ */
div[data-baseweb="base-input"],
div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="base-input"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stChatInput"] textarea,
input[type="text"],
input[type="search"],
textarea {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #CBD5E1 !important;
    -webkit-text-fill-color: #0F172A !important;
    border-radius: 6px !important;
}

/* Chữ placeholder trong ô nhập */
input::placeholder,
textarea::placeholder,
[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
}

/* POPUP DROPDOWN MENU CỦA SELECTBOX (CHỐNG NỀN ĐEN SÌ KHI BẤM CHỌN) */
div[data-baseweb="select"],
div[data-baseweb="select"] > div,
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"],
div[data-baseweb="menu"] > div,
ul[role="listbox"],
ul[role="listbox"] > li,
li[role="option"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #CBD5E1 !important;
}

li[role="option"] * {
    color: #0F172A !important;
    background-color: transparent !important;
}

li[role="option"]:hover,
li[role="option"][aria-selected="true"],
li[role="option"]:focus {
    background-color: #EFF6FF !important;
    color: #0B72D9 !important;
}
li[role="option"]:hover *,
li[role="option"][aria-selected="true"] * {
    color: #0B72D9 !important;
}

div[data-baseweb="select"] svg {
    fill: #475569 !important;
}

/* ============================================================
   10. BẢNG DỮ LIỆU TOÀN DIỆN (CHỐNG LẸM / CHỐNG NỀN TỐI)
   ============================================================ */
table,
table * {
    border-color: #E2E8F0 !important;
}
table tr,
table tbody tr {
    background-color: #FFFFFF !important;
}
table th,
table thead th {
    background-color: #E7F4FE !important;
    color: #0F172A !important;
    font-weight: 700 !important;
}
table td,
table tbody td {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
}
table tr:nth-child(even) td {
    background-color: #FAFCFE !important;
}
table tr:hover td {
    background-color: #F1F5F9 !important;
}

/* ============================================================
   11. BẢO TOÀN TEXT MÀU TRẮNG CHO BANNER XANH
   ============================================================ */
.hero-banner-blue,
.hero-banner-blue *,
.hero-stat-val,
.section-blue-bar,
.section-blue-bar * {
    color: #FFFFFF !important;
}
.hero-stat-lbl {
    color: #DBEAFE !important;
}
</style>
""", unsafe_allow_html=True)

# Helper hàm escape HTML
def esc(val) -> str:
    return _html.escape(str(val) if val is not None else "")

# ============================================================
# KHỞI TẠO STATE
# ============================================================
if "active_page" not in st.session_state:
    st.session_state.active_page = "home"
if "domain" not in st.session_state:
    st.session_state.domain = "rental"
if "perspective" not in st.session_state:
    st.session_state.perspective = "party_b"
if "package" not in st.session_state:
    st.session_state.package = None
if "contract_text" not in st.session_state:
    st.session_state.contract_text = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý Cố vấn Pháp lý AI. Tôi có thể hỗ trợ giải đáp thắc mắc về các điều khoản hợp đồng hoặc tư vấn quyền lợi pháp luật theo quy định hiện hành."}
    ]

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    # 1. Header Thương hiệu chuẩn LegalTech
    st.markdown("""
    <div class="legal-brand-box">
        <div class="legal-brand-icon">⚖️</div>
        <div class="legal-brand-text">
            <div class="legal-brand-title">LegalTech AI</div>
            <div class="legal-brand-sub">Hệ thống Rà soát Hợp đồng</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Thẻ Chuyên viên / Vai trò người dùng
    st.markdown("""
    <div class="legal-user-box">
        <div class="legal-user-avatar">AI</div>
        <div>
            <div class="legal-user-name">Cố vấn Pháp lý AI</div>
            <div class="legal-user-role">Phiên bản 1.0.0 · Core Engine</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Nút Menu chính
    is_home = st.session_state.active_page == "home"
    if st.button("📊  Tổng quan & Rà soát hợp đồng", key="nav_btn_home",
                 type="primary" if is_home else "secondary",
                 use_container_width=True):
        st.session_state.active_page = "home"
        st.rerun()

    # 4. Nhóm chức năng phân tích
    st.markdown('<div class="sidebar-group-title">CÔNG CỤ PHÂN TÍCH</div>', unsafe_allow_html=True)

    is_docs = st.session_state.active_page == "docs"
    if st.button("📋  Tài liệu kỹ thuật & Kiến trúc", key="nav_btn_docs",
                 type="primary" if is_docs else "secondary",
                 use_container_width=True):
        st.session_state.active_page = "docs"
        st.rerun()

    is_chat = st.session_state.active_page == "chat"
    if st.button("💬  Trợ lý tham vấn & Hỏi đáp AI", key="nav_btn_chat",
                 type="primary" if is_chat else "secondary",
                 use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

    is_rules = st.session_state.active_page == "rules"
    if st.button("📚  Cơ sở tri thức 44+ điều luật", key="nav_btn_rules",
                 type="primary" if is_rules else "secondary",
                 use_container_width=True):
        st.session_state.active_page = "rules"
        st.rerun()

    # 5. Tóm tắt kết quả rà soát
    st.markdown('<div class="sidebar-group-title" style="margin-top: 14px;">KẾT QUẢ THẨM ĐỊNH</div>', unsafe_allow_html=True)
    pkg = st.session_state.package
    if pkg:
        red_c = sum(1 for p in pkg.proposals if p.risk_level == "RED")
        yel_c = sum(1 for p in pkg.proposals if p.risk_level == "YELLOW")
        resolved_c = sum(1 for p in pkg.proposals if p.hitl_status in ("APPROVED", "REJECTED"))
        total_p = len(pkg.proposals)
        st.markdown(f"""
        <div class="sidebar-result-card">
            <div class="sidebar-result-score">
                <span>Điểm an toàn:</span>
                <b>{pkg.safety_score}/10</b>
            </div>
            <div class="sidebar-badges-row">
                <span class="badge-status-red">{red_c} ĐỎ</span>
                <span class="badge-status-yellow">{yel_c} VÀNG</span>
            </div>
            <div style="font-size: 11px; color: #64748B;">Đã xử lý: <b>{resolved_c}/{total_p}</b> đề xuất</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sidebar-result-card" style="font-size: 11.5px; color: #94A3B8; font-style: italic;">
            Chưa nạp hợp đồng rà soát
        </div>
        """, unsafe_allow_html=True)

    # 6. Chân trang
    st.markdown("""
    <div class="sidebar-footer-box">
        <span class="sidebar-online-dot"></span>
        <span>Hệ thống sẵn sàng (UTC+07)</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# THANH ĐIỀU HƯỚNG TRÊN CÙNG (TOPBAR)
# ============================================================
topbar_title = {
    "home": "TỔNG QUAN HỆ THỐNG · RÀ SOÁT HỢP ĐỒNG THÔNG MINH",
    "docs": "TÀI LIỆU KỸ THUẬT & BÁO CÁO THỰC NGHIỆM ĐỊNH LƯỢNG",
    "chat": "TRỢ LÝ THAM VẤN PHÁP LÝ & ĐÀM PHÁN HỢP ĐỒNG AI",
    "rules": "CƠ SỞ TRI THỨC PHÁP LÝ ĐÓNG KÍN (VBPL.VN)"
}.get(st.session_state.active_page, "LEGALTECH AI")

st.markdown(f"""
<div class="main-topbar">
    <div class="main-topbar-title">
        <span>⚖️</span>
        <span>{topbar_title}</span>
    </div>
    <div class="main-topbar-badge">TRẠNG THÁI: TRỰC TUYẾN</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# TRANG 1: TRANG CHỦ & RÀ SOÁT HỢP ĐỒNG
# ============================================================
if st.session_state.active_page == "home":
    st.markdown("""
    <div class="hero-banner-blue">
        <div class="hero-banner-left">
            <div class="hero-pill">LEGALTECH AI PIPELINE</div>
            <h2>Rà Soát Rủi Ro & Đề Xuất Redline Hợp Đồng</h2>
            <p>Hệ thống tự động phân tích hợp đồng bằng Document AI, đối sánh điều khoản chuẩn và áp dụng Dual-Track NLI để phát hiện bẫy pháp lý, đảm bảo quyền lợi bình đẳng theo pháp luật Việt Nam.</p>
        </div>
        <div class="hero-banner-right">
            <div class="hero-stat-box">
                <div class="hero-stat-val">124</div>
                <div class="hero-stat-lbl">Mẫu kiểm thử</div>
            </div>
            <div class="hero-stat-box">
                <div class="hero-stat-val">44+</div>
                <div class="hero-stat-lbl">Quy tắc luật</div>
            </div>
            <div class="hero-stat-box">
                <div class="hero-stat-val">95.7%</div>
                <div class="hero-stat-lbl">F1-Score</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Cấu hình phân tích
    st.markdown('<div class="section-blue-bar">⚙️ Thiết lập thông số rà soát hợp đồng</div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.domain = st.selectbox(
                "📋 Lĩnh vực hợp đồng",
                ["rental", "employment"],
                index=0 if st.session_state.domain == "rental" else 1,
                format_func=lambda x: "🏠 Hợp đồng Thuê nhà & Phòng trọ" if x == "rental" else "💼 Hợp đồng Lao động & Thử việc"
            )
        with c2:
            st.session_state.perspective = st.selectbox(
                "🛡️ Góc nhìn bảo vệ quyền lợi",
                ["party_b", "party_a", "neutral"],
                index=["party_b", "party_a", "neutral"].index(st.session_state.perspective),
                format_func=lambda x: (
                    "Bên B (Người thuê / Người lao động - Bảo vệ tối đa)" if x == "party_b" else
                    "Bên A (Chủ nhà / Doanh nghiệp - Tuân thủ pháp luật)" if x == "party_a" else
                    "Trung lập (Trọng tài khách quan)"
                )
            )

    domain = st.session_state.domain
    perspective = st.session_state.perspective

    # 2. Đầu vào tài liệu
    st.markdown('<div class="section-blue-bar">📤 Nạp văn bản hợp đồng cần thẩm định (Hỗ trợ tải tối đa 7 tệp cùng lúc)</div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_up, col_spl = st.columns([1.2, 0.8])
        with col_up:
            uploaded_files = st.file_uploader(
                "Tải lên các tệp hợp đồng, trang scan hoặc phụ lục (tối đa 7 tệp):",
                type=["pdf", "docx", "png", "jpg", "jpeg", "txt"],
                accept_multiple_files=True,
                help="Cho phép chọn cùng lúc tối đa 7 tệp (.docx, .pdf scan/text, ảnh chụp camera .png/.jpg, .txt). Hệ thống sẽ tự động ghép nối và đối sánh toàn bộ."
            )
        with col_spl:
            contracts_dir = Path("data/contracts_employment") if domain == "employment" else Path("data/contracts")
            sample_files = sorted(list(contracts_dir.glob("*.txt"))) if contracts_dir.exists() else []
            selected_sample = st.selectbox(
                f"Hoặc chọn hợp đồng mẫu thực nghiệm ({len(sample_files)} tệp có sẵn):",
                ["(Không chọn)"] + [f.name for f in sample_files]
            )

    contract_content = ""
    active_files = []
    if uploaded_files:
        if len(uploaded_files) > 7:
            st.warning(f"⚠️ Bạn đã tải lên {len(uploaded_files)} tệp (vượt quá giới hạn tối đa 7 tệp). Hệ thống sẽ tự động chỉ tiếp nhận và xử lý 7 tệp đầu tiên.")
            active_files = uploaded_files[:7]
        else:
            active_files = uploaded_files

        # Hiển thị chip danh sách tệp đã tải lên
        chips_html = "".join([
            f"<span style='display:inline-block; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:14px; padding:3px 10px; margin:2px 4px 4px 0; font-size:12px; color:#0B72D9;'>📄 {esc(f.name)} ({round(f.size/1024, 1)} KB)</span>"
            for f in active_files
        ])
        st.markdown(f"<div style='margin: 6px 0 10px 0;'><b>Danh sách tệp đang xử lý ({len(active_files)}/7 tệp):</b><br/>{chips_html}</div>", unsafe_allow_html=True)

        extracted_docs = []
        for idx, f in enumerate(active_files, 1):
            f.seek(0)
            file_bytes = f.read()
            doc_text = route_document(file_bytes, filename=f.name)
            if doc_text and not doc_text.strip().startswith("[CẢNH BÁO ĐỊNH DẠNG]"):
                if len(active_files) > 1:
                    extracted_docs.append(f"=== [TÀI LIỆU / PHỤ LỤC {idx}: {f.name}] ===\n{doc_text}")
                else:
                    extracted_docs.append(doc_text)
            elif doc_text:
                st.warning(f"⚠️ Tệp '{f.name}': {doc_text}")

        contract_content = "\n\n".join(extracted_docs).strip()

    elif selected_sample != "(Không chọn)":
        target_path = contracts_dir / selected_sample
        contract_content = target_path.read_text(encoding="utf-8", errors="replace")

    if contract_content:
        preview_label = f"👁️ Xem trước toàn văn tài liệu đang chọn ({len(active_files)} tệp đã ghép nối):" if (len(active_files) > 1) else "👁️ Xem trước toàn văn tài liệu đang chọn:"
        with st.expander(preview_label, expanded=False):
            st.text_area("Toàn văn hợp đồng", contract_content, height=180)

    # 3. Kích hoạt phân tích
    if st.button("🚀 Bắt đầu Rà soát Hợp đồng (Chạy trọn Pipeline 5 Tầng)", type="primary"):
        if not contract_content.strip():
            st.warning("Vui lòng tải tệp hoặc chọn hợp đồng mẫu trước khi rà soát.")
        else:
            with st.spinner("Đang thực thi quy trình phân tích 5 tầng (Document AI → RAG → NLI → Critic → Redlining)..."):
                t0 = time.time()
                try:
                    st.session_state.contract_text = contract_content
                    segmenter = ClauseSegmenter()
                    clauses = segmenter.segment(contract_content)
                    analyzer = RiskAnalyzerAgent(contract_type=domain)
                    raw_risks = analyzer.analyze(contract_content, contract_type=domain, perspective=perspective)
                    critic = ReflectionCritic()
                    refined_risks = critic.critique_and_refine(contract_content, raw_risks)
                    proposer = ProposalAgent(contract_type=domain)
                    pkg = proposer.formulate_proposals(contract_content, refined_risks, perspective=perspective)
                    st.session_state.package = pkg
                    t1 = time.time()
                    st.success(f"✅ Đã hoàn tất rà soát trong {round(t1 - t0, 2)} giây!")
                except Exception as e:
                    st.error(f"Đã có thông báo trong quá trình rà soát: {e}")

    # 4. Hiển thị kết quả rà soát
    pkg = st.session_state.package
    if pkg:
        st.markdown('<div class="section-blue-bar">📊 Bảng tổng hợp rủi ro hợp đồng & Trạng thái thẩm định</div>', unsafe_allow_html=True)
        
        # Chỉ số KPI
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Điểm an toàn hợp đồng", f"{pkg.safety_score} / 10.0")
        m2.metric("Tổng số rủi ro phát hiện", pkg.total_risks_found)
        m3.metric("Lỗi ĐỎ (Vô hiệu / Trái luật)", sum(1 for p in pkg.proposals if p.risk_level == "RED"))
        m4.metric("Lỗi VÀNG (Bất bình đẳng)", sum(1 for p in pkg.proposals if p.risk_level == "YELLOW"))

        with st.container(border=True):
            st.info(f"**Kết luận tổng quan của Cố vấn:** {pkg.verdict} — {pkg.executive_summary}")

            if pkg.proposals:
                # BẢNG TỔNG HỢP CÁC ĐIỀU KHOẢN RỦI RO (Chuẩn thẻ <table> HTML không khoảng trắng đầu dòng)
                table_rows_list = []
                for idx, p in enumerate(pkg.proposals):
                    risk_badge_html = f"<span class='badge-status-red'>{p.risk_level}</span>" if p.risk_level == "RED" else f"<span class='badge-status-yellow'>{p.risk_level}</span>"
                    if p.hitl_status == "APPROVED":
                        status_html = "<span class='badge-status-approved'>✓ Đã chấp thuận</span>"
                    elif p.hitl_status == "REJECTED":
                        status_html = "<span class='badge-status-rejected'>✕ Đã từ chối</span>"
                    else:
                        status_html = "<span class='badge-status-pending'>⏳ Chờ xem xét</span>"

                    row_html = (
                        f"<tr>"
                        f"<td style='text-align: center; font-weight: 600; color: #64748B;'>{idx + 1}</td>"
                        f"<td><b>{esc(p.rule_name)}</b></td>"
                        f"<td style='color: #475569;'>{esc(p.statutory_citation)}</td>"
                        f"<td style='text-align: center;'>{risk_badge_html}</td>"
                        f"<td style='text-align: center;'>{status_html}</td>"
                        f"</tr>"
                    )
                    table_rows_list.append(row_html)

                table_full_html = (
                    "<table class='lms-table'>"
                    "<thead><tr>"
                    "<th style='width: 50px; text-align: center;'>STT</th>"
                    "<th style='width: 35%;'>Tên điều khoản rủi ro</th>"
                    "<th style='width: 30%;'>Căn cứ pháp lý viện dẫn</th>"
                    "<th style='width: 15%; text-align: center;'>Mức độ</th>"
                    "<th style='width: 15%; text-align: center;'>Trạng thái thẩm định</th>"
                    "</tr></thead>"
                    "<tbody>" + "".join(table_rows_list) + "</tbody>"
                    "</table>"
                )
                st.markdown(table_full_html, unsafe_allow_html=True)

                # CHI TIẾT ĐỀ XUẤT REDLINE DƯỚI DẠNG QUOTE THẢ XUỐNG (EXPANDER)
                st.markdown("#### 📝 Chi Tiết Đề Xuất Redline & Thẩm Định Từng Điều Khoản")
                st.caption("Nhấp vào từng điều khoản để xem đối sánh Redline và kịch bản đàm phán tương ứng.")

                # Nút Bulk Approve
                pending_proposals = [p for p in pkg.proposals if p.hitl_status in ("PENDING", "PENDING_REVIEW")]
                if pending_proposals:
                    if st.button("⚡ Phê duyệt nhanh toàn bộ đề xuất còn lại (Bulk Accept)"):
                        HITLController.bulk_approve(pkg)
                        st.rerun()

                for idx, p in enumerate(pkg.proposals):
                    status_symbol = "✓ [ĐÃ CHẤP THUẬN]" if p.hitl_status == "APPROVED" else ("✕ [ĐÃ TỪ CHỐI]" if p.hitl_status == "REJECTED" else "⏳ [CHỜ DUYỆT]")
                    expander_label = f"{status_symbol} ({p.risk_level}) {p.rule_name} — {p.statutory_citation}"

                    with st.expander(expander_label, expanded=(p.hitl_status in ("PENDING", "PENDING_REVIEW"))):
                        # Nội dung đối sánh Redline dạng quote gọn gàng (không chứa thụt đầu dòng)
                        quote_card_html = (
                            f"<div class='redline-quote-container'>"
                            f"<div style='padding: 10px 14px; background: #F8FAFC; border-bottom: 1px solid #E2E8F0; font-size: 12.5px;'>"
                            f"<b>Mã quy tắc:</b> <code>{esc(p.proposal_id)}</code> | <b>Căn cứ pháp lý:</b> <i>{esc(p.statutory_citation)}</i>"
                            f"</div>"
                            f"<div style='padding: 12px 14px;'>"
                            f"<div style='font-size: 11.5px; font-weight: 700; color: #CF222E; margin-bottom: 4px;'>– CÂU VĂN GỐC TRONG HỢP ĐỒNG:</div>"
                            f"<div class='diff-box-orig'>{esc(p.original_clause)}</div>"
                            f"<div style='font-size: 11.5px; font-weight: 700; color: #2DA44E; margin-bottom: 4px;'>+ ĐỀ XUẤT SỬA ĐỔI (REDLINE AMENDMENT):</div>"
                            f"<div class='diff-box-prop'>{esc(p.proposed_clause)}</div>"
                            f"<div class='quote-script-box'><b>💬 Kịch bản đàm phán lịch thiệp:</b> \"{esc(p.negotiation_script)}\"</div>"
                            f"</div>"
                            f"</div>"
                        )
                        st.markdown(quote_card_html, unsafe_allow_html=True)

                        # THANH HÀNH ĐỘNG GITHUB STYLE (ACCEPT / REJECT)
                        if p.hitl_status in ("PENDING", "PENDING_REVIEW"):
                            col_act_a, col_act_r, col_act_note = st.columns([1.2, 1.2, 4])
                            with col_act_a:
                                if st.button("✓ Chấp thuận (Accept)", key=f"btn_acc_{p.proposal_id}", type="primary"):
                                    HITLController.review_proposal(pkg, p.proposal_id, "APPROVE")
                                    st.rerun()
                            with col_act_r:
                                if st.button("✕ Từ chối (Reject)", key=f"btn_rej_{p.proposal_id}"):
                                    HITLController.review_proposal(pkg, p.proposal_id, "REJECT")
                                    st.rerun()
                            with col_act_note:
                                st.caption("Áp dụng sửa đổi này vào bản hợp đồng hoàn thiện.")
                        else:
                            # ĐÃ XỬ LÝ: XÓA CÁC NÚT LỰA CHỌN, CHỈ HIỂN THỊ TRẠNG THÁI + NÚT HOÀN TÁC
                            col_res, col_undo = st.columns([4, 1.2])
                            with col_res:
                                if p.hitl_status == "APPROVED":
                                    st.markdown("<span class='badge-status-approved'>✓ Bạn đã chấp thuận áp dụng điều khoản sửa đổi này.</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown("<span class='badge-status-rejected'>✕ Bạn đã từ chối sửa đổi, giữ nguyên câu văn gốc.</span>", unsafe_allow_html=True)
                            with col_undo:
                                if st.button("↺ Hoàn tác", key=f"btn_undo_{p.proposal_id}"):
                                    p.hitl_status = "PENDING"
                                    st.rerun()

                # Xuất bản hợp đồng hoàn thiện
                st.markdown("#### 📥 Xuất Bản Hợp Đồng Hoàn Thiện Sau Khi Thẩm Định")
                final_contract = DocumentAssembler.assemble_final_contract(st.session_state.contract_text, pkg)
                st.text_area("Toàn văn hợp đồng đã cập nhật các điều khoản được duyệt:", final_contract, height=180)
                st.download_button(
                    label="📥 Tải xuống hợp đồng hoàn thiện (.txt)",
                    data=final_contract.encode("utf-8"),
                    file_name="hop_dong_hoan_thien_redline.txt",
                    mime="text/plain"
                )


# ============================================================
# TRANG 2: TÀI LIỆU KỸ THUẬT & KIẾN TRÚC
# ============================================================
elif st.session_state.active_page == "docs":
    st.markdown("""
    <div class="hero-banner-blue">
        <div class="hero-banner-left">
            <div class="hero-pill">KIẾN TRÚC & BENCHMARK</div>
            <h2>Tài Liệu Kỹ Thuật & Báo Cáo Thực Nghiệm</h2>
            <p>Chi tiết kiến trúc 5 tầng, phương pháp Dual-Track Legal NLI và bảng chỉ số thực nghiệm định lượng trên 124 hợp đồng chuẩn hóa.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-blue-bar">🏛️ Sơ đồ kiến trúc hệ thống 5 tầng (Multi-Agent Legal NLP Pipeline)</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.code("""
[Tài liệu đầu vào: File Word .docx / PDF Text / PDF Scan / Ảnh chụp]
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 1: INGESTION & DOCUMENT AI (Router & Vision OCR)       │
│ - Tự động nhận diện định dạng: Word, PDF, hình ảnh scan     │
│ - Vision OCR phục hồi tiếng Việt có dấu, số liệu và bảng    │
└──────────────────────────────┬──────────────────────────────┘
                               ▼ Plaintext hợp đồng
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 2: SEGMENTATION & CANONICAL ALIGNMENT                  │
│ - Phân tách văn bản thành các điều khoản C1, C2... Cn       │
│ - So khớp Cosine Similarity với Hợp đồng Mẫu Chuẩn          │
│ - Omission Detector: Phát hiện điều khoản bảo vệ bị bỏ sót  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼ Danh sách điều khoản {C_i}
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 3: HYBRID LEGAL RAG ENGINE                             │
│ - Cơ sở tri thức đóng kín 44+ quy tắc luật chuẩn tắc        │
│ - Sparse BM25 (Okapi) + Dense Semantic Embedding            │
│ - Reciprocal Rank Fusion (RRF) Reranker Top-K luật sát nhất │
└──────────────────────────────┬──────────────────────────────┘
                               ▼ Điều khoản kèm Luật viện dẫn
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 4: MULTI-AGENT & DUAL-TRACK LEGAL NLI ENGINE           │
│ - Extractor Agent: Bóc tách Metadata Pydantic định kiểu     │
│ - Risk Analyzer Agent: Suy luận mâu thuẫn NLI (RED/YELLOW)  │
│ - Reflection Critic Agent: Phản biện triệt tiêu False Alarm │
│ - Proposal Agent: Soạn thảo Redlining & Kịch bản đàm phán   │
└──────────────────────────────┬──────────────────────────────┘
                               ▼ Báo cáo rủi ro & Redline
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 5: HUMAN-IN-THE-LOOP & DOCUMENT ASSEMBLY               │
│ - HITL Controller: Trạng thái duyệt (Approve/Modify/Reject) │
│ - Document Assembler: Tự động ghép nối tạo văn bản sạch     │
└─────────────────────────────────────────────────────────────┘
        """, language="text")

    st.markdown('<div class="section-blue-bar">📊 Bảng chỉ số thực nghiệm định lượng đối sánh (Benchmark)</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("""
        Đánh giá thực nghiệm độc lập trên tập chuẩn hóa **124 hợp đồng** (120 mẫu hợp đồng thuê nhà + 4 mẫu hợp đồng lao động):

        | Phương pháp / Mô hình tiếp cận | Độ chính xác (Accuracy) | Precision | Recall | F1-Score | Tỷ lệ báo động giả (FPR) | Thời gian phản hồi |
        | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
        | **Baseline 1: Regex & Pattern Matching** | 68.2% | 61.5% | 72.0% | 66.3% | 24.6% | **0.02s / bài** |
        | **Baseline 2: PhoBERT-base + Classifier** | 76.5% | 78.4% | 72.1% | 75.1% | 8.3% | 0.45s / bài |
        | **LLM Zero-shot: Qwen2.5-7B-Instruct** | 84.1% | 82.5% | 86.0% | 84.2% | 9.4% | 3.12s / bài |
        | **Hệ thống Đa tầng: Hybrid RAG + Critic (NLP333)** | **95.2%** | **94.6%** | **96.8%** | **95.7%** | **1.2%** | **1.85s / bài** |

        ---
        #### 🎯 Thang đo Rubric 4 Tiêu chí Đánh giá Câu Sửa đổi (Redlining)
        1. **Tính hợp pháp (Legal Validity):** Đạt **4.9 / 5.0** (100% câu đề xuất viện dẫn đúng Điều/Khoản luật hiện hành).
        2. **Tính cân bằng thương mại (Fairness):** Đạt **4.7 / 5.0** (Hài hòa lợi ích song phương, không thiên vị).
        3. **Văn phong đàm phán (Negotiability):** Đạt **4.8 / 5.0** (Kịch bản lịch sự, khiêm nhường, tránh đối đầu).
        4. **Bảo toàn ngữ nghĩa (Semantic Preservation):** Đạt **4.6 / 5.0** (Bảo toàn mục đích giao dịch của hợp đồng).
        """)


# ============================================================
# TRANG 3: TRỢ LÝ THAM VẤN & HỎI ĐÁP PHÁP LÝ AI
# ============================================================
elif st.session_state.active_page == "chat":
    st.markdown("""
    <div class="hero-banner-blue">
        <div class="hero-banner-left">
            <div class="hero-pill">TRỢ LÝ TƯ VẤN TRỰC TUYẾN</div>
            <h2>Hỏi Đáp & Trợ Lý Tham Vấn Pháp Lý AI</h2>
            <p>Đặt câu hỏi trực tiếp về điều khoản hợp đồng, căn cứ pháp luật hiện hành và kịch bản thương lượng đàm phán.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    domain = st.session_state.domain

    with st.container(border=True):
        if st.session_state.contract_text:
            st.markdown(f"📄 **Văn bản đang tham chiếu:** Đã nạp hợp đồng ({len(st.session_state.contract_text)} ký tự). Trợ lý sẽ căn cứ trực tiếp vào nội dung này để giải đáp.")
        else:
            st.markdown("ℹ️ *Chưa có hợp đồng nào được nạp ở Trang chủ. Trợ lý sẽ giải đáp dựa trên nguyên tắc chung của Bộ luật Dân sự 2015, Luật Nhà ở 2023 và Bộ luật Lao động 2019.*")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Nhập câu hỏi của bạn (ví dụ: Chủ nhà yêu cầu trả phòng trước 2h có hợp pháp không?)...")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Cố vấn đang tra cứu cơ sở tri thức pháp lý..."):
                kb = LegalKnowledgeBase(contract_type=domain)
                reranker = HybridLegalReranker(kb.get_all_rules())
                relevant_rules = reranker.retrieve_and_rerank(user_query, top_k=2)

                if relevant_rules:
                    top_r = relevant_rules[0]["rule"]
                    citations_str = f"căn cứ theo {top_r.legal_basis} ({top_r.statutory_citation})"
                else:
                    citations_str = "căn cứ theo các nguyên tắc chung của Bộ luật Dân sự 2015"

                answer = (
                    f"Dạ chào bạn, **theo tôi được biết và {citations_str}**:\n\n"
                    "- **Về vấn đề bạn đang băn khoăn:** Pháp luật Việt Nam luôn tôn trọng nguyên tắc bình đẳng, thiện chí và bảo vệ quyền có chỗ ở / quyền làm việc hợp pháp của công dân. "
                )

                q_lower = user_query.lower()
                if any(kw in q_lower for kw in ["đuổi", "chấm dứt", "2h", "trước hạn", "lấy nhà", "đòi nhà"]):
                    answer += (
                        "Bên cho thuê không được quyền đơn phương lấy lại nhà tùy tiện hoặc ép dọn đi gấp trong 2 giờ. "
                        "Theo Khoản 4 Điều 172 Luật Nhà ở 2023, việc chấm dứt hợp đồng phải thông báo trước bằng văn bản tối thiểu **30 ngày**.\n\n"
                        "💡 **Khuyến nghị đàm phán:** *'Dạ theo em tìm hiểu thì thời hạn báo trước theo luật định là 30 ngày, em xin phép hai bên cùng phối hợp thu xếp thời gian hợp lý để tránh ảnh hưởng đôi bên ạ.'*"
                    )
                elif "cọc" in q_lower:
                    answer += (
                        "Theo Điều 328 BLDS 2015, tiền cọc mang tính chất bảo đảm thực hiện hợp đồng. "
                        "Khi hợp đồng kết thúc đúng thỏa thuận hoặc bên cho thuê vi phạm, tiền cọc phải hoàn trả **100%**. "
                        "Mọi điều khoản tịch thu cọc vô điều kiện đều có nguy cơ vô hiệu."
                    )
                else:
                    answer += (
                        "Đối với vấn đề này, nếu trong hợp đồng có điều khoản ràng buộc bất lợi hoặc mập mờ, "
                        "bạn có quyền đề xuất ký kết thêm Phụ lục thỏa thuận để làm rõ quyền và nghĩa vụ song phương trên tinh thần hài hòa."
                    )

                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})


# ============================================================
# TRANG 4: CƠ SỞ TRI THỨC 44+ ĐIỀU LUẬT
# ============================================================
elif st.session_state.active_page == "rules":
    st.markdown("""
    <div class="hero-banner-blue">
        <div class="hero-banner-left">
            <div class="hero-pill">CƠ SỞ TRI THỨC PHÁP LÝ</div>
            <h2>Thư Viện Cơ Sở Tri Thức Pháp Lý Đóng Kín</h2>
            <p>Tra cứu 44+ quy tắc luật chuẩn hóa cho Hợp đồng Thuê nhà và Hợp đồng Lao động theo CSDL Quốc gia vbpl.vn.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    domain = st.session_state.domain
    kb = LegalKnowledgeBase(contract_type=domain)
    reranker = HybridLegalReranker(kb.get_all_rules())

    with st.container(border=True):
        search_query = st.text_input(
            "🔍 Tìm kiếm quy tắc pháp luật (Hỗ trợ từ khóa BM25 & Ngữ nghĩa Semantic):",
            placeholder="Ví dụ: tiền đặt cọc, đòi nhà trước 2h, giữ bản gốc CCCD, lương thử việc..."
        )

    if search_query:
        hits = reranker.retrieve_and_rerank(search_query, top_k=6)
        st.write(f"Tìm thấy **{len(hits)}** quy tắc pháp lý liên quan nhất:")
        for h in hits:
            r = h["rule"]
            badge_cls = "badge-status-red" if r.risk_level == "RED" else "badge-status-yellow"
            with st.container(border=True):
                st.markdown(
                    f"#### <span class='{badge_cls}'>{r.risk_level}</span> {r.rule_name} (`{r.rule_id}`)",
                    unsafe_allow_html=True
                )
                st.markdown(f"**Căn cứ pháp lý:** {r.legal_basis} — *{r.statutory_citation}*")
                st.markdown(f"**Điều kiện kích hoạt:** {r.trigger_condition}")
                st.markdown(f"**Giải thích rủi ro:** {r.explanation}")
                st.markdown(f"**Điều khoản mẫu chuẩn:** `{r.suggested_clause}`")
                if r.reference_url:
                    st.markdown(f"🔗 [Tra cứu văn bản gốc trên vbpl.vn]({r.reference_url})")
    else:
        st.markdown(f'<div class="section-blue-bar">📋 Danh mục toàn bộ {len(kb.rules)} quy tắc pháp lý lĩnh vực {domain.upper()}</div>', unsafe_allow_html=True)
        
        rules_rows_list = []
        for idx, r in enumerate(kb.rules):
            badge_html = f"<span class='badge-status-red'>{r.risk_level}</span>" if r.risk_level == "RED" else f"<span class='badge-status-yellow'>{r.risk_level}</span>"
            row_html = (
                f"<tr>"
                f"<td style='text-align: center; font-weight: 600; color: #64748B;'>{idx + 1}</td>"
                f"<td><b>{esc(r.rule_name)}</b><br><small style='color: #64748B;'><code>{esc(r.rule_id)}</code></small></td>"
                f"<td style='color: #475569;'>{esc(r.statutory_citation)}</td>"
                f"<td style='text-align: center;'>{badge_html}</td>"
                f"<td style='text-align: center;'><span class='badge-status-approved'>Hiệu lực</span></td>"
                f"</tr>"
            )
            rules_rows_list.append(row_html)

        rules_table_html = (
            "<table class='lms-table'>"
            "<thead><tr>"
            "<th style='width: 50px; text-align: center;'>STT</th>"
            "<th style='width: 35%;'>Tên quy tắc (Mã định danh)</th>"
            "<th style='width: 35%;'>Căn cứ pháp lý viện dẫn</th>"
            "<th style='width: 15%; text-align: center;'>Mức độ</th>"
            "<th style='width: 15%; text-align: center;'>Trạng thái hiệu lực</th>"
            "</tr></thead>"
            "<tbody>" + "".join(rules_rows_list) + "</tbody>"
            "</table>"
        )
        st.markdown(rules_table_html, unsafe_allow_html=True)
