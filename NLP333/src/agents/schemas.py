from enum import Enum
from typing import Optional, List, Dict, Any, Literal

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Graceful fallback cho môi trường chưa cài pydantic
    class BaseModel:
        def __init__(self, **kwargs):
            # Khởi tạo mặc định từ class annotations nếu có
            if hasattr(self, "__annotations__"):
                for k in self.__annotations__:
                    setattr(self, k, getattr(self.__class__, k, None))
            for k, v in kwargs.items():
                setattr(self, k, v)

        @classmethod
        def model_validate_json(cls, json_str: str):
            import json
            data = json.loads(json_str)
            return cls(**data)

        @classmethod
        def model_json_schema(cls) -> Dict[str, Any]:
            return {"title": cls.__name__, "type": "object"}

        def model_dump(self) -> Dict[str, Any]:
            return self.__dict__

    def Field(default=None, default_factory=None, description=""):
        if default_factory is not None:
            return default_factory()
        return default

class ReviewPerspective(str, Enum):
    PARTY_B = "party_b"   # Người thuê nhà / Người lao động (Bên yếu thế)
    PARTY_A = "party_a"   # Bên cho thuê / Người sử dụng lao động
    NEUTRAL = "neutral"   # Trọng tài / Trung lập khách quan

class ContractType(str, Enum):
    RENTAL = "rental"
    EMPLOYMENT = "employment"

class ContractMetadata(BaseModel):
    """Schema cấu trúc dữ liệu metadata của hợp đồng thuê nhà do Extractor Agent trích xuất."""
    lessor_name: Optional[str] = Field(None, description="Họ tên bên cho thuê")
    lessee_name: Optional[str] = Field(None, description="Họ tên bên thuê")
    property_address: Optional[str] = Field(None, description="Địa chỉ phòng trọ, căn hộ")
    rent_price: float = Field(0.0, description="Giá thuê hàng tháng VNĐ")
    deposit_amount: float = Field(0.0, description="Số tiền đặt cọc VNĐ")
    lease_term_months: int = Field(12, description="Thời hạn hợp đồng theo tháng")
    start_date: Optional[str] = Field(None, description="Ngày bắt đầu")
    end_date: Optional[str] = Field(None, description="Ngày kết thúc")
    payment_cycle: str = Field("Hàng tháng", description="Chu kỳ thanh toán")
    payment_deadline_day: Optional[int] = Field(None, description="Ngày thanh toán")
    notice_period_days: int = Field(30, description="Thời hạn báo trước khi chấm dứt")
    electricity_price: Optional[str] = Field(None, description="Đơn giá tiền điện")
    water_price: Optional[str] = Field(None, description="Đơn giá nước sinh hoạt")
    termination_clause_summary: Optional[str] = Field(None, description="Tóm tắt về cọc và trả phòng")

class EmploymentMetadata(BaseModel):
    """Schema cấu trúc dữ liệu metadata của hợp đồng lao động do Extractor Agent trích xuất."""
    employer_name: Optional[str] = Field(None, description="Tên công ty / Bên A")
    employee_name: Optional[str] = Field(None, description="Họ tên người lao động / Bên B")
    job_title: Optional[str] = Field(None, description="Vị trí đảm nhận")
    work_location: Optional[str] = Field(None, description="Địa điểm làm việc")
    contract_type_str: Optional[str] = Field("Hợp đồng xác định thời hạn", description="Phân loại hợp đồng")
    contract_term_months: Optional[int] = Field(12, description="Thời hạn hợp đồng")
    official_salary: float = Field(0.0, description="Mức lương chính thức VNĐ")
    probation_salary: Optional[float] = Field(None, description="Mức lương thử việc")
    probation_duration_days: Optional[int] = Field(None, description="Thời gian thử việc ngày")
    working_hours: Optional[str] = Field("8 giờ/ngày, 40-48 giờ/tuần", description="Thời giờ làm việc")
    notice_period_days: int = Field(30, description="Thời hạn báo trước")
    social_insurance_status: Optional[str] = Field(None, description="Quy định BHXH, BHYT")
    termination_clause_summary: Optional[str] = Field(None, description="Tóm tắt chấm dứt")

