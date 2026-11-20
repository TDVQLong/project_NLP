import re
from typing import List, Dict

class ClauseSegmenter:
    """
    Tầng 2: Module phân đoạn văn bản hợp đồng thành danh sách các điều khoản độc lập (C1, C2... Cn).
    Hỗ trợ nhận diện các mẫu biểu thức quy phạm:
    - 'Điều 1.', 'Điều 1:', 'ĐIỀU 1 -', 'Điều 12'
    """
    CLAUSE_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:ĐIỀU|Điều)\s+(\d+)\s*[:\.\-–]?\s*([^\n]*)",
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def segment(self, contract_text: str) -> List[Dict[str, any]]:
        matches = list(self.CLAUSE_PATTERN.finditer(contract_text))
        clauses = []

        if not matches:
            paragraphs = [p.strip() for p in contract_text.split("\n\n") if len(p.strip()) > 30]
            for idx, p in enumerate(paragraphs, 1):
                clauses.append({
                    "clause_id": f"C_{idx:02d}",
                    "clause_number": idx,
                    "title": p[:40] + ("..." if len(p) > 40 else ""),
                    "raw_text": p,
                    "char_span": (0, len(p))
                })
            return clauses

        for i, match in enumerate(matches):
            clause_num = int(match.group(1))
            title = match.group(2).strip()
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(contract_text)
            
            raw_text = contract_text[start_pos:end_pos].strip()

            clauses.append({
                "clause_id": f"C_{clause_num:02d}",
                "clause_number": clause_num,
                "title": title or f"Điều {clause_num}",
                "raw_text": raw_text,
                "char_span": (start_pos, end_pos)
            })

        return clauses
