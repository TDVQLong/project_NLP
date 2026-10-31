import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Đảm bảo in tiếng Việt chuẩn trên Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("."))

from src.agents import RiskAnalyzerAgent

def main():
    print("=" * 70)
    print("⚖️ KIỂM THỬ AGENT 2: RISK ANALYZER (RÀ SOÁT RỦI RO PHÁP LÝ)")
    print("=" * 70)

    analyzer = RiskAnalyzerAgent()

    # 1. TEST TRÊN HỢP ĐỒNG SẠCH (HD_001.txt) - ĐO FALSE ALARM
    clean_file = Path("data/contracts/HD_001.txt")
    print(f"\n🧪 [TEST 1] Rà soát Hợp đồng CHUẨN MỰC ({clean_file})...")
    with open(clean_file, "r", encoding="utf-8") as f:
        clean_text = f.read()

    result_clean = analyzer.analyze(clean_text)
    print(f"👉 Kết quả: An toàn? {result_clean.is_safe} | Tổng rủi ro: {result_clean.total_risks}")
    print(f"👉 Nhận định tổng quan: {result_clean.overall_assessment}")
    if result_clean.is_safe and result_clean.total_risks == 0:
        print("✅ PASS: Hệ thống nhận diện chính xác hợp đồng sạch (False Alarm = 0).")
    else:
        print("⚠️ CẢNH BÁO: Phát hiện rủi ro không mong muốn trên hợp đồng sạch!")

    # 2. TEST TRÊN HỢP ĐỒNG CÓ BẪY (HD_015.txt) - CÓ BẪY ĐIỀU 10
    violated_file = Path("data/contracts/HD_015.txt")
    print(f"\n🧪 [TEST 2] Rà soát Hợp đồng CÓ CÀI BẪY ({violated_file})...")
    with open(violated_file, "r", encoding="utf-8") as f:
        violated_text = f.read()

    result_violated = analyzer.analyze(violated_text)
    print(f"👉 Kết quả: An toàn? {result_violated.is_safe} | Tổng rủi ro: {result_violated.total_risks}")
    print(f"   🔴 Rủi ro ĐỎ (Cao): {result_violated.red_risks_count}")
    print(f"   🟡 Rủi ro VÀNG (Trung bình): {result_violated.yellow_risks_count}")
    print(f"👉 Nhận định tổng quan: {result_violated.overall_assessment}")

    print("\n📋 CHI TIẾT CÁC RỦI RO ĐƯỢC PHÁT HIỆN:")
    print("-" * 70)
    for idx, risk in enumerate(result_violated.risks, 1):
        color_icon = "🔴" if risk.risk_level.upper() == "RED" else "🟡"
        print(f"{idx}. {color_icon} [{risk.rule_id}] {risk.rule_name} ({risk.risk_level})")
        print(f"   📍 Vị trí: {risk.related_article}")
        print(f"   📜 Đoạn văn vi phạm nguyên văn:\n      \"{risk.original_clause}\"")
        print(f"   ⚖️ Căn cứ pháp lý: {risk.legal_basis}")
        if risk.statutory_citation:
            print(f"   📖 Trích dẫn điều khoản: {risk.statutory_citation}")
        if risk.reference_url:
            print(f"   🔗 Tra cứu VBPL.VN: {risk.reference_url}")
        print(f"   💡 Giải thích: {risk.explanation}")
        if risk.suggested_action:
            print(f"   🛠️ Khuyến nghị: {risk.suggested_action}")
        print("-" * 70)

    print("\n🎉 HOÀN TẤT KIỂM THỬ AGENT 2!")

if __name__ == "__main__":
    main()
