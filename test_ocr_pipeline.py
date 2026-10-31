import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Đảm bảo in tiếng Việt chuẩn trên Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("."))

from src.parsers import parse_contract_file
from src.agents import ExtractorAgent

def create_sample_contract_image(output_path: str = "sample_scanned_contract.png"):
    """
    Tạo một file ảnh hợp đồng giả lập ảnh chụp/scan để kiểm thử OCR.
    """
    # Kích thước ảnh chuẩn A4 tỷ lệ tương đối (1200 x 1000)
    img = Image.new("RGB", (1200, 950), color=(248, 249, 250))
    d = ImageDraw.Draw(img)

    # Thêm viền giả lập trang giấy scan
    d.rectangle([(15, 15), (1185, 935)], outline=(200, 200, 200), width=2)

    # Vẽ nội dung văn bản hợp đồng tiếng Việt
    lines = [
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "Độc lập - Tự do - Hạnh phúc",
        "------------------------------------",
        "HỢP ĐỒNG CHO THUÊ CĂN HỘ CHUNG CƯ",
        "Số: 48/2026/HĐT-NO",
        "",
        "Hôm nay, ngày 15 tháng 10 năm 2026, tại Hà Nội, chúng tôi gồm có:",
        "",
        "I. BÊN CHO THUÊ (BÊN A):",
        "- Họ và tên: Ông TRẦN ĐĂNG KHOA",
        "- CCCD số: 001082009841 do Cục CSQLHC về TTXH cấp ngày 12/04/2021",
        "- Địa chỉ thường trú: Số 45 phố Phan Đình Phùng, Ba Đình, Hà Nội",
        "- Số điện thoại liên hệ: 0912.345.678",
        "",
        "II. BÊN THUÊ (BÊN B):",
        "- Họ và tên: Bà NGUYỄN PHƯƠNG THẢO",
        "- CCCD số: 036195004123 do Cục CSQLHC về TTXH cấp ngày 20/08/2022",
        "- Địa chỉ thường trú: Số 12 phố Trần Phú, TP. Nam Định",
        "- Số điện thoại: 0988.765.432",
        "",
        "Hai bên thống nhất ký kết hợp đồng thuê nhà với các điều khoản sau:",
        "Điều 1. Đối tượng hợp đồng: Căn hộ số 1205, Tòa S2.05, KĐT Vinhomes Smart City, Nam Từ Liêm, Hà Nội.",
        "Điều 2. Thời hạn thuê: 12 tháng, tính từ ngày 01/11/2026 đến hết ngày 31/10/2027.",
        "Điều 3. Giá thuê và tiền đặt cọc:",
        "  - Giá thuê: 8.500.000 đồng/tháng (Tám triệu năm trăm nghìn đồng). Thanh toán vào ngày 05 hàng tháng.",
        "  - Tiền đặt cọc: 8.500.000 đồng nộp ngay khi ký hợp đồng.",
        "  - Tiền điện nước: Theo hóa đơn nhà nước ban hành.",
        "Điều 4. Chấm dứt hợp đồng:",
        "  - Mỗi bên có quyền chấm dứt hợp đồng nhưng phải báo trước bằng văn bản tối thiểu 30 ngày.",
        "  - Tiền cọc sẽ được hoàn trả cho Bên B sau khi bàn giao lại căn hộ nguyên trạng."
    ]

    y_offset = 35
    for line in lines:
        d.text((50, y_offset), line, fill=(20, 20, 20))
        y_offset += 28

    img.save(output_path, quality=95)
    print(f"✅ Đã tạo file ảnh scan giả lập: {output_path}")
    return output_path

def main():
    print("=" * 70)
    print("🚀 KIỂM THỬ PIPELINE ĐẶC BIỆT: OCR PARSING & BÓC TÁCH DỮ LIỆU TỪ ẢNH")
    print("=" * 70)

    # 1. Tạo file ảnh giả lập
    image_file = create_sample_contract_image("sample_scanned_contract.png")

    # 2. Chạy Module OCR
    print("\n📸 [BƯỚC 1] Đang thực hiện OCR nhận diện văn bản tiếng Việt từ ảnh...")
    ocr_result_text = parse_contract_file(image_file)
    print("\n--- NỘI DUNG VĂN BẢN TRÍCH XUẤT TỪ ẢNH (OCR OUTPUT) ---")
    print(ocr_result_text[:700] + "...\n(còn tiếp)")
    print("-" * 70)

    # 3. Chạy Module Bóc tách (Agent 1 Extractor)
    print("\n🧠 [BƯỚC 2] Đang bóc tách dữ liệu có cấu trúc từ văn bản OCR (Parsing)...")
    extractor = ExtractorAgent()
    metadata = extractor.extract(ocr_result_text)

    print("\n🎉 KẾT QUẢ BÓC TÁCH HOÀN CHỈNH (STRUCTURED JSON METADATA):")
    print("=" * 70)
    print(metadata.model_dump_json(indent=2))
    print("=" * 70)
    print(f"👤 Bên cho thuê (A)   : {metadata.lessor_name}")
    print(f"👤 Bên thuê (B)       : {metadata.lessee_name}")
    print(f"🏠 Địa chỉ căn hộ     : {metadata.property_address}")
    print(f"💰 Giá thuê hàng tháng: {metadata.rent_price:,.0f} VNĐ")
    print(f"🔒 Tiền đặt cọc       : {metadata.deposit_amount:,.0f} VNĐ")
    print(f"⏱️ Thời hạn thuê      : {metadata.lease_term_months} tháng ({metadata.start_date} -> {metadata.end_date})")
    print(f"📅 Hạn báo trước      : {metadata.notice_period_days} ngày")
    print(f"📝 Tóm tắt chấm dứt   : {metadata.termination_clause_summary}")
    print("=" * 70)

if __name__ == "__main__":
    main()
