import re
from pathlib import Path
from typing import Union, Any

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

def extract_text_from_pdf(file_path: Union[str, Path, Any]) -> str:
    """
    Trích xuất văn bản từ tệp PDF:
    - Nếu là PDF text layer chuẩn: trích xuất tức thì bằng pypdf (< 0.1s).
    - Nếu là PDF dạng scan: tự động chuyển hướng sang Vision OCR.
    """
    if PdfReader is None:
        return "[LỖI]: Chưa cài đặt thư viện 'pypdf'. Vui lòng chạy: pip install pypdf"

    try:
        import io
        if hasattr(file_path, "read"):
            reader = PdfReader(file_path)
        elif isinstance(file_path, bytes):
            reader = PdfReader(io.BytesIO(file_path))
        else:
            reader = PdfReader(str(file_path))
    except Exception as e:
        return f"[LỖI ĐỌC PDF]: {str(e)}"
    full_text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text.append(page_text.strip())

    combined_text = "\n\n".join(full_text).strip()

    # Kiểm tra fallback nếu PDF scan không có text layer
    if len(combined_text) < 50:
        from .vision_ocr import extract_text_from_vision
        ocr_texts = []
        for page in reader.pages:
            for img_file in page.images:
                page_ocr = extract_text_from_vision(img_file.data)
                if page_ocr and not page_ocr.startswith("["):
                    ocr_texts.append(page_ocr)
        if ocr_texts:
            combined_text = "\n\n".join(ocr_texts).strip()

    cleaned = re.sub(r"[ \t]+", " ", combined_text)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()
