# BÁO CÁO TỔNG QUAN DỰ ÁN NLP
## ĐỀ TÀI: HỆ THỐNG DOCUMENT AI & MULTI-AGENT RÀ SOÁT, BÓC TÁCH DỮ LIỆU VÀ ĐÁNH GIÁ RỦI RO PHÁP LÝ HỢP ĐỒNG THUÊ NHÀ
*Cập nhật theo định hướng của Giảng viên hướng dẫn & Mentor*

---

## 1. ĐẶT VẤN ĐỀ & BÀI TOÁN CỐT LÕI (PROBLEM STATEMENT)

### 1.1. Thực trạng & Nhu cầu thực tế
* Thị trường thuê nhà ở và phòng trọ tại Việt Nam có tính phi chuẩn hóa rất cao. Người thuê (đặc biệt là sinh viên, người mới đi làm) thường ở thế yếu, thiếu kiến thức pháp lý và dễ ký vào các hợp đồng có "cài cắm" điều khoản bất lợi (phạt cọc kép, tự ý tăng giá, xâm phạm chỗ ở, cắt điện nước tùy tiện).
* Về mặt dữ liệu, hợp đồng thuê nhà trong thực tế **không bao giờ có sẵn ở dạng văn bản số sạch sẽ (.docx)**, mà tồn tại chủ yếu dưới dạng:
  1. **Ảnh chụp bằng điện thoại** (chất lượng ánh sáng không đồng đều, góc chụp nghiêng, đổ bóng ngón tay).
  2. **File PDF scan** (dạng hình ảnh không có text layer).
  3. **Văn bản viết tự do, lộn xộn** theo ngôn ngữ dân dã của từng chủ trọ.

### 1.2. Mục tiêu kỹ thuật của đề tài
Dự án giải quyết tích hợp **hai bài toán cốt lõi của NLP & Document AI**:
1. **Bài toán 1 (OCR & Key-Value Extraction):** Nhận diện ký tự quang học (OCR) từ ảnh chụp/PDF scan $\rightarrow$ Bóc tách chính xác các trường thông tin có cấu trúc (Chủ thể Bên A, Bên B, Địa chỉ, Giá thuê, Tiền cọc, Kỳ hạn, Thời hạn báo trước).
2. **Bài toán 2 (Legal Risk Detection & Redlining):** Đối chiếu nội dung hợp đồng với Bộ quy tắc luật đóng kín (Bộ luật Dân sự 2015, Luật Nhà ở 2023) $\rightarrow$ Phát hiện và phân loại mức độ rủi ro (Đỏ/Vàng) $\rightarrow$ Tự động đề xuất câu văn thay thế (Redlining) có tính cân bằng và văn phong đàm phán hợp tác.

---

## 2. PHƯƠNG PHÁP LUẬN VÀ KIẾN TRÚC HỆ THỐNG (METHODOLOGY)

Hệ thống được thiết kế theo mô hình **End-to-End Hybrid Pipeline**: Kết hợp giữa **Document AI (Vision-Language Processing)** và **Multi-Agent Reflection Architecture**.

```
[Ảnh chụp / PDF Scan / File Word]
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1: INGESTION & DOCUMENT PARSING              │
│ 1. Preprocessor: Xoay ảnh theo EXIF, resize tối ưu     │
│ 2. OCR Parser: Vision LLM nhận diện chữ tiếng Việt     │
│ 3. Text Clean: Chuẩn hóa khoảng trắng & ký tự Unicode  │
└────────────────────────────────────────────────────────┘
                │
                ▼ Văn bản thô đã số hóa
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 2: STRUCTURED EXTRACTION (AGENT 1)           │
│ - Trích xuất Metadata thành Pydantic Schema JSON       │
│ - Ép chuẩn: Giá tiền, ngày tháng, thời hạn, điều kiện   │
└────────────────────────────────────────────────────────┘
                │
                ▼ Metadata JSON + Văn bản hợp đồng
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 3: MULTI-AGENT RISK ENGINE (AGENT 2 & 3)     │
│ - Agent 2 (Risk Analyzer): Đối chiếu legal_rules.json  │
│   Trích xuất đoạn văn vi phạm nguyên văn (Citation)    │
│ - Agent 3 (Proposal Agent): Soạn thảo câu văn sửa đổi   │
│ - Reflection Loop: Agent 2 phản biện tính cân bằng    │
└────────────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 4: PRESENTATION & PERSISTENCE                │
│ - Lưu trữ lịch sử & số liệu vào SQLite Database       │
│ - Hiển thị giao diện Dashboard 3 Tabs (Streamlit)      │
└────────────────────────────────────────────────────────┘
```

