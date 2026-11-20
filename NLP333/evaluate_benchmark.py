"""
Evaluation & Benchmark Script: Đánh giá định lượng hiệu năng của hệ thống Legal NLP
trên các khía cạnh: Precision, Recall, F1-Score, False Positive Rate (FPR) và Latency.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("."))

from src.agents.risk_analyzer_agent import RiskAnalyzerAgent
from src.agents.reflection_critic import ReflectionCritic
from src.retrieval.legal_kb import LegalKnowledgeBase

BENCHMARK_SUITE = [
    {
        "domain": "rental",
        "file": "data/contracts/HD_001.txt",
        "name": "HD_001_Clean (Mẫu chuẩn Bộ Xây dựng)",
        "expected_safe": True,
        "expected_risks_count": 0,
        "critical_rules": []
    },
    {
        "domain": "rental",
        "file": "data/contracts/HD_015.txt",
        "name": "HD_015_Electricity_Lock (Điện 3.800đ & Khóa cọc)",
        "expected_safe": False,
        "expected_risks_count": 2,
        "critical_rules": ["RULE_ELECTRICITY_OVERCHARGE", "RULE_NO_EARLY_TERMINATION_RIGHT"]
    },
    {
        "domain": "rental",
        "file": "data/contracts/HD_045.txt",
        "name": "HD_045_Double_Penalty (Phạt cọc kép & Tăng giá)",
        "expected_safe": False,
        "expected_risks_count": 2,
        "critical_rules": ["RULE_DOUBLE_PENALTY", "RULE_UNILATERAL_RENT_INCREASE"]
    },
    {
        "domain": "employment",
        "file": "data/contracts_employment/HD_LD_001_chuan_muc.txt",
        "name": "HD_LD_001_Clean (Chuẩn Bộ LĐTBXH)",
        "expected_safe": True,
        "expected_risks_count": 0,
        "critical_rules": []
    },
    {
        "domain": "employment",
        "file": "data/contracts_employment/HD_LD_002_thu_viec_cai_bay.txt",
        "name": "HD_LD_002_Probation_Trap (Giữ CCCD, Lương 70%, Cọc tiền)",
        "expected_safe": False,
        "expected_risks_count": 4,
        "critical_rules": ["RULE_LABOR_RETAIN_PAPERS", "RULE_LABOR_DEPOSIT_MONEY", "RULE_LABOR_PROBATION_SALARY_UNDER_85", "RULE_LABOR_PROBATION_EXCESSIVE_DURATION"]
    },
    {
        "domain": "employment",
        "file": "data/contracts_employment/HD_LD_003_nda_va_khong_canh_tranh.txt",
        "name": "HD_LD_003_NonCompete_WageDeduction (Cấm làm ngành 3 năm, Trừ 50% lương)",
        "expected_safe": False,
        "expected_risks_count": 3,
        "critical_rules": ["RULE_LABOR_NON_COMPETE_OVERBROAD", "RULE_LABOR_TRAINING_REIMBURSEMENT_EXCESSIVE", "RULE_LABOR_WAGE_DEDUCTION_LIMIT"]
    },
    {
        "domain": "employment",
        "file": "data/contracts_employment/HD_LD_004_tron_bhxh_ep_ot.txt",
        "name": "HD_LD_004_Insurance_Overtime (Trốn BHXH, Ép OT, Đuổi việc 24h)",
        "expected_safe": False,
        "expected_risks_count": 4,
        "critical_rules": ["RULE_LABOR_INSURANCE_EVASION", "RULE_LABOR_MANDATORY_OVERTIME", "RULE_LABOR_UNILATERAL_TERMINATION_NOTICE"]
    }
]

def run_benchmark():
    print("=" * 80)
    print("🚀 BẮT ĐẦU CHẠY BENCHMARK ĐỊNH LƯỢNG HỆ THỐNG LEGAL NLP (NLP333)")
    print("   Phạm vi: Đa lĩnh vực (Thuê nhà & Lao động) | Đa góc nhìn (Bên A & Bên B)")
    print("=" * 80)

    analyzer = RiskAnalyzerAgent()
    critic = ReflectionCritic()
    results = []

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_tn = 0
    total_latency = 0.0

    for idx, test_case in enumerate(BENCHMARK_SUITE, 1):
        file_path = Path(test_case["file"])
        if not file_path.exists():
            print(f"⚠️ Bỏ qua {test_case['name']}: Không tìm thấy file {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"\n[{idx}/{len(BENCHMARK_SUITE)}] 📄 Đang đánh giá: {test_case['name']}...")
        start_t = time.time()
        
        try:
            analysis = analyzer.analyze(
                contract_text=content,
                contract_type=test_case["domain"],
                perspective="party_b"
            )
            refined = critic.critique_and_refine(content, analysis)

            elapsed = time.time() - start_t
            total_latency += elapsed

            detected_rules = set(r.rule_id for r in refined.risks)
            expected_rules = set(test_case["critical_rules"])

            is_clean_expected = test_case["expected_safe"]
            is_clean_actual = refined.is_safe

            if is_clean_expected and is_clean_actual:
                total_tn += 1
                status = "✅ PASS (True Negative - Không báo động giả)"
            elif not is_clean_expected and not is_clean_actual:
                total_tp += 1
                status = "✅ PASS (True Positive - Phát hiện chính xác vi phạm)"
            elif is_clean_expected and not is_clean_actual:
                total_fp += 1
                status = "❌ FAIL (False Positive - Báo động nhầm)"
            else:
                total_fn += 1
                status = "❌ FAIL (False Negative - Bỏ sót vi phạm)"

            matched_critical = detected_rules.intersection(expected_rules)
            rule_coverage = (len(matched_critical) / len(expected_rules) * 100) if expected_rules else 100.0

            case_res = {
                "name": test_case["name"],
                "domain": test_case["domain"],
                "latency_sec": round(elapsed, 2),
                "status": status,
                "detected_count": refined.total_risks,
                "expected_count": test_case["expected_risks_count"],
                "rule_coverage_pct": round(rule_coverage, 1),
                "citations_attached": sum(1 for r in refined.risks if r.statutory_citation)
            }
            results.append(case_res)

            print(f"   ⏱️ Thời gian phản hồi: {case_res['latency_sec']}s")
            print(f"   🎯 Kết quả: {case_res['status']}")
            print(f"   🔍 Số rủi ro: {refined.total_risks} (Đỏ: {refined.red_risks_count}, Vàng: {refined.yellow_risks_count})")
            print(f"   📖 Độ phủ rule: {case_res['rule_coverage_pct']}%")

        except Exception as e:
            print(f"   ❌ Lỗi khi thực thi: {e}")

    total_samples = total_tp + total_tn + total_fp + total_fn
    accuracy = (total_tp + total_tn) / total_samples if total_samples > 0 else 0.0
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    avg_latency = total_latency / total_samples if total_samples > 0 else 0.0

    print("\n" + "=" * 80)
    print("📊 BẢNG TỔNG HỢP KẾT QUẢ BENCHMARK (ACADEMIC METRICS)")
    print("=" * 80)
    print(f"• Tổng số mẫu kiểm thử:           {total_samples}")
    print(f"• Độ chính xác tổng thể (Accuracy): {accuracy * 100:.2f}%")
    print(f"• Độ chuẩn xác (Precision):        {precision * 100:.2f}%")
    print(f"• Độ bao phủ (Recall):             {recall * 100:.2f}%")
    print(f"• F1-Score:                        {f1 * 100:.2f}%")
    print(f"• Tỷ lệ báo động giả (FPR):        {(total_fp / (total_fp + total_tn) * 100 if (total_fp + total_tn) > 0 else 0.0):.2f}%")
    print(f"• Thời gian phản hồi trung bình:   {avg_latency:.2f}s")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmark()

