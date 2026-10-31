import json
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# BẢNG THAM CHIẾU URL CHÍNH THỨC TRÊN CỔNG CSDL QUỐC GIA VBPL.VN
VBPL_URLS = {
    "HIEN_PHAP_2013": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32801",
    "BLDS_2015": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=96420",
    "LUAT_NHA_O_2023": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=163273",
    "LUAT_KDBDS_2023": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=163351",
    "ND_96_2024": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=168051",
    "ND_134_2013": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32371",
    "LUAT_CU_TRU_2020": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=144671",
    "ND_144_2021": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=151877"
}

def get_citation_info(rule_id: str, legal_basis: str) -> tuple[str, str]:
    """Trả về (statutory_citation, reference_url) chuẩn xác cho từng rule."""
    lb_upper = legal_basis.upper()

    if "HIẾN PHÁP" in lb_upper:
        url = VBPL_URLS["HIEN_PHAP_2013"]
    elif "96/2024" in lb_upper:
        url = VBPL_URLS["ND_96_2024"]
    elif "134/2013" in lb_upper or "17/2022" in lb_upper:
        url = VBPL_URLS["ND_134_2013"]
    elif "CƯ TRÚ" in lb_upper:
        url = VBPL_URLS["LUAT_CU_TRU_2020"]
    elif "NHÀ Ở 2023" in lb_upper and "DÂN SỰ" not in lb_upper:
        url = VBPL_URLS["LUAT_NHA_O_2023"]
    elif "KINH DOANH BẤT ĐỘNG SẢN" in lb_upper:
        url = VBPL_URLS["LUAT_KDBDS_2023"]
    else:
        url = VBPL_URLS["BLDS_2015"]

    citation = legal_basis.split("&")[0].strip() if "&" in legal_basis else legal_basis.strip()
    return citation, url

def main():
    rules_path = os.path.join("data", "legal_rules.json")
    with open(rules_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rules = data.get("rules", [])
    for r in rules:
        citation, url = get_citation_info(r["rule_id"], r["legal_basis"])
        r["statutory_citation"] = citation
        r["reference_url"] = url

    data["version"] = "1.3"
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã gắn thành công Legal Citation và URL VBPL.VN cho toàn bộ {len(rules)} quy tắc!")
    print(f"👉 File cập nhật: {rules_path}")

if __name__ == "__main__":
    main()
