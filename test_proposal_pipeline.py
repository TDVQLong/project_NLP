import sys
import io
import os
import json
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from src.agents import (
    ExtractorAgent,
    RiskAnalyzerAgent,
    ProposalAgent,
    HITLController
)

def test_full_agent_pipeline():
    print("=" * 70)
    print(" KIỂM THỬ TOÀN DIỆN PIPELINE AGENT 1 -> AGENT 2 -> AGENT 3 + HITL")
    print("=" * 70)

    # 1. Nạp file hợp đồng mẫu có rủi ro HD_015.txt
    contract_file = Path("data/contracts/HD_015.txt")
    if not contract_file.exists():
        print(f"Lỗi: Không tìm thấy file {contract_file}")
        return

    contract_text = contract_file.read_text(encoding="utf-8")
    print(f"\n[1] Đã nạp văn bản hợp đồng: {contract_file.name} ({len(contract_text)} ký tự)")

    # 2. Chạy Agent 1: Trích xuất Metadata
    print("\n--- [AGENT 1: STRUCTURED EXTRACTOR] ---")
    extractor = ExtractorAgent()
    metadata = extractor.extract(contract_text)
    print(f"✓ Chủ nhà (Bên A): {metadata.lessor_name}")
    print(f"✓ Khách thuê (Bên B): {metadata.lessee_name}")
    print(f"✓ Giá thuê: {metadata.rent_price:,.0f} đ/tháng | Tiền cọc: {metadata.deposit_amount:,.0f} đ")
    print(f"✓ Thời hạn thuê: {metadata.lease_term_months} tháng")

    # 3. Chạy Agent 2: Rà soát rủi ro pháp lý & Trích dẫn điều luật
    print("\n--- [AGENT 2: RISK ANALYZER (28 RULES)] ---")
    analyzer = RiskAnalyzerAgent()
    risk_result = analyzer.analyze(contract_text)
    print(f"✓ Phát hiện rủi ro: {risk_result.total_risks} điều khoản")
    print(f"  - Đỏ (Nghiêm trọng): {risk_result.red_risks_count}")
    print(f"  - Vàng (Bất lợi): {risk_result.yellow_risks_count}")
    for idx, r in enumerate(risk_result.risks, 1):
        print(f"  [{idx}] ({r.risk_level}) {r.rule_name} | {r.statutory_citation}")
        print(f"      Trích dẫn gốc: \"{r.original_clause[:70]}...\"")

    # 4. Chạy Agent 3: Đề xuất sửa đổi (Redlines), Gắn Citation & Kịch bản đàm phán
    print("\n--- [AGENT 3: PROPOSAL & REDLINING AGENT] ---")
    proposal_agent = ProposalAgent()
    package = proposal_agent.generate_review_package(
        contract_text=contract_text,
        risk_analysis=risk_result,
        metadata=metadata
    )
    print(f"✓ Phán quyết: {package.verdict}")
    print(f"✓ Điểm an toàn ban đầu: {package.safety_score}/10.0")
    print(f"✓ Tổng số đề xuất sửa đổi: {len(package.proposals)}")

    # 5. MÔ PHỎNG QUY TRÌNH HUMAN-IN-THE-LOOP (HITL)
    print("\n--- [HUMAN-IN-THE-LOOP (HITL) INTERACTION] ---")
    print("Người dùng tiến hành duyệt từng điều khoản do AI tham mưu:\n")

    for i, prop in enumerate(package.proposals):
        print(f">> Xem xét Đề xuất {prop.proposal_id} ({prop.rule_name}):")
        print(f"   + Câu gốc: \"{prop.original_clause[:80]}...\"")
        print(f"   + Đề xuất AI: \"{prop.proposed_clause[:80]}...\"")
        print(f"   + Căn cứ (Citation): {prop.statutory_citation}")
        print(f"   + Tra cứu vbpl.vn: {prop.reference_url}")

        if i == 0:
            # Điều khoản 1: Con người duyệt chấp thuận phương án AI đề xuất
            print("   -> [HÀNH ĐỘNG]: APPROVE (Đồng ý áp dụng phương án AI)")
            HITLController.review_proposal(package, prop.proposal_id, "APPROVE")
        elif i == 1:
            # Điều khoản 2: Con người tự chỉnh sửa lại theo thỏa thuận riêng
            custom_text = (
                "Hai bên thống nhất: Nếu Bên B trả phòng trước hạn, Bên B phải báo trước 30 ngày "
                "và hỗ trợ Bên A 50% tiền cọc tháng đó để đăng tin tìm khách thuê mới."
            )
            print(f"   -> [HÀNH ĐỘNG]: MODIFY (Người dùng tự điều chỉnh câu chữ)")
            HITLController.review_proposal(
                package, 
                prop.proposal_id, 
                "MODIFY", 
                custom_clause=custom_text,
                user_notes="Đã gọi điện trao đổi riêng với bác An chủ nhà và bác đồng ý mức này."
            )
        else:
            # Điều khoản còn lại: Duyệt Approve
            print("   -> [HÀNH ĐỘNG]: APPROVE (Đồng ý phương án AI)")
            HITLController.review_proposal(package, prop.proposal_id, "APPROVE")

    print(f"\n✓ Hoàn tất quy trình HITL: is_hitl_completed = {package.is_hitl_completed}")
    post_score = HITLController.calculate_post_hitl_safety_score(package)
    print(f"✓ Điểm an toàn hợp đồng sau khi xử lý HITL: {post_score}/10.0 (Cải thiện từ {package.safety_score})")

    # 6. Tái cấu trúc văn bản hợp đồng hoàn thiện (Contract Re-assembly)
    print("\n--- [ASSEMBLING FINAL CONTRACT SẴN SÀNG KÝ] ---")
    final_contract = HITLController.assemble_final_contract(contract_text, package)
    print(f"✓ Bản hợp đồng hoàn thiện đã được tạo: {len(final_contract)} ký tự.")

    # Xuất báo cáo Diff Markdown
    diff_report = HITLController.generate_diff_report(package)
    output_diff_file = Path("data/sample_redline_diff_report.md")
    output_diff_file.write_text(diff_report, encoding="utf-8")
    print(f"✓ Đã lưu Báo cáo Redline Diff: {output_diff_file}")

    # Xuất file hợp đồng sau sửa
    output_final_file = Path("data/sample_final_contract_signed_ready.txt")
    output_final_file.write_text(final_contract, encoding="utf-8")
    print(f"✓ Đã lưu Bản hợp đồng hoàn thiện: {output_final_file}")

    print("\n" + "=" * 70)
    print(" TOÀN BỘ PIPELINE AGENT 1 + AGENT 2 + AGENT 3 + HITL ĐÃ THÀNH CÔNG!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_agent_pipeline()
