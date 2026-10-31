# ⚖️ Hệ Thống Hỗ Trợ Rà Soát và Đề Xuất Hợp Đồng Thuê Nhà

Hệ thống **Document AI** và **Multi-Agent Reflection** hỗ trợ nhận diện, bóc tách dữ liệu có cấu trúc và đánh giá rủi ro pháp lý trong các hợp đồng thuê nhà ở/phòng trọ tại Việt Nam.

---

## 📌 Tính Năng Cốt Lõi

1. **Đa dạng định dạng đầu vào (Document Ingestion & OCR)**:
   - Hỗ trợ file ảnh chụp điện thoại/ảnh scan (`.png`, `.jpg`, `.jpeg`, `.webp`) bằng Vision AI nhận diện tiếng Việt.
   - Hỗ trợ tệp văn bản số hóa (`.docx`, `.pdf`, `.txt`).
2. **Bóc tách thông tin có cấu trúc (Structured Extraction - Agent 1)**:
   - Tự động trích xuất các trường quan trọng: Chủ thể (Bên A, Bên B), Địa chỉ, Tiền thuê, Tiền cọc, Kỳ thanh toán, Thời hạn báo trước,...
   - Ép kiểu dữ liệu chuẩn xác qua schema Pydantic (`ContractMetadata`).
3. **Phân tích rủi ro & Điều khoản vi phạm (Risk Analyzer - Agent 2)**:
   - Đối chiếu nội dung hợp đồng với Bộ quy tắc luật đóng kín (`data/legal_rules.json`) dựa trên **Bộ luật Dân sự 2015** và **Luật Nhà ở 2023**.
   - Phát hiện các điều khoản bất lợi (tăng giá bất hợp lý, xâm phạm chỗ ở, giữ cọc trái luật, đơn phương chấm dứt hợp đồng).
   - Trích xuất dẫn chứng nguyên văn (Citation) từ văn bản gốc.
4. **Đề xuất câu văn sửa đổi (Proposal Agent - Agent 3 & HITL)**:
   - Tự động soạn thảo phương án thay thế (Redlining) theo văn phong đàm phán hợp tác, bảo vệ quyền lợi người thuê mà vẫn hợp lý với chủ nhà.
   - Cơ chế Human-In-The-Loop (HITL) cho phép người dùng phê duyệt/chỉnh sửa trước khi xuất bản hợp đồng hoàn chỉnh.
5. **Giao diện trực quan (Streamlit Dashboard)**:
   - Giao diện người dùng thân thiện, hiển thị trực quan mức độ rủi ro (Đỏ / Vàng), bảng so sánh trước - sau (Side-by-Side Diff) và cho phép tải báo cáo rà soát.

---

## 🏗️ Kiến Trúc Hệ Thống

```text
[Ảnh chụp / PDF Scan / File Word]
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1: DOCUMENT PARSING & OCR (Vision AI)        │
│ - Tự động nhận diện định dạng: docx, pdf, image, txt   │
│ - Chuẩn hóa ký tự Unicode tiếng Việt                   │
└────────────────────────────────────────────────────────┘
                │
                ▼ Văn bản thô
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 2: STRUCTURED EXTRACTION (Agent 1)           │
│ - Schema Pydantic: ContractMetadata                    │
└────────────────────────────────────────────────────────┘
                │
                ▼ Metadata + Văn bản
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 3: MULTI-AGENT RISK ENGINE (Agent 2 & Agent 3)│
│ - Risk Analyzer Agent: Đối chiếu data/legal_rules.json │
│ - Proposal Agent: Soạn thảo câu văn Redline thay thế   │
└────────────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 4: HUMAN-IN-THE-LOOP & STREAMLIT DASHBOARD   │
│ - Review, Duyệt điều khoản, Xuất báo cáo Markdown      │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Cấu Trúc Thư Mục

```text
NLP/
├── app.py                      # Ứng dụng Streamlit Dashboard chính
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── .env.example                # File mẫu cấu hình biến môi trường
├── .gitignore                  # Cấu hình bỏ qua tệp tạm & bí mật
├── README.md                   # Tài liệu hướng dẫn dự án
├── bao_cao_tong_quan_du_an.md  # Báo cáo tổng quan chi tiết đề tài
├── project_plan_5_weeks.md     # Kế hoạch triển khai dự án
├── data/
│   ├── legal_rules.json        # Bộ luật và quy tắc pháp lý chuẩn
│   ├── golden_dataset_120.json # Dataset đánh giá chuẩn hóa 120 mẫu
│   └── contracts/              # Tập dữ liệu 120 hợp đồng mẫu
├── src/
│   ├── agents/                 # Các Agent: Extractor, Risk Analyzer, Proposal, HITL
│   ├── parsers/                # Các bộ bóc tách: DOCX, PDF, OCR Vision
│   └── utils/                  # Script sinh dữ liệu và tiện ích
└── test_*.py                   # Bộ kiểm thử cho từng agent và pipeline
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### 1. Yêu cầu môi trường
- Python >= 3.10

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình API Key
Sao chép tệp cấu hình mẫu và điền API Key của bạn:
```bash
cp .env.example .env
```
Mở `.env` và điền khóa API (hỗ trợ **OpenRouter**, **Google Gemini** hoặc **OpenAI**):
```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-flash
```

### 4. Khởi chạy Dashboard
```bash
streamlit run app.py
```
Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ: `http://localhost:8501`.

---

## 🧪 Chạy Kiểm Thử (Unit Tests)

Bạn có thể chạy thử nghiệm độc lập từng module trong hệ thống:
```bash
# Kiểm thử Agent 1: Bóc tách thông tin có cấu trúc
python test_extractor.py

# Kiểm thử Module OCR nhận diện ảnh scan hợp đồng
python test_ocr_pipeline.py

# Kiểm thử Agent 2: Phân tích rủi ro theo quy tắc luật
python test_risk_analyzer.py

# Kiểm thử Agent 3: Đề xuất câu văn sửa đổi (Redlining)
python test_proposal_pipeline.py
```

