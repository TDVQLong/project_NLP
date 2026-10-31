from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ContractMetadata(BaseModel):
    """Schema cấu trúc dữ liệu metadata của hợp đồng thuê nhà do Agent 1 trích xuất."""
    lessor_name: Optional[str] = Field(
        None, 
        description="Họ tên bên cho thuê (Bên A / Chủ nhà / Bên đại diện)"
    )
    lessee_name: Optional[str] = Field(
        None, 
        description="Họ tên bên thuê (Bên B / Khách thuê)"
    )
    property_address: Optional[str] = Field(
        None, 
        description="Địa chỉ phòng trọ, căn hộ hoặc nhà cho thuê"
    )
    rent_price: float = Field(
        0.0, 
        description="Giá thuê hàng tháng tính bằng số tiền VNĐ (ví dụ: 4500000)"
    )
    deposit_amount: float = Field(
        0.0, 
        description="Số tiền đặt cọc tính bằng số tiền VNĐ (ví dụ: 4500000)"
    )
    lease_term_months: int = Field(
        12, 
        description="Thời hạn hợp đồng tính theo số tháng (ví dụ: 6, 12, 24)"
    )
    start_date: Optional[str] = Field(
        None, 
        description="Ngày bắt đầu có hiệu lực của hợp đồng (ví dụ: '01/10/2026')"
    )
    end_date: Optional[str] = Field(
        None, 
        description="Ngày kết thúc hợp đồng (ví dụ: '01/10/2027')"
    )
    payment_cycle: str = Field(
        "Hàng tháng", 
        description="Chu kỳ thanh toán (ví dụ: 'Hàng tháng', '3 tháng/lần', 'Thanh toán vào ngày 5 hàng tháng')"
    )
    payment_deadline_day: Optional[int] = Field(
        None, 
        description="Ngày thanh toán định kỳ trong tháng nếu có (ví dụ: 5)"
    )
    notice_period_days: int = Field(
        30, 
        description="Thời hạn báo trước bắt buộc khi muốn đơn phương chấm dứt hợp đồng (tính bằng số ngày)"
    )
    electricity_price: Optional[str] = Field(
        None, 
        description="Đơn giá tiền điện ghi trong hợp đồng (ví dụ: '3.800 đ/kWh' hoặc 'theo hóa đơn nhà nước')"
    )
    water_price: Optional[str] = Field(
        None, 
        description="Đơn giá tiền nước sinh hoạt (ví dụ: '100.000 đ/người/tháng' hoặc '30.000 đ/m3')"
    )
    termination_clause_summary: Optional[str] = Field(
        None, 
        description="Tóm tắt ngắn gọn (1-2 câu) quy định về điều kiện trả phòng và xử lý cọc"
    )

class RiskItem(BaseModel):
    """Schema cho một rủi ro pháp lý/thương mại do Agent 2 phát hiện."""
    rule_id: str = Field(
        ..., 
        description="Mã quy tắc vi phạm theo legal_rules.json (ví dụ: 'RULE_UNANNOUNCED_ENTRY')"
    )
    rule_name: str = Field(
        ..., 
        description="Tên quy tắc rủi ro vi phạm"
    )
    category: str = Field(
        ..., 
        description="Nhóm quy tắc (ví dụ: 'Quyền riêng tư & Sử dụng', 'Đặt cọc & Hoàn cọc', 'Phạt vi phạm')"
    )
    risk_level: str = Field(
        ..., 
        description="Mức độ rủi ro: 'RED' (Rủi ro cao - vi phạm luật cấm) hoặc 'YELLOW' (Rủi ro trung bình - bất lợi thương mại)"
    )
    original_clause: str = Field(
        ..., 
        description="Đoạn văn trích dẫn NGUYÊN VĂN từ trong văn bản hợp đồng vi phạm quy tắc này (bắt buộc đúng nguyên văn)"
    )
    related_article: Optional[str] = Field(
        None, 
        description="Tên hoặc số thứ tự điều khoản chứa đoạn vi phạm này (ví dụ: 'Điều 6', 'Điều 10')"
    )
    legal_basis: str = Field(
        ..., 
        description="Căn cứ pháp lý cụ thể (ví dụ: 'Điều 22 Hiến pháp 2013 & Điều 10 Luật Nhà ở 2023')"
    )
    explanation: str = Field(
        ..., 
        description="Giải thích chi tiết tại sao điều khoản này gây bất lợi, vi phạm pháp luật hoặc tiềm ẩn nguy cơ cho người thuê"
    )
    suggested_action: Optional[str] = Field(
        None, 
        description="Khuyến nghị xử lý nhanh dành cho người thuê (ví dụ: 'Yêu cầu xóa bỏ điều khoản', 'Đàm phán sửa thời hạn thành 30 ngày')"
    )
    statutory_citation: Optional[str] = Field(
        None, 
        description="Trích dẫn điều khoản luật định chính thức (ví dụ: 'Khoản 2 Điều 328 BLDS 2015')"
    )
    reference_url: Optional[str] = Field(
        None, 
        description="Đường link URL chính thức tra cứu trên Cơ sở dữ liệu quốc gia về văn bản pháp luật vbpl.vn"
    )

