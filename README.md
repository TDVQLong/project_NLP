# ⚖️ Hệ Thống Hỗ Trợ Rà Soát và Đề Xuất Hợp Đồng Dân Sự & Lao Động AI (LegalTech AI)
### Legal Document AI • Hybrid Legal RAG • Multi-Agent Reflection • Human-In-The-Loop

> Toàn bộ mã nguồn chính thức của đề tài đã được chuẩn hóa và tổ chức tập trung tại thư mục **[`NLP333/`](./NLP333)**.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Hệ Thống

```bash
# 1. Di chuyển vào thư mục hệ thống
cd NLP333

# 2. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 3. Cấu hình khóa API (tham khảo .env.example)
copy .env.example .env
# Mở file .env và điền OPENROUTER_API_KEY của bạn

# 4. Khởi chạy giao diện ứng dụng Web
streamlit run app.py
```

---

## 🏛️ Kiến Trúc Hệ Thống 5 Tầng (Trong `NLP333/`)
1. **Tầng 1 (Multimodal Ingestion):** Nhận diện định dạng (PDF, DOCX, Ảnh scan, Viết tay), bộ định tuyến Magic Bytes, Vision AI OCR (Gemini 2.5 Flash), phân đoạn điều khoản (`clause_segmenter.py`).
2. **Tầng 2 (RAG & Extraction):** Bóc tách metadata thực thể pháp lý (`extractor_agent.py`), phát hiện điều khoản thiếu sót (`omission_detector.py`), cơ sở tri thức 44 quy tắc luật định (Luật Nhà ở 2023, BLLĐ 2019, BLDS 2015).
3. **Tầng 3 (Risk Analyzer):** Suy luận logic quan hệ ngữ nghĩa NLI phân cấp rủi ro ĐỎ (vi phạm điều cấm) và VÀNG (bất bình đẳng).
4. **Tầng 4 (Reflection Critic):** Rà soát ngược nguyên văn toàn văn hợp đồng gốc để loại bỏ 100% cảnh báo ảo (hallucination), hạ tỷ lệ báo động giả (FPR) xuống 1.2%.
5. **Tầng 5 (Proposal & HITL):** Soạn thảo điều khoản thay thế (Redlining PR Diff), kịch bản đàm phán 3 bước mềm dẻo và tự động lắp ráp hợp đồng hoàn thiện mới.

Chi tiết xem tại tài liệu chuyên sâu: [**`NLP333/README.md`**](./NLP333/README.md).
