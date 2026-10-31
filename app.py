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
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
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
        padding: 16px;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    .diff-orig {
        background-color: #FFF1F2;
        border-left: 4px solid #F43F5E;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 0.95rem;
        color: #9F1239;
        margin-bottom: 8px;
    }
    .diff-proposed {
        background-color: #F0FDF4;
        border-left: 4px solid #22C55E;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 0.95rem;
        color: #166534;
        margin-bottom: 8px;
    }
    .script-box {
        background-color: #F8FAFC;
        border: 1px dashed #94A3B8;
        padding: 12px 16px;
        border-radius: 8px;
        font-style: italic;
        color: #334155;
        margin: 8px 0;
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

# ============================================================
# SIDEBAR: CẤU HÌNH & CHỌN HỢP ĐỒNG
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/law.png", width=64)
    st.title("Pháp lý Thuê nhà AI")
    st.caption("Multi-Agent System với Human-in-the-Loop")
    st.divider()

    st.subheader("📁 Nguồn Hợp đồng")
    input_method = st.radio(
        "Chọn cách nạp văn bản:",
        ["Hợp đồng mẫu có sẵn (Dataset)", "Tải lên file của bạn (Docx/PDF/Ảnh/Txt)"],
        index=0
    )

    if input_method == "Hợp đồng mẫu có sẵn (Dataset)":
        contracts_dir = Path("data/contracts")
        available_files = []
        if contracts_dir.exists():
            available_files = sorted([f.name for f in contracts_dir.glob("*.txt")])
        
        # Chọn mẫu đặc trưng
        recommended_samples = [
            ("HD_015.txt", "HD_015: Rủi ro tiền điện 3.800đ & cấm chấm dứt sớm"),
            ("HD_001.txt", "HD_001: Mẫu hợp đồng chuẩn mẫu (Sạch 100%)"),
            ("HD_045.txt", "HD_045: Rủi ro phạt cọc kép & tự ý tăng giá"),
            ("HD_030.txt", "HD_030: Rủi ro tự ý vào phòng & chậm trả tiền"),
        ]
        
        sample_dict = {label: fname for fname, label in recommended_samples}
        selected_label = st.selectbox(
            "Chọn tình huống mẫu:",
            list(sample_dict.keys()),
            index=0
        )
        selected_file_name = sample_dict[selected_label]
        file_path = contracts_dir / selected_file_name

        if st.button("📥 Nạp văn bản hợp đồng này", use_container_width=True):
            if file_path.exists():
                st.session_state.contract_text = file_path.read_text(encoding="utf-8")
                st.session_state.active_file_name = selected_file_name
                # Reset kết quả cũ
                st.session_state.metadata = None
                st.session_state.risk_result = None
                st.session_state.review_package = None
                st.success(f"Đã nạp thành công: {selected_file_name}")

    else:
        uploaded_file = st.file_uploader(
            "Tải lên văn bản hợp đồng:",
            type=["docx", "doc", "pdf", "png", "jpg", "jpeg", "txt"]
        )
        if uploaded_file is not None:
            if st.button("🚀 Xử lý & Bóc tách File", use_container_width=True):
                temp_path = Path("data") / f"temp_upload_{uploaded_file.name}"
                temp_path.write_bytes(uploaded_file.getbuffer())
                try:
                    with st.spinner("Đang xử lý tài liệu (OCR nếu là ảnh/PDF scan)..."):
                        extracted_text = parse_contract_file(temp_path)
                    st.session_state.contract_text = extracted_text
                    st.session_state.active_file_name = uploaded_file.name
                    st.session_state.metadata = None
                    st.session_state.risk_result = None
                    st.session_state.review_package = None
                    st.success(f"Đã trích xuất {len(extracted_text)} ký tự từ {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Lỗi khi đọc file: {e}")
                finally:
                    if temp_path.exists():
                        temp_path.unlink()

    st.divider()
    st.subheader("⚙️ Trạng thái Hệ thống")
    api_key_set = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
    if api_key_set:
        st.success("🟢 API AI: Đã kết nối OpenRouter")
        st.caption(f"Model: {os.getenv('OPENROUTER_MODEL', 'google/gemini-2.5-flash')}")
    else:
        st.warning("🟡 Chưa thấy API Key, chạy chế độ Rule-based offline")

    st.info("💡 **Bộ luật áp dụng:**\n- Bộ luật Dân sự 2015\n- Luật Nhà ở 2023 (số 27/2023/QH15)\n- Nghị định 96/2024/NĐ-CP\n- Nghị định 134/2013/NĐ-CP")

# ============================================================
# MAIN CONTENT HEADER
# ============================================================
st.markdown('<div class="main-header">⚖️ HỆ THỐNG HỖ TRỢ RÀ SOÁT VÀ ĐỀ XUẤT HỢP ĐỒNG THUÊ NHÀ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Phân tích rủi ro pháp lý theo 28 quy tắc chuẩn mực • Trích dẫn Citation vbpl.vn • Hỗ trợ Con người phê duyệt (HITL)</div>', unsafe_allow_html=True)

# THANH HÀNH ĐỘNG CHÍNH
col_act1, col_act2 = st.columns([3, 1])
with col_act1:
    st.write(f"📄 **Tài liệu đang mở:** `{st.session_state.active_file_name}` ({len(st.session_state.contract_text)} ký tự)")

with col_act2:
    run_btn = st.button("⚡ CHẠY RÀ SOÁT TOÀN DIỆN", type="primary", use_container_width=True, disabled=not bool(st.session_state.contract_text))

# XỬ LÝ KHI BẤM CHẠY PIPELINE
if run_btn:
    try:
        progress_bar = st.progress(0, text="Khởi động pipeline...")
        
        # 1. Agent 1: Extractor
        progress_bar.progress(20, text="🤖 [Agent 1] Đang trích xuất Metadata hợp đồng...")
        extractor = ExtractorAgent()
        st.session_state.metadata = extractor.extract(st.session_state.contract_text)
        
        # 2. Agent 2: Risk Analyzer
        progress_bar.progress(50, text="🛡️ [Agent 2] Đang đối chiếu 28 quy tắc pháp lý & trích dẫn điều luật...")
        analyzer = RiskAnalyzerAgent()
        st.session_state.risk_result = analyzer.analyze(st.session_state.contract_text)
        
        # 3. Agent 3: Proposal & Redlining
        progress_bar.progress(80, text="✍️ [Agent 3] Đang soạn thảo điều khoản sửa đổi & kịch bản đàm phán...")
        proposal_agent = ProposalAgent()
        st.session_state.review_package = proposal_agent.generate_review_package(
            contract_text=st.session_state.contract_text,
            risk_analysis=st.session_state.risk_result,
            metadata=st.session_state.metadata
        )
        
        progress_bar.progress(100, text="✅ Hoàn tất rà soát! Sẵn sàng cho người dùng kiểm duyệt (HITL).")
        st.success("Hệ thống đã hoàn thành phân tích. Mời bạn kiểm tra các tab bên dưới để duyệt điều khoản!")
    except Exception as e:
        st.error(f"Đã xảy ra lỗi trong quá trình chạy: {e}")

# ============================================================
# CÁC TAB HIỂN THỊ CHỨC NĂNG
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 1. Hợp đồng & Metadata",
    "🛡️ 2. Đánh giá Rủi ro (Agent 2)",
    "✍️ 3. Đề xuất Sửa đổi & Duyệt HITL (Agent 3)",
    "📝 4. Hợp đồng Hoàn thiện Sẵn sàng Ký"
])

