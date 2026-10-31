import os
import sys
from dotenv import load_dotenv

# Đảm bảo in tiếng Việt và ký tự đặc biệt mượt mà trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Đảm bảo đường dẫn import từ thư mục gốc dự án
sys.path.insert(0, os.path.abspath("."))

from src.parsers import parse_contract_file
from src.agents import ExtractorAgent, ContractMetadata

# Hợp đồng mẫu giả lập để kiểm thử Agent 1
SAMPLE_CONTRACT_TEXT = """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
-----------------------------
HỢP ĐỒNG THUÊ PHÒNG TRỌ

Hôm nay, ngày 01 tháng 10 năm 2026, tại Hà Nội, chúng tôi gồm có:
BÊN CHO THUÊ (BÊN A):
Ông: Nguyễn Văn An
Sinh năm: 1975
CCCD số: 001075xxxxxx
Địa chỉ: Số 18 ngõ 25 Phan Văn Trường, Dịch Vọng Hậu, Cầu Giấy, Hà Nội.

BÊN THUÊ (BÊN B):
Bà: Trần Thị Mai
Sinh năm: 2003
CCCD số: 038203xxxxxx
Hộ khẩu thường trú: TP. Nam Định, tỉnh Nam Định.

Hai bên thống nhất ký kết hợp đồng thuê phòng với các điều khoản sau:
Điều 1: Đối tượng hợp đồng
Bên A đồng ý cho Bên B thuê phòng số 302 tại địa chỉ: Số 18 ngõ 25 Phan Văn Trường, Cầu Giấy, Hà Nội.

Điều 2: Thời hạn thuê
Thời hạn thuê là 12 tháng, bắt đầu từ ngày 01/10/2026 đến hết ngày 30/09/2027.

Điều 3: Giá thuê và phương thức thanh toán
- Giá thuê phòng: 4.500.000 đồng/tháng (Bằng chữ: Bốn triệu năm trăm nghìn đồng).
- Tiền cọc: Bên B đặt cọc cho Bên A số tiền 4.500.000 đồng ngay khi ký hợp đồng.
- Tiền thuê thanh toán theo hình thức hàng tháng, vào ngày 05 của mỗi tháng.
- Tiền điện: 3.800 đ/kWh theo chỉ số công tơ riêng.
- Tiền nước: 100.000 đ/người/tháng.

Điều 4: Chấm dứt hợp đồng
Bên nào muốn chấm dứt hợp đồng trước thời hạn phải thông báo trước cho bên kia ít nhất 30 ngày bằng văn bản hoặc tin nhắn xác nhận. Tiền cọc sẽ được hoàn trả lại cho Bên B sau khi trừ các khoản chi phí dịch vụ còn nợ.
"""

def main():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")

    print("=" * 60)
    print("🔍 KIỂM THỬ AGENT 1: STRUCTURED EXTRACTOR (OPENROUTER)")
    print("=" * 60)

    if not api_key:
        print("⚠️  Chưa cấu hình OPENROUTER_API_KEY trong file .env!")
        return

    model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    print(f"🚀 Đang khởi chạy Agent 1 với OpenRouter (Model: {model_name})...")
    agent = ExtractorAgent()

    try:
        metadata = agent.extract(SAMPLE_CONTRACT_TEXT)
        print("\n🎉 KẾT QUẢ TRÍCH XUẤT THÀNH CÔNG:")
        print("-" * 60)
        print(metadata.model_dump_json(indent=2))
        print("-" * 60)
        print(f"Bên cho thuê (A) : {metadata.lessor_name}")
        print(f"Bên thuê (B)     : {metadata.lessee_name}")
        print(f"Địa chỉ thuê     : {metadata.property_address}")
        print(f"Giá thuê         : {metadata.rent_price:,.0f} VNĐ")
        print(f"Tiền cọc         : {metadata.deposit_amount:,.0f} VNĐ")
        print(f"Thời hạn thuê    : {metadata.lease_term_months} tháng")
        print(f"Bắt đầu - Kết thúc: {metadata.start_date} -> {metadata.end_date}")
        print(f"Báo trước        : {metadata.notice_period_days} ngày")
        print(f"Đơn giá điện     : {metadata.electricity_price}")
        print(f"Đơn giá nước     : {metadata.water_price}")
        print(f"Tóm tắt chấm dứt : {metadata.termination_clause_summary}")
        print("-" * 60)
    except Exception as e:
        print(f"❌ Lỗi trong quá trình trích xuất: {e}")

if __name__ == "__main__":
    main()