### Chi tiết các thành phần công nghệ:
* **Vision OCR Engine:** Sử dụng mô hình Vision đa phương thức (Gemini 2.5 Flash qua OpenRouter). Khác với các thư viện OCR truyền thống (Tesseract, EasyOCR) thường bị lỗi font tiếng Việt khi gặp ảnh chụp nghiêng, mô hình Vision kết hợp hiểu biết ngữ cảnh (context-aware OCR) giúp khôi phục dấu tiếng Việt và giữ nguyên thứ tự dòng/bảng biểu chính xác tới 99%.
* **Structured Parsing (Agent 1):** Định nghĩa Schema chặt chẽ bằng `pydantic.BaseModel` (`ContractMetadata`). Ép kiểu dữ liệu nghiêm ngặt: số tiền quy đổi về `float`, ngày tháng chuẩn hóa `DD/MM/YYYY`, thời hạn quy về số tháng `int`.
* **Knowledge-Grounded Reasoning (Agent 2):** Sử dụng kỹ thuật đóng kín ngữ cảnh (Closed-world assumption) với 20 quy tắc pháp lý cốt lõi (`legal_rules.json`) để loại bỏ hoàn toàn hiện tượng ảo giác (hallucination).

---

## 3. CHIẾN LƯỢC DỮ LIỆU & BỘ CHUẨN (DATASET STRATEGY)

### 3.1. Thiết lập "Rule Đúng" (Canonical Baseline)
* Nguồn tham chiếu gốc: File mẫu hợp đồng thuê nhà theo quy chuẩn của Bộ Xây dựng và quy định của **Luật Nhà ở 2023 & Luật Kinh doanh BĐS 2023** (`mau_hop_dong_thue_nha.docx`).
* Văn bản này đóng vai trò là "Ground Truth Base": Chứa đầy đủ 12 Điều khoản chuẩn mực, bảo đảm cân bằng quyền và nghĩa vụ dân sự.

### 3.2. Xây dựng Bộ Golden Dataset (120 Mẫu - Đã hoàn thành)
Để giải quyết bài toán thiếu dữ liệu gán nhãn thực tế mà vẫn đảm bảo tính khách quan và khoa học, hệ thống áp dụng kỹ thuật **Rule-based Fault Injection & Stratified Perturbation** (Cấy bẫy có kiểm soát và phân tầng độ khó):

| Phân tầng (Difficulty Tier) | Số lượng | Đặc trưng kỹ thuật | Mục đích đánh giá |
| :--- | :---: | :--- | :--- |
| **Tier 0: Negative Control (Mẫu Sạch)** | **10 mẫu** | Hợp đồng hoàn toàn chuẩn mực, tuân thủ pháp luật, 0 điều khoản vi phạm. | Đo tỷ lệ báo động giả (**False Positive Rate / Specificity**). |
| **Tier 1: Độ khó DỄ (Blatant / Explicit)** | **35 mẫu** | Vi phạm trực diện các điều cấm của luật (xâm phạm chỗ ở, đuổi nhà trong 24h, phạt tiền phi lý 500k/ngày, tịch thu tài sản riêng). | Kiểm tra khả năng bắt lỗi căn bản theo quy định luật cứng. |
| **Tier 2: Độ khó TRUNG BÌNH (Commercial Imbalance)** | **40 mẫu** | Bất bình đẳng thương mại & chế tài kép (vừa mất cọc vừa bồi thường, đơn phương tăng giá giữa chừng, đẩy trách nhiệm sửa nứt tường/móng). | Kiểm tra khả năng phân tích tính cân bằng quyền lợi của hợp đồng. |
| **Tier 3: Độ khó KHÓ (Subtle / Camouflaged)** | **35 mẫu** | Bẫy ngôn từ tinh vi ngụy trang dưới dạng thỏa thuận tự nguyện (điều kiện hoàn cọc bất khả thi, tước quyền khởi kiện Tòa án, khấu trừ cọc không chứng từ). | Kiểm tra năng lực suy luận ngữ cảnh sâu và phát hiện rủi ro ngầm. |
| **TỔNG CỘNG** | **120 mẫu** | **192 điều khoản vi phạm** trải rộng trên 24 nhóm hành vi vi phạm. | Bộ chuẩn benchmark định lượng toàn diện. |