# ------------------------------------------------------------
# TAB 1: NỘI DUNG VĂN BẢN & METADATA
# ------------------------------------------------------------
with tab1:
    if st.session_state.metadata:
        m = st.session_state.metadata
        st.subheader("📋 Bảng Thông tin Hợp đồng (Metadata Trích xuất bởi Agent 1)")
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
            st.caption(f"📍 **Địa chỉ căn hộ/phòng trọ:** {m.property_address}")
        st.divider()

    st.subheader("📜 Toàn văn Hợp đồng Đang xem xét")
    if st.session_state.contract_text:
        st.text_area(
            "Nội dung văn bản:", 
            st.session_state.contract_text, 
            height=350, 
            disabled=True
        )
    else:
        st.info("Vui lòng chọn hoặc tải lên một bản hợp đồng từ thanh bên trái.")

# ------------------------------------------------------------
# TAB 2: ĐÁNH GIÁ RỦI RO CỦA AGENT 2
# ------------------------------------------------------------
with tab2:
    if not st.session_state.risk_result:
        st.info("Chưa có kết quả rà soát. Hãy bấm nút **'⚡ CHẠY RÀ SOÁT TOÀN DIỆN'** phía trên.")
    else:
        res = st.session_state.risk_result
        col_res1, col_res2, col_res3 = st.columns([1, 1, 2])
        
        with col_res1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Tổng số rủi ro phát hiện", res.total_risks)
            st.markdown(f'<span class="badge-red">Mức ĐỎ (Cấm): {res.red_risks_count}</span> &nbsp; <span class="badge-yellow">Mức VÀNG (Bất lợi): {res.yellow_risks_count}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_res2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            if res.is_safe:
                st.metric("Đánh giá độ an toàn", "10.0 / 10.0")
                st.markdown('<span class="badge-green">HỢP ĐỒNG SẠCH AN TOÀN</span>', unsafe_allow_html=True)
            else:
                score = round(max(1.0, 10.0 - (res.red_risks_count * 2.5) - (res.yellow_risks_count * 1.0)), 1)
                st.metric("Điểm an toàn ban đầu", f"{score} / 10.0")
                st.markdown('<span class="badge-red">CẦN ĐÀM PHÁN SỬA ĐỔI</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_res3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("**Nhận định pháp lý tổng quan:**")
            st.write(res.overall_assessment)
            st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("🔎 Chi tiết Từng Điều khoản Vi phạm")
        if not res.risks:
            st.success("🎉 Không phát hiện bất kỳ điều khoản vi phạm nào! Hợp đồng tuân thủ đúng pháp luật.")
        else:
            for idx, risk in enumerate(res.risks, 1):
                badge_class = "badge-red" if risk.risk_level.upper() == "RED" else "badge-yellow"
                badge_label = "MỨC ĐỎ (Vi phạm điều cấm)" if risk.risk_level.upper() == "RED" else "MỨC VÀNG (Bất bình đẳng)"
                
                with st.expander(f"[{idx}] {risk.rule_name} ({risk.risk_level}) - {risk.related_article or 'Điều khoản hợp đồng'}", expanded=True):
                    st.markdown(f'<span class="{badge_class}">{badge_label}</span> &nbsp; <b>Nhóm:</b> {risk.category}', unsafe_allow_html=True)
                    st.markdown(f"**Căn cứ pháp lý:** `{risk.legal_basis}`")
                    if risk.statutory_citation:
                        st.markdown(f"**Trích dẫn điều luật (Citation):** {risk.statutory_citation}")
                    if risk.reference_url:
                        st.markdown(f"🔗 **Tra cứu Cơ sở dữ liệu vbpl.vn:** [{risk.reference_url}]({risk.reference_url})")

                    st.markdown("**Trích dẫn nguyên văn câu gốc từ hợp đồng:**")
                    st.markdown(f'<div class="diff-orig">"{risk.original_clause}"</div>', unsafe_allow_html=True)

                    st.markdown(f"**Giải thích rủi ro:** {risk.explanation}")
                    if risk.suggested_action:
                        st.info(f"💡 **Khuyến nghị xử lý:** {risk.suggested_action}")

# ------------------------------------------------------------
# TAB 3: ĐỀ XUẤT SỬA ĐỔI, CITATION & VÒNG LẶP HITL
# ------------------------------------------------------------
with tab3:
    if not st.session_state.review_package or not st.session_state.review_package.proposals:
        st.info("Chưa có đề xuất sửa đổi nào cần duyệt (Hợp đồng không có lỗi hoặc chưa chạy rà soát).")
    else:
        pkg = st.session_state.review_package
        
        # Tính toán điểm an toàn hiện tại theo trạng thái HITL
        current_score = HITLController.calculate_post_hitl_safety_score(pkg)
        all_completed = pkg.is_hitl_completed

        col_h1, col_h2, col_h3 = st.columns([1, 1, 1])
        with col_h1:
            st.metric("Điểm an toàn ban đầu", f"{pkg.safety_score}/10.0")
        with col_h2:
            st.metric("Điểm an toàn sau khi duyệt", f"{current_score}/10.0", delta=round(current_score - pkg.safety_score, 1))
        with col_h3:
            status_text = "✅ ĐÃ DUYỆT XONG TẤT CẢ" if all_completed else "⏳ ĐANG CHỜ DUYỆT"
            st.metric("Trạng thái HITL", status_text)

        st.caption("💡 **Cơ chế Human-in-the-Loop (HITL):** AI tham mưu câu sửa và căn cứ luật. Bạn có toàn quyền chọn **Chấp thuận (Dùng câu AI)**, **Tự sửa lại theo ý mình**, hoặc **Bác bỏ (Giữ câu gốc của chủ nhà)**.")

        # Nút duyệt nhanh tất cả
        if st.button("⚡ Duyệt nhanh tất cả đề xuất theo gợi ý của AI (Bulk Approve)", use_container_width=False):
            HITLController.bulk_approve(pkg)
            st.success("Đã phê duyệt tất cả các đề xuất của AI!")
            st.rerun()

        st.divider()

        # Danh sách duyệt từng điều khoản
        for i, prop in enumerate(pkg.proposals):
            status_icons = {
                "APPROVED": "✅ ĐÃ PHÊ DUYỆT (Áp dụng đề xuất AI)",
                "MODIFIED": "✏️ ĐÃ CHỈNH SỬA (Theo ý riêng của bạn)",
                "REJECTED": "❌ BÁC BỎ (Giữ nguyên văn gốc chủ nhà)",
                "PENDING_REVIEW": "⏳ CHỜ BẠN DUYỆT (Pending Review)"
            }
            status_badge = status_icons.get(prop.hitl_status, prop.hitl_status)

            with st.container():
                st.markdown(f"#### Đề xuất {prop.proposal_id}: {prop.rule_name}")
                st.caption(f"**Vị trí:** {prop.related_article or 'Hợp đồng'} | **Trạng thái hiện tại:** {status_badge}")

                # Bảng so sánh Before vs After
                col_diff1, col_diff2 = st.columns(2)
                with col_diff1:
                    st.markdown("**❌ Câu văn gốc của chủ nhà:**")
                    st.markdown(f'<div class="diff-orig">"{prop.original_clause}"</div>', unsafe_allow_html=True)
                with col_diff2:
                    st.markdown("**✅ Câu văn đề xuất sửa đổi của AI:**")
                    st.markdown(f'<div class="diff-proposed">"{prop.proposed_clause}"</div>', unsafe_allow_html=True)

                # Dẫn chứng Citation & vbpl.vn
                st.markdown(f"⚖️ **Căn cứ pháp lý (Citation):** `{prop.statutory_citation}`")
                if prop.reference_url:
                    st.markdown(f"🔗 **Cơ sở dữ liệu Quốc gia vbpl.vn:** [{prop.reference_url}]({prop.reference_url})")

                # Kịch bản đàm phán gửi chủ nhà
                with st.expander("💬 Xem Kịch bản đàm phán gửi chủ nhà", expanded=False):
                    st.markdown(f'<div class="script-box">"{prop.negotiation_script}"</div>', unsafe_allow_html=True)
                    if prop.compromise_option:
                        st.caption(f"🛡️ **Phương án nhượng bộ bậc 2 (dự phòng):** {prop.compromise_option}")

                # CÁC NÚT BẤM HUMAN-IN-THE-LOOP
                st.markdown("**Hành động của bạn (HITL Decision):**")
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])

                with btn_col1:
                    if st.button(f"✅ Đồng ý dùng câu AI", key=f"app_{prop.proposal_id}", use_container_width=True):
                        HITLController.review_proposal(pkg, prop.proposal_id, "APPROVE")
                        st.rerun()

                with btn_col2:
                    if st.button(f"❌ Giữ nguyên câu gốc", key=f"rej_{prop.proposal_id}", use_container_width=True):
                        HITLController.review_proposal(pkg, prop.proposal_id, "REJECT")
                        st.rerun()

                with btn_col3:
                    with st.popover(f"✏️ Tự sửa câu này theo ý riêng", use_container_width=True):
                        st.markdown(f"**Chỉnh sửa nội dung cho {prop.proposal_id}:**")
                        default_edit_val = prop.user_custom_clause or prop.proposed_clause
                        custom_edit_text = st.text_area(
                            "Nhập câu văn bạn muốn đưa vào hợp đồng:",
                            value=default_edit_val,
                            key=f"txt_{prop.proposal_id}",
                            height=100
                        )
                        note_text = st.text_input("Ghi chú cá nhân (nếu có):", value=prop.user_notes or "", key=f"note_{prop.proposal_id}")
                        if st.button("💾 Lưu và Chốt câu tự sửa", key=f"save_{prop.proposal_id}"):
                            HITLController.review_proposal(
                                pkg, 
                                prop.proposal_id, 
                                "MODIFY", 
                                custom_clause=custom_edit_text,
                                user_notes=note_text
                            )
                            st.success("Đã cập nhật câu văn tự chỉnh sửa!")
                            st.rerun()

                # Hiển thị câu văn chốt cuối cùng
                if prop.final_clause:
                    st.info(f"📌 **Câu văn chốt cuối cùng sẽ vào hợp đồng:** \"{prop.final_clause}\"")

                st.divider()

