import re
from pathlib import Path
from docx import Document

def extract_text_from_docx(file_path: str | Path) -> str:
    """
    Trích xuất toàn bộ văn bản từ file Word (.docx) bao gồm cả đoạn văn và bảng biểu.
    Chuẩn hóa khoảng trắng và định dạng UTF-8.
    """
    doc = Document(file_path)
    full_text = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            full_text.append(text)

    # Đọc thêm dữ liệu trong các bảng biểu (nếu hợp đồng lập dạng bảng)
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip().replace("\n", " ") for cell in row.cells if cell.text.strip()]
            if row_text:
                full_text.append(" | ".join(row_text))

    raw_content = "\n".join(full_text)
    # Chuẩn hóa khoảng trắng thừa
    cleaned_content = re.sub(r"[ \t]+", " ", raw_content)
    cleaned_content = re.sub(r"\n\s*\n+", "\n\n", cleaned_content)
    return cleaned_content.strip()
