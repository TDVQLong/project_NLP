import os
import re
from pathlib import Path
from typing import Union, Any
from .pdf_parser import extract_text_from_pdf
from .vision_ocr import extract_text_from_vision

def extract_text_from_docx(file_input: Union[str, Path, bytes, Any]) -> str:
    """Đọc file docx bằng python-docx (hỗ trợ file path, bytes, BytesIO và trích xuất cả table)."""
    try:
        from docx import Document
        import io
        if isinstance(file_input, bytes):
            doc = Document(io.BytesIO(file_input))
        elif hasattr(file_input, "read"):
            doc = Document(file_input)
        else:
            doc = Document(file_input)

        full_text = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                full_text.append(text)

        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip().replace("\n", " ") for cell in row.cells if cell.text.strip()]
                if row_text:
                    full_text.append(" | ".join(row_text))

        raw_content = "\n".join(full_text)
        cleaned_content = re.sub(r"[ \t]+", " ", raw_content)
        cleaned_content = re.sub(r"\n\s*\n+", "\n\n", cleaned_content)
        return cleaned_content.strip()
    except Exception as e:
        return f"[LỖI DOCX PARSER]: {str(e)}"

def route_document(file_input: Union[str, Path, bytes], filename: str = None) -> str:
    """
    Bộ định tuyến thông minh (Smart Router - Tầng 1):
    Phân tích định dạng tài liệu đầu vào và chuyển tiếp tới Parser tối ưu tương ứng:
    - PDF: pypdf (text) hoặc Vision OCR fallback
    - Word (.docx): docx parser (hỗ trợ cả bytes)
    - Hình ảnh (.png, .jpg, .jpeg, .webp): Vision AI OCR đa phương thức
    - Plaintext (.txt, .md): Đọc trực tiếp
    - Kiểm soát an toàn: Ngăn chặn dữ liệu nhị phân thô lọt vào pipeline xử lý NLP.
    """
    ext = ""
    if filename:
        ext = Path(filename).suffix.lower()
    elif isinstance(file_input, (str, Path)):
        ext = Path(file_input).suffix.lower()

    # 1. Hình ảnh
    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return extract_text_from_vision(file_input)

    # 2. PDF
    if ext == ".pdf":
        return extract_text_from_pdf(file_input)

    # 3. Microsoft Word
    if ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_input)

    # 4. Văn bản thuần
    if ext in [".txt", ".md"]:
        if isinstance(file_input, bytes):
            return file_input.decode("utf-8", errors="replace").strip()
        with open(file_input, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()

    # 5. Xử lý dữ liệu dạng bytes không rõ extension qua Magic Bytes
    if isinstance(file_input, bytes):
        # Ảnh PNG hoặc JPEG
        if file_input.startswith(b"\x89PNG\r\n\x1a\n") or file_input.startswith(b"\xff\xd8\xff"):
            return extract_text_from_vision(file_input)
        # PDF
        if file_input.startswith(b"%PDF"):
            return extract_text_from_pdf(file_input)
        # DOCX (ZIP archive)
        if file_input.startswith(b"PK\x03\x04"):
            return extract_text_from_docx(file_input)

        # Kiểm tra file nhị phân lạ (chứa null byte hoặc không phải UTF-8 hợp lệ)
        if b"\x00" in file_input[:1024]:
            return "[CẢNH BÁO ĐỊNH DẠNG]: Tệp tải lên là tệp nhị phân không xác định. Vui lòng tải lên tệp văn bản .docx, .pdf, ảnh chụp (.png/.jpg) hoặc .txt."

        decoded = file_input.decode("utf-8", errors="replace").strip()
        if decoded.count("\ufffd") > 20:
            return "[CẢNH BÁO ĐỊNH DẠNG]: Tệp tải lên chứa dữ liệu nhị phân không đọc được. Vui lòng cung cấp tệp hợp đồng đúng định dạng."
        return decoded

    elif isinstance(file_input, (str, Path)):
        path = Path(file_input)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()

    return ""