class RiskItem(BaseModel):
    """Schema cho một rủi ro pháp lý/thương mại do Risk Analyzer Agent phát hiện."""
    rule_id: str = Field(..., description="Mã quy tắc vi phạm theo KB")
    rule_name: str = Field(..., description="Tên quy tắc rủi ro vi phạm")
    category: str = Field(..., description="Nhóm quy tắc")
    risk_level: str = Field(..., description="Mức độ rủi ro: 'RED' hoặc 'YELLOW'")
    original_clause: str = Field(..., description="Đoạn văn trích dẫn NGUYÊN VĂN từ trong hợp đồng")
    related_article: Optional[str] = Field(None, description="Tên hoặc số thứ tự điều khoản")
    legal_basis: str = Field(..., description="Căn cứ pháp lý cụ thể")
    explanation: str = Field(..., description="Giải thích chi tiết")
    suggested_action: Optional[str] = Field(None, description="Khuyến nghị xử lý nhanh")
    statutory_citation: Optional[str] = Field(None, description="Trích dẫn điều khoản luật")
    reference_url: Optional[str] = Field(None, description="Đường link URL vbpl.vn")
    nli_relation: Optional[str] = Field("CONTRADICTION", description="Quan hệ NLI")

class RiskAnalysisResult(BaseModel):
    """Schema kết quả phân tích rủi ro của toàn bộ hợp đồng."""
    is_safe: bool = Field(..., description="True nếu an toàn; False nếu có rủi ro")
    total_risks: int = Field(..., description="Tổng số rủi ro")
    red_risks_count: int = Field(..., description="Số lượng rủi ro mức ĐỎ")
    yellow_risks_count: int = Field(..., description="Số lượng rủi ro mức VÀNG")
    risks: List[RiskItem] = Field(default_factory=list, description="Danh sách rủi ro")
    overall_assessment: str = Field(..., description="Nhận định pháp lý tổng quan")

class RedlineProposal(BaseModel):
    """Schema đề xuất sửa đổi điều khoản kèm Citation và HITL state."""
    proposal_id: str = Field(..., description="Mã đề xuất")
    rule_id: str = Field(..., description="Mã rủi ro")
    rule_name: str = Field(..., description="Tên rủi ro")
    risk_level: str = Field(..., description="RED / YELLOW")
    related_article: Optional[str] = Field(None, description="Tên điều khoản")
    original_clause: str = Field(..., description="Câu văn gốc vi phạm")
    proposed_clause: str = Field(..., description="Câu văn đề xuất thay thế")
    statutory_citation: str = Field(..., description="Trích dẫn điều khoản luật")
    reference_url: Optional[str] = Field(None, description="Link tra cứu")
    negotiation_script: str = Field(..., description="Lời thoại mẫu đàm phán")
    compromise_option: Optional[str] = Field(None, description="Phương án nhượng bộ")
    
    hitl_status: str = Field("PENDING", description="'PENDING', 'PENDING_REVIEW', 'APPROVED', 'MODIFIED', 'REJECTED'")
    user_custom_clause: Optional[str] = Field(None, description="Nội dung điều khoản do người dùng tự gõ")
    user_notes: Optional[str] = Field(None, description="Ghi chú")
    final_clause: Optional[str] = Field(None, description="Câu văn chốt cuối")

class ContractReviewPackage(BaseModel):
    """Gói hồ sơ đánh giá và đề xuất toàn diện của hệ thống."""
    executive_summary: str = Field(..., description="Tóm tắt điều hành")
    verdict: str = Field(..., description="Phán quyết")
    safety_score: float = Field(..., description="Thang điểm an toàn từ 1.0 đến 10.0")
    total_risks_found: int = Field(..., description="Tổng số điều khoản rủi ro")
    proposals: List[RedlineProposal] = Field(default_factory=list, description="Danh sách đề xuất Redline")
    is_hitl_completed: bool = Field(False, description="Đã hoàn thành duyệt HITL")
    final_contract_text: Optional[str] = Field(None, description="Toàn văn hợp đồng hoàn thiện")