class RiskAnalysisResult(BaseModel):
    """Schema kết quả phân tích tổng thể của Agent 2 (Risk Analyzer)."""
    is_safe: bool = Field(
        ..., 
        description="True nếu hợp đồng sạch, không có điều khoản vi phạm Đỏ hoặc Vàng; False nếu có rủi ro"
    )
    total_risks: int = Field(
        ..., 
        description="Tổng số rủi ro phát hiện được"
    )
    red_risks_count: int = Field(
        ..., 
        description="Số lượng rủi ro mức ĐỎ (vi phạm trực tiếp điều cấm của luật)"
    )
    yellow_risks_count: int = Field(
        ..., 
        description="Số lượng rủi ro mức VÀNG (bất bình đẳng thương mại, điều khoản mập mờ)"
    )
    risks: List[RiskItem] = Field(
        default_factory=list, 
        description="Danh sách chi tiết từng rủi ro được phát hiện"
    )
    overall_assessment: str = Field(
        ..., 
        description="Nhận định và đánh giá pháp lý tổng quan về hợp đồng này"
    )

# ============================================================
# CÁC SCHEMA MỚI DÀNH CHO AGENT 3 (PROPOSAL & HITL)
# ============================================================

class RedlineProposal(BaseModel):
    """Schema một đề xuất sửa đổi điều khoản kèm Citation và cơ chế duyệt Human-in-the-Loop."""
    proposal_id: str = Field(
        ..., 
        description="Mã định danh đề xuất (ví dụ: 'PROP_001')"
    )
    rule_id: str = Field(
        ..., 
        description="Mã rủi ro tương ứng từ Agent 2"
    )
    rule_name: str = Field(
        ..., 
        description="Tên rủi ro vi phạm"
    )
    risk_level: str = Field(
        ..., 
        description="Mức độ rủi ro: RED / YELLOW"
    )
    related_article: Optional[str] = Field(
        None, 
        description="Tên điều khoản trong hợp đồng (ví dụ: 'Điều 6', 'Điều 10')"
    )
    original_clause: str = Field(
        ..., 
        description="Câu văn gốc vi phạm trong hợp đồng của chủ nhà"
    )
    proposed_clause: str = Field(
        ..., 
        description="Câu văn đề xuất thay thế do Agent 3 soạn thảo (chuẩn mực, bảo vệ quyền lợi và hài hòa)"
    )
    statutory_citation: str = Field(
        ..., 
        description="Trích dẫn điều khoản luật làm căn cứ vững chắc cho câu sửa đổi (Citation)"
    )
    reference_url: Optional[str] = Field(
        None, 
        description="Đường link dẫn đến văn bản gốc trên vbpl.vn"
    )
    negotiation_script: str = Field(
        ..., 
        description="Lời thoại mẫu khéo léo để người thuê nhắn tin hoặc trao đổi trực tiếp với chủ nhà"
    )
    compromise_option: Optional[str] = Field(
        None, 
        description="Phương án nhượng bộ dự phòng bậc 2 nếu chủ nhà kiên quyết từ chối phương án 1"
    )
    
    # CƠ CHẾ HUMAN-IN-THE-LOOP (HITL)
    hitl_status: str = Field(
        "PENDING_REVIEW", 
        description="Trạng thái phê duyệt của con người: 'PENDING_REVIEW' (Chờ duyệt), 'APPROVED' (Đồng ý), 'MODIFIED' (Đã chỉnh sửa lại), 'REJECTED' (Bỏ qua)"
    )
    user_custom_clause: Optional[str] = Field(
        None, 
        description="Nội dung điều khoản do người dùng tự gõ/chỉnh sửa lại theo ý mình (khi status là MODIFIED)"
    )
    user_notes: Optional[str] = Field(
        None, 
        description="Ghi chú cá nhân của người thuê khi xem xét điều khoản này"
    )
    final_clause: Optional[str] = Field(
        None, 
        description="Câu văn chốt cuối cùng sẽ được đưa vào bản hợp đồng hoàn thiện sau khi con người duyệt"
    )

class ContractReviewPackage(BaseModel):
    """Gói hồ sơ đánh giá và đề xuất toàn diện của hệ thống sau khi Agent 3 hoàn thành."""
    executive_summary: str = Field(
        ..., 
        description="Tóm tắt điều hành ngắn gọn về tình trạng pháp lý của hợp đồng"
    )
    verdict: str = Field(
        ..., 
        description="Phán quyết cuối cùng: 'AN TOÀN - CÓ THỂ KÝ', 'CẦN ĐÀM PHÁN SỬA ĐỔI', 'RỦI RO ĐẶC BIỆT CAO - KHUYẾN CÁO KHÔNG KÝ'"
    )
    safety_score: float = Field(
        ..., 
        description="Thang điểm an toàn hợp đồng từ 1.0 (cực kỳ nguy hiểm) đến 10.0 (hoàn toàn an toàn chuẩn mực)"
    )
    total_risks_found: int = Field(
        ..., 
        description="Tổng số điều khoản rủi ro phát hiện được"
    )
    proposals: List[RedlineProposal] = Field(
        default_factory=list, 
        description="Danh sách các đề xuất sửa đổi và kịch bản đàm phán"
    )
    is_hitl_completed: bool = Field(
        False, 
        description="Đánh dấu người dùng đã hoàn thành quy trình duyệt/sửa đổi Human-in-the-Loop hay chưa"
    )
    final_contract_text: Optional[str] = Field(
        None, 
        description="Toàn văn hợp đồng hoàn thiện sau khi đã áp dụng các điều khoản được con người phê duyệt"
    )
