import re
from pathlib import Path
from typing import Union
from pypdf import PdfReader

def extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    """
    Trích xuất văn bản từ file PDF:
    - Nếu là PDF text-based thông thường: trích xuất nhanh bằng pypdf.
    - Nếu là PDF dạng scan (không có text layer): tự động chuyển sang OCR ảnh từng trang.
    """
    reader = PdfReader(str(file_path))
    full_text = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            full_text.append(page_text.strip())

    combined_text = "\n\n".join(full_text).strip()

    # Kiểm tra nếu PDF scan (gần như không có text layer)
    if len(combined_text) < 50:
        # Fallback sang OCR từng trang scan
        from .ocr_parser import extract_text_from_image
        ocr_texts = []
        for page_idx, page in enumerate(reader.pages):
            for img_file in page.images:
                # img_file.data chứa raw bytes của ảnh scan
                page_ocr = extract_text_from_image(img_file.data)
                if page_ocr:
                    ocr_texts.append(page_ocr)
        if ocr_texts:
            combined_text = "\n\n".join(ocr_texts).strip()

    # Chuẩn hóa ký tự khoảng trắng thừa
    cleaned_content = re.sub(r"[ \t]+", " ", combined_text)
    cleaned_content = re.sub(r"\n\s*\n+", "\n\n", cleaned_content)
    return cleaned_content.strip()
