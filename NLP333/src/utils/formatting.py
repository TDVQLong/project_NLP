import re
from datetime import datetime
from typing import Union, Optional

def format_vnd(amount: Union[int, float, str]) -> str:
    """Định dạng số tiền sang chuẩn hiển thị VNĐ (ví dụ: 4500000 -> 4.500.000 VNĐ)."""
    try:
        if isinstance(amount, str):
            clean_str = re.sub(r"[^\d\.]", "", amount)
            val = float(clean_str)
        else:
            val = float(amount)
        return f"{int(val):,}".replace(",", ".") + " VNĐ"
    except Exception:
        return str(amount)

def format_date(date_str: Optional[str]) -> str:
    """Chuẩn hóa hiển thị ngày tháng DD/MM/YYYY."""
    if not date_str:
        return "Chưa xác định"
    return str(date_str).strip()

def levenshtein_distance(seq1, seq2) -> int:
    """Tính khoảng cách Levenshtein (Dynamic Programming) giữa 2 chuỗi ký tự hoặc 2 danh sách từ."""
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = [[0] * size_y for _ in range(size_x)]
    for x in range(size_x):
        matrix[x][0] = x
    for y in range(size_y):
        matrix[0][y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x][y] = matrix[x - 1][y - 1]
            else:
                matrix[x][y] = min(
                    matrix[x - 1][y] + 1,      # Deletion
                    matrix[x][y - 1] + 1,      # Insertion
                    matrix[x - 1][y - 1] + 1   # Substitution
                )
    return matrix[size_x - 1][size_y - 1]

def compute_cer(reference: str, hypothesis: str) -> float:
    """
    Tính Character Error Rate (CER = (S + D + I) / N).
    Metric học thuật chuẩn quốc tế đo lường chất lượng OCR tiếng Việt (dấu thanh, dấu mũ, số tiền).
    """
    ref_chars = list(reference.strip())
    hyp_chars = list(hypothesis.strip())
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0
    distance = levenshtein_distance(ref_chars, hyp_chars)
    return round(distance / len(ref_chars), 4)

def compute_wer(reference: str, hypothesis: str) -> float:
    """
    Tính Word Error Rate (WER = (S + D + I) / N).
    Metric học thuật đo lường tỷ lệ lỗi nhận diện ở cấp độ từ vựng pháp lý.
    """
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    distance = levenshtein_distance(ref_words, hyp_words)
    return round(distance / len(ref_words), 4)

