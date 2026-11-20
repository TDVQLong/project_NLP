import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

ContractType = Literal["rental", "employment"]

class LegalRule:
    """Đại diện cho một quy tắc luật trong Cơ sở tri thức pháp lý."""
    def __init__(self, data: Dict[str, Any]):
        self.rule_id: str = data.get("rule_id", "")
        self.rule_name: str = data.get("rule_name", "")
        self.category: str = data.get("category", "")
        self.risk_level: str = data.get("risk_level", "YELLOW")
        self.legal_basis: str = data.get("legal_basis", "")
        self.trigger_condition: str = data.get("trigger_condition", "")
        self.explanation: str = data.get("explanation", "")
        self.suggested_clause: str = data.get("suggested_clause", "")
        self.keywords: List[str] = data.get("keywords", [])
        self.statutory_citation: str = data.get("statutory_citation", "")
        self.reference_url: Optional[str] = data.get("reference_url")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category,
            "risk_level": self.risk_level,
            "legal_basis": self.legal_basis,
            "trigger_condition": self.trigger_condition,
            "explanation": self.explanation,
            "suggested_clause": self.suggested_clause,
            "keywords": self.keywords,
            "statutory_citation": self.statutory_citation,
            "reference_url": self.reference_url
        }

class LegalKnowledgeBase:
    """
    Tầng 3: Quản lý 42+ quy tắc luật đóng kín (Closed Legal KB).
    Hỗ trợ 2 lĩnh vực trọng điểm:
    - Thuê nhà (28 quy tắc Luật Nhà ở 2023 & BLDS 2015)
    - Lao động (14 quy tắc Bộ luật Lao động 2019)
    """
    def __init__(self, contract_type: ContractType = "rental", data_dir: Optional[str] = None):
        self.contract_type = contract_type
        # Tự động định vị thư mục data
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            current_file = Path(__file__).resolve()
            # Giả định cấu trúc NLP333/src/retrieval -> NLP333/data
            base_dir = current_file.parent.parent.parent
            self.data_dir = base_dir / "data"

        self.rules: List[LegalRule] = []
        self.rules_map: Dict[str, LegalRule] = {}
        self.load()

    def _get_file_path(self) -> Path:
        filename = "legal_rules_employment.json" if self.contract_type == "employment" else "legal_rules.json"
        target_path = self.data_dir / filename
        if not target_path.exists():
            # Thử tìm ở thư mục data cấp cha
            alt = Path("data") / filename
            if alt.exists():
                return alt
        return target_path

    def load(self) -> None:
        file_path = self._get_file_path()
        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file quy tắc pháp lý tại: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.rules = [LegalRule(r) for r in data.get("rules", [])]
        self.rules_map = {r.rule_id: r for r in self.rules}

    def switch_domain(self, contract_type: ContractType) -> None:
        self.contract_type = contract_type
        self.load()

    def get_rule(self, rule_id: str) -> Optional[LegalRule]:
        return self.rules_map.get(rule_id)

    def get_all_rules(self) -> List[LegalRule]:
        return self.rules

