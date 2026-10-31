import os
import json
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.agents import (
    ExtractorAgent,
    RiskAnalyzerAgent,
    ProposalAgent,
    HITLController,
    ContractMetadata,
    RiskAnalysisResult,
    ContractReviewPackage,
    RedlineProposal
)
from src.parsers import parse_contract_file

# ============================================================
# CẤU HÌNH GIAO DIỆN STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Hệ thống hỗ trợ rà soát và đề xuất hợp đồng thuê nhà",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .badge-red {
        background-color: #FEE2E2;
        color: #DC2626;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #FCA5A5;
    }
    .badge-yellow {
        background-color: #FEF3C7;
        color: #D97706;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #FCD34D;
    }
    .badge-green {
        background-color: #DCFCE7;
        color: #16A34A;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #86EFAC;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 14px;
        border: 1px solid #E2E8F0;
        margin-bottom: 0.8rem;
    }
    .diff-orig {
        background-color: #FFF1F2;
        border-left: 4px solid #F43F5E;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 0.92rem;
        color: #9F1239;
        margin-bottom: 8px;
    }
    .diff-proposed {
        background-color: #F0FDF4;
        border-left: 4px solid #22C55E;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 0.92rem;
        color: #166534;
        margin-bottom: 8px;
    }
    .script-box {
        background-color: #F8FAFC;
        border: 1px dashed #94A3B8;
        padding: 10px 14px;
        border-radius: 8px;
        font-style: italic;
        color: #334155;
        margin: 6px 0;
        font-size: 0.9rem;
    }
    .inspector-panel {
        background-color: #F8FAFC;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 16px;
        position: sticky;
        top: 20px;
    }
    .citation-tag {
        font-weight: 700;
        color: #1D4ED8;
        background-color: #EFF6FF;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #BFDBFE;
        display: inline-block;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo Session State
if "contract_text" not in st.session_state:
    st.session_state.contract_text = ""
if "metadata" not in st.session_state:
    st.session_state.metadata = None
if "risk_result" not in st.session_state:
    st.session_state.risk_result = None
if "review_package" not in st.session_state:
    st.session_state.review_package = None
if "active_file_name" not in st.session_state:
    st.session_state.active_file_name = "Chưa chọn file"
if "inspecting_prop_id" not in st.session_state:
    st.session_state.inspecting_prop_id = None

# Hàm nạp dữ liệu quy tắc luật
@st.cache_data
def load_legal_rules_map():
    rules_path = Path("data/legal_rules.json")
    if not rules_path.exists():
        return {}
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {r["rule_id"]: r for r in data.get("rules", [])}
    except Exception:
        return {}

rules_map = load_legal_rules_map()

# ============================================================
# HÀM XỬ LÝ PHA 1: NẠP VÀ BÓC TÁCH TỰ ĐỘNG (AGENT 1 & AGENT 2)
# ============================================================
def process_phase_one(contract_text: str, filename: str):
    """
    Pha 1: Tiếp nhận văn bản, bóc tách thực thể (Agent 1) và đối chiếu quy định (Agent 2).
    Chưa chạy Agent 3 để người dùng chủ động kiểm soát.
    """
    st.session_state.contract_text = contract_text
    st.session_state.active_file_name = filename
    st.session_state.review_package = None
    st.session_state.inspecting_prop_id = None

    with st.spinner("🤖 Đang bóc tách thông tin (Agent 1) và đối chiếu 28 quy tắc luật (Agent 2)..."):
        # Agent 1
        extractor = ExtractorAgent()
        st.session_state.metadata = extractor.extract(contract_text)
        
        # Agent 2
        analyzer = RiskAnalyzerAgent()
        st.session_state.risk_result = analyzer.analyze(contract_text)

# ============================================================
# SIDEBAR: CHỌN NGUỒN TÀI LIỆU
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/law.png", width=60)
    st.title("Pháp lý Thuê nhà AI")
    st.caption("Document AI • Bóc tách • Đối chiếu quy định")
    st.divider()

    st.subheader("📁 Nguồn Hợp đồng")
    input_method = st.radio(
        "Chọn cách nạp văn bản:",
        ["Hợp đồng mẫu có sẵn (Dataset)", "Tải lên file của bạn (Scan/Docx/PDF/Txt)"],
        index=0
    )

    if input_method == "Hợp đồng mẫu có sẵn (Dataset)":
        contracts_dir = Path("data/contracts")
        available_files = []
        if contracts_dir.exists():
            available_files = sorted([f.name for f in contracts_dir.glob("*.txt")])
        
        recommended_samples = [
            ("HD_015.txt", "HD_015: Tiền điện 3.800đ & Cấm chấm dứt sớm"),
            ("HD_045.txt", "HD_045: Phạt cọc kép & Tự ý tăng giá 15%"),
            ("HD_001.txt", "HD_001: Mẫu chuẩn Bộ Xây dựng (Sạch 100%)"),
            ("HD_030.txt", "HD_030: Tự ý vào phòng & Chậm trả tiền"),
        ]
        
        sample_dict = {label: fname for fname, label in recommended_samples}
        selected_label = st.selectbox(
            "Chọn tình huống mẫu để demo nhanh:",
            list(sample_dict.keys()),
            index=0
        )
        selected_file_name = sample_dict[selected_label]
        file_path = contracts_dir / selected_file_name

        if st.button("📥 Nạp & Bóc tách văn bản này", use_container_width=True, type="primary"):
            if file_path.exists():
                text_content = file_path.read_text(encoding="utf-8")
                process_phase_one(text_content, selected_file_name)
                st.success(f"Đã nạp và bóc tách thành công: {selected_file_name}")
                st.rerun()

    else:
        st.caption("ℹ️ **Định dạng hỗ trợ:** Ảnh scan in ấn (`.png`, `.jpg`), tài liệu Word (`.docx`, `.doc`), file PDF scan/text (`.pdf`) hoặc tệp văn bản (`.txt`).\n*(Hệ thống không nhận văn bản viết tay để bảo đảm độ chính xác cao nhất).*")
        uploaded_file = st.file_uploader(
            "Tải lên tệp tài liệu hợp đồng:",
            type=["docx", "doc", "pdf", "png", "jpg", "jpeg", "txt"]
        )
        if uploaded_file is not None:
            if st.button("🚀 Bóc tách & Rà soát tài liệu", use_container_width=True, type="primary"):
                temp_path = Path("data") / f"temp_upload_{uploaded_file.name}"
                temp_path.write_bytes(uploaded_file.getbuffer())
                try:
                    with st.spinner("Đang xử lý tài liệu (OCR nếu là ảnh scan hoặc PDF)..."):
                        extracted_text = parse_contract_file(temp_path)
                    process_phase_one(extracted_text, uploaded_file.name)
                    st.success(f"Đã trích xuất và bóc tách thành công {len(extracted_text)} ký tự!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi đọc file: {e}")
                finally:
                    if temp_path.exists():
                        temp_path.unlink()

    st.divider()
    st.subheader("⚙️ Trạng thái Hệ thống")
    api_key_set = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY"))
    if api_key_set:
        st.success("🟢 API AI: Đã kết nối OpenRouter")
        st.caption(f"Mô hình: `{os.getenv('OPENROUTER_MODEL', 'google/gemini-2.5-flash')}`")
    else:
        st.warning("🟡 Chạy chế độ Rule-based offline (chưa nạp API Key)")

    st.info("💡 **Bộ luật áp dụng đối chiếu:**\n- Bộ luật Dân sự 2015\n- Luật Nhà ở 2023 (số 27/2023/QH15)\n- Nghị định 134/2013/NĐ-CP\n- Nghị định 96/2024/NĐ-CP")

# ============================================================
# MAIN CONTENT HEADER
# ============================================================
st.markdown('<div class="main-header">⚖️ HỆ THỐNG HỖ TRỢ RÀ SOÁT VÀ ĐỀ XUẤT HỢP ĐỒNG THUÊ NHÀ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Bóc tách thông tin có cấu trúc • Đối chiếu quy định pháp luật Việt Nam • Đề xuất câu văn sửa đổi theo yêu cầu (Human-in-the-Loop)</div>', unsafe_allow_html=True)

# Trạng thái chưa nạp văn bản
if not st.session_state.contract_text:
    st.info("👉 **Bắt đầu:** Vui lòng chọn một bản hợp đồng mẫu hoặc tải lên tệp văn bản/ảnh scan từ thanh menu bên trái để hệ thống tiến hành bóc tách.")
    
    col_intro1, col_intro2, col_intro3 = st.columns(3)
    with col_intro1:
        st.markdown("""
        **1. 📄 Nạp tài liệu đa định dạng**
        - Hỗ trợ tệp Word (`.docx`), PDF (`.pdf`), hoặc ảnh scan in ấn (`.png`, `.jpg`).
        - Tự động nhận diện chữ tiếng Việt bằng Vision AI.
        """)
    with col_intro2:
        st.markdown("""
        **2. 🤖 Bóc tách & Đối chiếu tự động**
        - Trích xuất thông tin Bên A, Bên B, giá thuê, cọc.
        - Tự động đối chiếu với 28 quy tắc luật (Luật Nhà ở 2023 & BLDS 2015).
        """)
    with col_intro3:
        st.markdown("""
        **3. 💡 Đề xuất gợi ý & Tra cứu điều luật**
        - Bấm nút yêu cầu AI soạn thảo câu văn thay thế.
        - Bấm vào trích dẫn điều luật để mở ngăn tra cứu chi tiết bên phải.
        """)
    st.stop()

# ============================================================
# THANH THÔNG TIN TÀI LIỆU HIỆN TẠI
# ============================================================
st.markdown(f"📄 **Tài liệu đang xử lý:** `{st.session_state.active_file_name}` ({len(st.session_state.contract_text):,} ký tự)")

# ============================================================
# KHU VỰC 1: BẢNG THÔNG TIN HỢP ĐỒNG (AGENT 1 METADATA)
# ============================================================
if st.session_state.metadata:
    m = st.session_state.metadata
    st.markdown("### 📋 1. Bảng Thông Tin Hợp Đồng (Bóc tách bởi Agent 1)")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Chủ nhà (Bên A)", m.lessor_name or "Chưa rõ")
        st.metric("Khách thuê (Bên B)", m.lessee_name or "Chưa rõ")
    with col_m2:
        st.metric("Giá thuê hàng tháng", f"{m.rent_price:,.0f} đ" if m.rent_price else "Chưa rõ")
        st.metric("Tiền đặt cọc", f"{m.deposit_amount:,.0f} đ" if m.deposit_amount else "Chưa rõ")
    with col_m3:
        st.metric("Thời hạn thuê", f"{m.lease_term_months} tháng" if m.lease_term_months else "Chưa rõ")
        st.metric("Thời hạn báo trước", f"{m.notice_period_days} ngày" if m.notice_period_days else "Chưa rõ")
    with col_m4:
        st.metric("Đơn giá tiền điện", m.electricity_price or "Theo thực tế")
        st.metric("Đơn giá tiền nước", m.water_price or "Theo thực tế")
    
    if m.property_address:
        st.caption(f"📍 **Địa chỉ tài sản thuê:** {m.property_address}")

    with st.expander("📜 Xem toàn văn nội dung hợp đồng gốc", expanded=False):
        st.text_area("Toàn văn hợp đồng:", st.session_state.contract_text, height=250, disabled=True)

st.divider()

# ============================================================
# KHU VỰC 2: KẾT QUẢ ĐỐI CHIẾU PHÁP LUẬT (AGENT 2)
# ============================================================
if st.session_state.risk_result:
    res = st.session_state.risk_result
    st.markdown("### 🛡️ 2. Kết Quả Đối Chiếu Quy Định Pháp Luật (Agent 2)")
    
    col_r1, col_r2 = st.columns([1, 3])
    with col_r1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if res.is_safe or res.total_risks == 0:
            st.metric("Tình trạng đối chiếu", "Chuẩn mực 100%")
            st.markdown('<span class="badge-green">HỢP ĐỒNG SẠCH AN TOÀN</span>', unsafe_allow_html=True)
        else:
            st.metric("Điểm cần lưu ý", f"{res.total_risks} điều khoản")
            st.markdown(f'<span class="badge-red">Mức Đỏ: {res.red_risks_count}</span> &nbsp; <span class="badge-yellow">Mức Vàng: {res.yellow_risks_count}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**Nhận định tổng quan về hợp đồng:**")
        st.write(res.overall_assessment)
        st.markdown('</div>', unsafe_allow_html=True)

    # Chi tiết các điều khoản cần lưu ý
    if res.risks:
        with st.expander(f"🔎 Xem danh sách {len(res.risks)} điều khoản phát hiện trong hợp đồng", expanded=False):
            for idx, r in enumerate(res.risks, 1):
                badge_cls = "badge-red" if r.risk_level.upper() == "RED" else "badge-yellow"
                badge_txt = "MỨC ĐỎ (Vi phạm điều cấm)" if r.risk_level.upper() == "RED" else "MỨC VÀNG (Bất lợi thương mại)"
                st.markdown(f"**[{idx}] {r.rule_name}** &nbsp; <span class='{badge_cls}'>{badge_txt}</span>", unsafe_allow_html=True)
                st.markdown(f"- **Đoạn văn trong hợp đồng (Nguyên văn):** *\"{r.original_clause}\"*")
                st.markdown(f"- **Căn cứ đối chiếu:** `{r.legal_basis}`")
                st.caption(f"Giải thích: {r.explanation}")
                st.write("---")

st.divider()

# ============================================================
# KHU VỰC 3: NÚT KÍCH HOẠT ĐỀ XUẤT GỢI Ý (AGENT 3 ON-DEMAND)
# ============================================================
st.markdown("### ✍️ 3. Đề Xuất Gợi Ý Sửa Đổi & Tra Cứu Điều Luật")

# Trường hợp hợp đồng sạch hoàn toàn
if st.session_state.risk_result and st.session_state.risk_result.is_safe:
    st.success("🎉 **Hợp đồng chuẩn mực, tuân thủ đúng pháp luật:** Không phát hiện điều khoản nào vi phạm điều cấm hoặc bất lợi nghiêm trọng. Bạn có thể an tâm sử dụng bản hợp đồng này mà không cần đề xuất sửa đổi.")
else:
    # Nếu Agent 3 CHƯA CHẠY -> Hiển thị nút bấm để người dùng kích hoạt
    if st.session_state.review_package is None:
        st.info("💡 Hệ thống đã hoàn tất bóc tách và đối chiếu. Nhấn nút bên dưới nếu bạn muốn **kích hoạt Agent 3** để soạn thảo các câu văn thay thế cân bằng quyền lợi và kịch bản đàm phán gửi chủ nhà:")
        
        btn_col1, btn_col2 = st.columns([2, 3])
        with btn_col1:
            if st.button("⚡ ĐỀ XUẤT GỢI Ý SỬA ĐỔI (KÍCH HOẠT AGENT 3)", type="primary", use_container_width=True):
                with st.spinner("✍️ [Agent 3] Đang phân tích rủi ro, soạn thảo câu văn thay thế và kịch bản đàm phán..."):
                    proposal_agent = ProposalAgent()
                    st.session_state.review_package = proposal_agent.generate_review_package(
                        contract_text=st.session_state.contract_text,
                        risk_analysis=st.session_state.risk_result,
                        metadata=st.session_state.metadata
                    )
                st.success("Đã hoàn thành soạn thảo đề xuất gợi ý!")
                st.rerun()

    # NẾU AGENT 3 ĐÃ HOÀN THÀNH -> HIỂN THỊ DANH SÁCH GỢI Ý & NGĂN TRA CỨU BÊN PHẢI (SIDE PANEL)
    else:
        pkg = st.session_state.review_package
        post_score = HITLController.calculate_post_hitl_safety_score(pkg)

        # Thanh trạng thái duyệt HITL
        st.markdown(f"**Trạng thái phiên làm việc:** Đang hiển thị **{len(pkg.proposals)}** đề xuất gợi ý sửa đổi | Điểm tương thích sau khi duyệt: **{post_score}/10.0**")
        
        # Nút duyệt nhanh
        if st.button("✓ Duyệt nhanh tất cả gợi ý AI (Bulk Approve)"):
            HITLController.bulk_approve(pkg)
            st.success("Đã đồng ý áp dụng tất cả các câu văn do AI đề xuất!")
            st.rerun()

        # ========================================================
        # BỐ CỤC 2 CỘT: CỘT TRÁI (LIST GỢI Ý) & CỘT PHẢI (SIDE PANEL TRA CỨU)
        # ========================================================
        col_list, col_drawer = st.columns([7, 5])

        # --------------------------------------------------------
        # CỘT TRÁI (7 PHẦN): DANH SÁCH CÁC GỢI Ý SỬA ĐỔI
        # --------------------------------------------------------
        with col_list:
            st.markdown("#### 📝 Danh sách Điều khoản Gợi ý Sửa đổi")
            
            for i, prop in enumerate(pkg.proposals, 1):
                status_labels = {
                    "APPROVED": "✅ ĐÃ ÁP DỤNG CÂU AI",
                    "MODIFIED": "✏️ ĐÃ TỰ SỬA CÂU CHỮ",
                    "REJECTED": "❌ GIỮ NGUYÊN VĂN GỐC",
                    "PENDING_REVIEW": "⏳ CHỜ DUYỆT"
                }
                status_txt = status_labels.get(prop.hitl_status, prop.hitl_status)

                with st.container():
                    st.markdown(f"**Gợi ý {i}: {prop.rule_name}** (`{status_txt}`)")
                    
                    # Bảng Before vs After
                    st.markdown("**❌ Đoạn văn trong hợp đồng (Nguyên văn):**")
                    st.markdown(f'<div class="diff-orig">"{prop.original_clause}"</div>', unsafe_allow_html=True)
                    
                    st.markdown("**💡 Đề xuất câu văn thay thế (Cân bằng quyền lợi):**")
                    st.markdown(f'<div class="diff-proposed">"{prop.proposed_clause}"</div>', unsafe_allow_html=True)

                    # CITATION IN ĐẬM VÀ NÚT MỞ NGĂN TRA CỨU BÊN PHẢI
                    st.markdown(f"**⚖️ Trích dẫn:** <span class='citation-tag'>Trích {prop.statutory_citation}</span>", unsafe_allow_html=True)
                    
                    c_btn1, c_btn2 = st.columns([2, 1])
                    with c_btn1:
                        # Nút bấm mở ngăn tra cứu bên phải
                        is_current = (st.session_state.inspecting_prop_id == prop.proposal_id)
                        btn_label = f"📖 Đang xem điều luật này ↗" if is_current else f"📖 Mở thông tin điều luật này ở cạnh phải ↗"
                        if st.button(btn_label, key=f"inspect_{prop.proposal_id}"):
                            st.session_state.inspecting_prop_id = prop.proposal_id
                            st.rerun()

                    # Kịch bản đàm phán gửi chủ nhà
                    with st.expander("💬 Kịch bản đàm phán lịch sự gửi chủ nhà", expanded=False):
                        st.markdown(f'<div class="script-box">"{prop.negotiation_script}"</div>', unsafe_allow_html=True)

                    # CÁC NÚT BẤM HUMAN-IN-THE-LOOP
                    st.markdown("**Hành động của bạn:**")
                    h_col1, h_col2, h_col3 = st.columns([1, 1, 1])
                    with h_col1:
                        if st.button("✅ Đồng ý dùng câu AI", key=f"app_{prop.proposal_id}"):
                            HITLController.review_proposal(pkg, prop.proposal_id, "APPROVE")
                            st.rerun()
                    with h_col2:
                        if st.button("❌ Giữ câu gốc", key=f"rej_{prop.proposal_id}"):
                            HITLController.review_proposal(pkg, prop.proposal_id, "REJECT")
                            st.rerun()
                    with h_col3:
                        with st.popover("✏️ Tự sửa câu này"):
                            edit_val = prop.user_custom_clause or prop.proposed_clause
                            new_text = st.text_area("Nhập câu chữ riêng của bạn:", value=edit_val, key=f"custom_{prop.proposal_id}", height=120)
                            if st.button("Lưu câu tự sửa", key=f"save_edit_{prop.proposal_id}"):
                                HITLController.review_proposal(pkg, prop.proposal_id, "MODIFY", custom_clause=new_text)
                                st.rerun()

                    if prop.final_clause:
                        st.caption(f"📌 *Câu văn chốt đưa vào hợp đồng:* \"{prop.final_clause}\"")

                    st.write("---")

        # --------------------------------------------------------
        # CỘT PHẢI (5 PHẦN): NGĂN TRA CỨU ĐIỀU LUẬT (SIDE PANEL INSPECTOR)
        # --------------------------------------------------------
        with col_drawer:
            st.markdown('<div class="inspector-panel">', unsafe_allow_html=True)
            st.markdown("#### 📖 NGĂN TRA CỨU ĐIỀU LUẬT (LEGAL INSPECTOR)")
            st.caption("Thông tin quy định pháp luật tham chiếu theo từng điều khoản")

            # Nếu chưa chọn điều luật nào
            if not st.session_state.inspecting_prop_id:
                st.info("👈 **Hướng dẫn:** Bấm vào nút **'📖 Mở thông tin điều luật này ở cạnh phải ↗'** ở bất kỳ gợi ý nào bên trái để xem đầy đủ căn cứ và điều luật tại đây.")
            else:
                # Tìm proposal và quy tắc tương ứng
                target_prop = None
                for p in pkg.proposals:
                    if p.proposal_id == st.session_state.inspecting_prop_id:
                        target_prop = p
                        break
                
                if target_prop:
                    rule_detail = rules_map.get(target_prop.rule_id, {})
                    
                    st.markdown(f"### {target_prop.rule_name}")
                    st.markdown(f"**Mã quy tắc:** `{target_prop.rule_id}`")
                    
                    st.divider()
                    st.markdown(f"**🏛️ Căn cứ pháp lý chính thức:**")
                    st.markdown(f"<span class='citation-tag' style='font-size:1rem;'>Trích {target_prop.statutory_citation}</span>", unsafe_allow_html=True)

                    if rule_detail:
                        st.markdown(f"**📚 Nhóm quy định:** {rule_detail.get('category', 'Pháp luật Nhà ở')}")
                        st.markdown(f"**⚖️ Chi tiết nội dung pháp luật & Lý giải:**")
                        st.write(rule_detail.get("explanation", target_prop.explanation))
                        
                        if rule_detail.get("trigger_condition"):
                            st.markdown(f"**⚠️ Dấu hiệu vi phạm / không phù hợp:**")
                            st.write(rule_detail.get("trigger_condition"))
                    else:
                        st.write(target_prop.explanation)

                    # Link tra cứu văn bản quy phạm pháp luật vbpl.vn
                    ref_url = target_prop.reference_url or (rule_detail.get("reference_url") if rule_detail else None)
                    if ref_url:
                        st.markdown(f"""
                        <div style="margin: 14px 0;">
                            <a href="{ref_url}" target="_blank" style="text-decoration:none;">
                                <button style="background-color:#2563EB; color:white; border:none; padding:8px 14px; border-radius:8px; font-weight:600; font-size:0.85rem; cursor:pointer;">
                                    🔗 Mở toàn văn trên Cơ sở dữ liệu vbpl.vn ↗
                                </button>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    if st.button("✕ Đóng ngăn tra cứu", use_container_width=True):
                        st.session_state.inspecting_prop_id = None
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # ========================================================
        # KHU VỰC 4: XUẤT BẢN HỢP ĐỒNG HOÀN THIỆN
        # ========================================================
        st.divider()
        st.markdown("### 📝 4. Xuất Bản Hợp Đồng Hoàn Thiện Sẵn Sàng Ký")
        
        final_contract_text = HITLController.assemble_final_contract(st.session_state.contract_text, pkg)
        diff_report_md = HITLController.generate_diff_report(pkg)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("Điểm an toàn hợp đồng sau khi xử lý", f"{post_score}/10.0")
        with col_f2:
            verdict_final = "AN TOÀN - CÓ THỂ KÝ KẾT" if post_score >= 8.0 else "CẦN THẬN TRỌNG THÊM"
            st.metric("Phán quyết sau cùng", verdict_final)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 Tải Văn bản Hợp đồng Hoàn thiện (.txt)",
                data=final_contract_text,
                file_name=f"HopDong_HoanThien_{st.session_state.active_file_name}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                label="📊 Tải Báo cáo Đối chiếu Redline Diff (.md)",
                data=diff_report_md,
                file_name=f"BaoCao_Redline_Diff_{st.session_state.active_file_name}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with st.expander("👁️ Xem trước toàn văn hợp đồng sau chỉnh sửa", expanded=False):
            st.text_area("Nội dung hoàn thiện:", final_contract_text, height=350, disabled=True)