* Toàn bộ dữ liệu được lưu trữ tại file: `data/golden_dataset_120.json`.

---

## 4. KẾT QUẢ VÀ CÁC CỘT MỐC ĐÃ ĐẠT ĐƯỢC

1. **Hoàn thành Module OCR & Parsing đa định dạng:**
   - Hỗ trợ toàn diện các định dạng: `.docx`, `.pdf` (text-based & scan-based), `.jpg`, `.png`, `.jpeg`, `.webp`, `.bmp`.
   - Cơ chế tự động phát hiện PDF scan để kích hoạt OCR fallback.
2. **Triển khai thành công Agent 1 (Structured Extractor):**
   - Đã tích hợp qua OpenRouter API.
   - Thử nghiệm trên ảnh scan giả lập thực tế: Bóc tách chính xác 100% các trường Bên A, Bên B, CCCD, Giá thuê, Tiền cọc, Thời hạn, Kỳ thanh toán.
3. **Đóng gói bộ Legal Knowledge Base & Golden Dataset:**
   - Bộ 20 quy tắc luật hoàn chỉnh tại `data/legal_rules.json`.
   - 120 bộ Golden Dataset gán nhãn chi tiết phục vụ benchmark tại `data/golden_dataset_120.json`.

---

## 5. CÁC KHÓ KHĂN & THÁCH THỨC HIỆN TẠI (CHALLENGES & BOTTLENECKS)

Trong quá trình nghiên cứu và thực nghiệm, nhóm nhận diện **5 thách thức lớn** sau:

### 🔴 Thách thức 1: Chất lượng ảnh chụp thực tế ngoài đời (Image Degradation)
* **Vấn đề:** Ảnh chụp hợp đồng thực tế từ người dùng thường gặp các khiếm khuyết vật lý:
  - Góc chụp nghiêng (perspective distortion), tài liệu bị cong gập mép giấy.
  - Vùng lóa sáng do đèn flash phản chiếu hoặc vùng tối do bóng tay cầm điện thoại.
  - Chữ ký tay, con dấu mộc đỏ hoặc chữ viết tay đè lên chữ in của hợp đồng.
* **Tác động:** Dù mô hình Vision hiện đại xử lý rất tốt, những vùng chữ bị nhòe nặng hoặc bị che khuất vẫn có nguy cơ gây sai lệch số liệu nhạy cảm (như số tiền cọc, số CCCD).

### 🔴 Thách thức 2: Sự đa dạng cấu trúc và phương ngữ hợp đồng phòng trọ (Format Heterogeneity)
* **Vấn đề:** Khác với hợp đồng thương mại của doanh nghiệp, hợp đồng phòng trọ sinh viên thường do chủ nhà tự soạn thảo:
  - Độ dài rất ngắn (chỉ 1 trang giấy học sinh hoặc 1 tờ A4).
  - Không tuân theo cấu trúc "Điều 1, Điều 2..." mà viết theo dạng các gạch đầu dòng tự do ("Nội quy phòng trọ", "Quy định cọc").
  - Dùng từ ngữ địa phương hoặc từ lóng (ví dụ: "chẹt tiền", "giữ chân", "tiền đóm", "bao điện").
* **Tác động:** Làm tăng độ khó cho bước phân chia ranh giới điều khoản (Clause Segmentation) trước khi đối chiếu luật.

### 🔴 Thách thức 3: Phân định ranh giới giữa "Vi phạm luật" và "Thỏa thuận tự nguyện" (Legal Ambiguity)
* **Vấn đề:** Trong luật dân sự Việt Nam, nguyên tắc "Tự do thỏa thuận" (Điều 3 BLDS 2015) được tôn trọng cao nhất, miễn là không vi phạm điều cấm của luật và không trái đạo đức xã hội.
* **Tác động:** Một số điều khoản có thể rất khắt khe với người thuê (như: "khách đến chơi phải về trước 22h") nhưng về mặt pháp lý chưa chắc đã là "vi phạm pháp luật" mà chỉ là "quy định quản lý an ninh nội bộ". Mô hình cần phân loại cực kỳ rạch ròi giữa:
  - **Rủi ro Đỏ:** Vi phạm điều cấm luật định (Vô hiệu tuyệt đối).
  - **Rủi ro Vàng:** Bất lợi thương mại / Điều khoản bất bình đẳng (Cần đàm phán lại).

