# HỆ THỐNG PHÂN TÍCH RỦI RO & RÀ SOÁT ĐIỀU KHOẢN HỢP ĐỒNG THÔNG MINH (LEGAL NLP PIPELINE)

Hệ thống ứng dụng trí tuệ nhân tạo (NLP, Hybrid RAG, Multi-Agent & Legal NLI) hỗ trợ người thuê nhà và người lao động phát hiện bẫy pháp lý, điều khoản bất lợi, vi phạm luật và tự động sinh bản sửa đổi (Redline).

---

## 🏛️ KIẾN TRÚC HỆ THỐNG 5 TẦNG (5-LAYER ARCHITECTURE)

```
[Văn bản đầu vào: PDF / DOCX / Ảnh Scan / Viết tay]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 1: INGESTION & DOCUMENT AI (Router & Vision OCR)       │
│ - router.py: Phân loại định dạng tài liệu                   │
│ - pdf_parser.py: Trích xuất Text Layer tốc độ cao           │
│ - image_preprocessor.py: Tiền xử lý xoay, cân bằng tương phản│
│ - vision_ocr.py: Vision LLM OCR phục hồi tiếng Việt có dấu  │
└────────────────────────┬────────────────────────────────────┘
                         │ Plaintext Hợp đồng
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 2: SEGMENTATION & CANONICAL ALIGNMENT                  │
│ - clause_segmenter.py: Tách điều khoản regex + logic        │
│ - baseline_aligner.py: So khớp Cosine với Mẫu Chuẩn         │
│ - omission_detector.py: Phát hiện điều khoản bị cố tình bỏ  │
└────────────────────────┬────────────────────────────────────┘
                         │ Danh sách Điều khoản {C_i}
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 3: HYBRID LEGAL RAG ENGINE                             │
│ - legal_kb.py: Cơ sở tri thức 42+ quy tắc luật              │
│ - sparse_bm25.py: Tìm kiếm từ khóa chính xác                │
│ - dense_retriever.py: Tìm kiếm ngữ nghĩa embedding          │
│ - reranker.py: Sắp xếp điều luật đối chiếu sát nhất         │
└────────────────────────┬────────────────────────────────────┘
                         │ Điều khoản + Luật đối chiếu
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 4: MULTI-AGENT & LEGAL NLI ENGINE                      │
│ - schemas.py: Pydantic Model chuẩn hóa dữ liệu              │
│ - extractor_agent.py: Bóc tách thông tin thực thể           │
│ - risk_analyzer_agent.py: Suy luận mâu thuẫn (NLI)          │
│ - reflection_critic.py: Phản biện triệt tiêu False Alarm    │
│ - proposal_agent.py: Đề xuất Redlining & Kịch bản đàm phán  │
└────────────────────────┬────────────────────────────────────┘
                         │ Báo cáo rủi ro & Phương án sửa
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ TẦNG 5: HUMAN-IN-THE-LOOP (HITL) & DOCUMENT ASSEMBLY        │
│ - hitl_controller.py: Cơ chế Duyệt / Từ chối / Chỉnh sửa    │
│ - document_assembler.py: Lắp ráp văn bản hợp đồng mới       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 CẤU TRÚC THƯ MỤC CHI TIẾT

```
NLP333/
├── .env                                # Biến môi trường (API Keys, Config)
├── .gitignore                          # Cấu hình bỏ qua tệp nhị phân, cache, .venv
├── requirements.txt                    # Danh mục thư viện phụ thuộc
├── README.md                           # Tài liệu tổng quan & hướng dẫn chạy
├── bao_cao_tong_quan_du_an.md          # Báo cáo học thuật chi tiết nộp giảng viên
├── app.py                              # Entrypoint: Giao diện Web Streamlit 3 Tabs
├── evaluate_benchmark.py               # Script chạy Benchmark đo Accuracy, F1, Latency
│
├── data/                               # === CƠ SỞ DỮ LIỆU & BỘ CHUẨN ===
│   ├── legal_rules.json                # 28 quy tắc Luật Nhà ở & BLDS 2015
│   ├── legal_rules_employment.json     # 14 quy tắc Bộ luật Lao động 2019
│   ├── golden_dataset_120.json         # 120 mẫu thuê nhà gán nhãn phân tầng độ khó
│   ├── sample_employment_canonical.json# Mẫu chuẩn Bộ LĐTBXH sạch 100% (Negative Control)
│   ├── contracts/                      # 120 tệp hợp đồng thuê nhà thực nghiệm (.txt)
│   ├── contracts_employment/           # Hợp đồng lao động mẫu & bẫy thử việc/NDA (.txt)
│   └── raw_scans/                      # Bộ ảnh scan/PDF kiểm thử thực tế (.png, .pdf)
│
├── src/                                # === TẦNG MÃ NGUỒN CỐT LÕI (CORE PIPELINE) ===
│   ├── __init__.py
│   ├── ingestion/                      # --- TẦNG 1: INGESTION & DOCUMENT AI ---
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── pdf_parser.py
│   │   ├── image_preprocessor.py
│   │   └── vision_ocr.py
│   ├── segmentation/                   # --- TẦNG 2: PHÂN ĐOẠN & SO KHỚP BẢN CHUẨN ---
│   │   ├── __init__.py
│   │   ├── clause_segmenter.py
│   │   ├── baseline_aligner.py
│   │   └── omission_detector.py
│   ├── retrieval/                      # --- TẦNG 3: HYBRID LEGAL RAG ENGINE ---
│   │   ├── __init__.py
│   │   ├── legal_kb.py
│   │   ├── sparse_bm25.py
│   │   ├── dense_retriever.py
│   │   └── reranker.py
│   ├── agents/                         # --- TẦNG 4: MULTI-AGENT & LEGAL NLI ENGINE ---
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── extractor_agent.py
│   │   ├── risk_analyzer_agent.py
│   │   ├── reflection_critic.py
│   │   └── proposal_agent.py
│   ├── hitl/                           # --- TẦNG 5: HUMAN-IN-THE-LOOP & XUẤT BẢN ---
│   │   ├── __init__.py
│   │   ├── hitl_controller.py
│   │   └── document_assembler.py
│   └── utils/                          # Tiện ích bổ trợ (Formatters, Loggers)
│       ├── __init__.py
│       └── formatting.py
│
└── tests/                              # === HỆ THỐNG KIỂM THỬ ĐỘC LẬP ===
    ├── test_ingestion.py
    ├── test_segmentation.py
    ├── test_legal_rag.py
    ├── test_nli_reasoning.py
    └── test_full_pipeline.py
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY

### 1. Cài đặt môi trường
```bash
python -m venv .venv
# Trên Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Cài đặt thư viện:
pip install -r requirements.txt
```

### 2. Thiết lập API Key
Tạo hoặc kiểm tra file `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Khởi chạy ứng dụng Web UI
```bash
streamlit run app.py
```

### 4. Chạy kiểm thử tự động
```bash
python -m unittest discover tests
```

### 5. Đánh giá Benchmark
```bash
python evaluate_benchmark.py
```

