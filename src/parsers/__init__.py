from pathlib import Path
from typing import Union

from .docx_parser import extract_text_from_docx
from .pdf_parser import extract_text_from_pdf
from .ocr_parser import extract_text_from_image, OCRParser

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

def parse_contract_file(file_path: Union[str, Path]) -> str:
    """
    Tự động nhận diện định dạng file đầu vào và chọn parser phù hợp:
    - .docx, .doc: Trích xuất đoạn văn bản và bảng biểu.
    - .pdf: Trích xuất text hoặc tự động fallback sang OCR nếu là PDF scan.
    - .jpg, .png, .jpeg, .webp: OCR nhận diện chữ tiếng Việt bằng Vision AI.
    - .txt: Đọc trực tiếp định dạng UTF-8.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in {".docx", ".doc"}:
        return extract_text_from_docx(file_path)
    elif suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in IMAGE_EXTENSIONS:
        return extract_text_from_image(file_path)
    elif suffix == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        supported = [".docx", ".pdf", ".txt"] + list(IMAGE_EXTENSIONS)
        raise ValueError(
            f"Định dạng file không được hỗ trợ: {suffix}. "
            f"Chỉ hỗ trợ: {', '.join(supported)}."
        )

__all__ = [
    "parse_contract_file",
    "extract_text_from_docx",
    "extract_text_from_pdf",
    "extract_text_from_image",
    "OCRParser"
]