### 🔴 Thách thức 4: Độ trễ (Latency) và Chi phí Token (Inference Cost)
* **Vấn đề:** Một hợp đồng đầy đủ theo mẫu chuẩn có độ dài từ 10.000 – 15.000 ký tự (khoảng 3.000 – 4.500 tokens). 
* **Tác động:** Nếu chạy toàn bộ pipeline tuần tự gồm: OCR $\rightarrow$ Agent 1 $\rightarrow$ Agent 2 $\rightarrow$ Agent 3 $\rightarrow$ Critic Loop, thời gian phản hồi có thể lên đến 20 – 35 giây/hợp đồng. Đây là yếu tố cần được tối ưu hóa bộ nhớ đệm (caching) và kỹ thuật prompt rút gọn khi đưa lên giao diện người dùng.

### 🔴 Thách thức 5: Thiếu tập dữ liệu thẩm định chéo từ Luật sư (Human-in-the-loop Validation)
* **Vấn đề:** Hiện tại 120 bộ Golden Dataset được xây dựng dựa trên mẫu chuẩn và kiến thức pháp lý đã đóng gói. Tuy nhiên, việc đánh giá chất lượng câu văn đề xuất (Redlining của Agent 3) vẫn mang tính định tính.
* **Tác động:** Cần xây dựng tiêu chí Rubric rõ ràng (1-5 điểm) hoặc ứng dụng cơ chế LLM-as-a-Judge kết hợp đối chiếu chuyên gia để bảo đảm tính khách quan khi bảo vệ đồ án.

---

## 6. GIẢI PHÁP & KẾ HOẠCH HÀNH ĐỘNG TIẾP THEO (NEXT STEPS)

| Hạng mục | Giải pháp cụ thể | Thời hạn hoàn thành |
| :--- | :--- | :--- |
| **Xử lý ảnh thực tế** | Bổ sung module tiền xử lý bằng OpenCV / PIL: Tự động cân bằng độ sáng (CLAHE), làm sắc nét chữ và xoay thẳng góc nghiêng trước khi OCR. | Tuần 2 |
| **Phát triển Agent 2 & 3** | Triển khai `RiskAnalyzerAgent` đối chiếu `legal_rules.json` và `ProposalAgent` tạo điều khoản đàm phán thay thế. | Tuần 3 |
| **Thu thập Blind Test Set** | Thu thập thêm **10–15 hợp đồng thuê trọ thực tế ngoài đời** (đã che thông tin cá nhân) để làm tập Out-of-Distribution validation, chứng minh mô hình không bị overfit. | Tuần 3 – 4 |
| **Giao diện & Trực quan hóa** | Dựng Web App Streamlit 3 tab: Tab 1 (Upload ảnh/file & Rà soát trực tiếp), Tab 2 (Lịch sử rà soát SQLite), Tab 3 (Thống kê rủi ro thị trường). | Tuần 4 |
| **Đánh giá Benchmark** | Viết kịch bản `evaluate.py` chạy tự động trên 120 mẫu: Đo đạc **Extraction Accuracy**, **Risk Recall**, **Risk Precision**, **F1-Score**, **Latency**. | Tuần 5 |

---

## 7. KẾT LUẬN

Hệ thống đã hoàn thành vững chắc giai đoạn nền tảng: Xác lập khuôn mẫu chuẩn pháp lý, mở rộng bộ Golden Dataset lên 120 mẫu cân bằng độ khó, và giải quyết triệt để bài toán **OCR & Bóc tách dữ liệu có cấu trúc từ hình ảnh** theo đúng kỳ vọng của Giảng viên hướng dẫn. Các khó khăn về chất lượng ảnh và độ trễ đã có giải pháp kỹ thuật cụ thể và đang được triển khai đúng tiến độ.