# ------------------------------------------------------------
# TAB 4: HỢP ĐỒNG HOÀN THIỆN & XUẤT BẢN
# ------------------------------------------------------------
with tab4:
    if not st.session_state.review_package:
        st.info("Chưa có hợp đồng nào được rà soát.")
    else:
        pkg = st.session_state.review_package
        
        # Tái cấu trúc hợp đồng
        final_contract_text = HITLController.assemble_final_contract(st.session_state.contract_text, pkg)
        diff_report_md = HITLController.generate_diff_report(pkg)
        post_score = HITLController.calculate_post_hitl_safety_score(pkg)

        st.subheader("📑 Bản Hợp đồng Hoàn thiện (Signed-Ready Contract)")
        st.caption("Các điều khoản vi phạm đã được tự động thay thế bằng nội dung mà bạn và AI đã phê duyệt ở Tab 3.")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("Điểm an toàn hợp đồng sau khi sửa", f"{post_score}/10.0")
        with col_f2:
            verdict_final = "AN TOÀN - CÓ THỂ KÝ KẾT" if post_score >= 8.0 else "CẦN THẬN TRỌNG THÊM"
            st.metric("Phán quyết sau cùng", verdict_final)

        # Download Buttons
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

        st.text_area(
            "Toàn văn hợp đồng sẵn sàng in/ký:",
            final_contract_text,
            height=450
        )
