import os
import io
import re
import base64
from pathlib import Path
from typing import Union, List, Optional
from PIL import Image, ImageOps
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OCR_SYSTEM_PROMPT = """Bạn là một Hệ thống OCR & Document Parsing chuyên dụng cho văn bản pháp lý, hợp đồng thuê nhà tại Việt Nam.

Nhiệm vụ của bạn:
1. Đọc và phiên âm (transcribe) chính xác toàn bộ văn bản trong hình ảnh sang tiếng Việt có dấu chuẩn Unicode.
2. Giữ nguyên cấu trúc văn bản: các tiêu đề (Quốc hiệu, Tiêu đề Hợp đồng, Tên Điều khoản như 'Điều 1.', 'Điều 2.'), thụt lề, danh sách gạch đầu dòng.
3. Đặc biệt bảo toàn chính xác 100% các dữ liệu số: Số CCCD, số tiền thuê, tiền cọc, ngày tháng năm, số nhà, diện tích.
4. Trả về TRỰC TIẾP nội dung văn bản được OCR, KHÔNG thêm các câu chào đầu như 'Dưới đây là...', 'Đây là nội dung ảnh...' hay lời kết.
"""

class OCRParser:
    """Module OCR chuyên dụng xử lý ảnh chụp và tài liệu scan hợp đồng."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = (
            api_key 
            or os.getenv("OPENROUTER_API_KEY") 
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
        self.base_url = (
            base_url 
            or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        )
        self.model_name = (
            model_name 
            or os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        )

        if self.api_key:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        else:
            self.client = None

    def preprocess_image(self, image_input: Union[str, Path, bytes, Image.Image]) -> tuple[str, str]:
        """
        Tiền xử lý ảnh:
        - Tự động xoay thẳng theo EXIF (ảnh chụp điện thoại).
        - Chuyển sang định dạng RGB.
        - Resize tối ưu nếu ảnh quá lớn (giữ max kích thước 2048px).
        - Trả về (base64_string, mime_type).
        """
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise ValueError(f"Định dạng đầu vào không hợp lệ: {type(image_input)}")

        # Tự động xoay theo EXIF tag
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Đổi sang RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Tối ưu kích thước (nếu cạnh lớn nhất > 2048px thì resize)
        max_size = 2048
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Lưu vào buffer dưới dạng JPEG chất lượng cao
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=90)
        base64_encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return base64_encoded, "image/jpeg"

    def extract_text(self, image_input: Union[str, Path, bytes, Image.Image]) -> str:
        """
        Thực hiện OCR nhận diện chữ từ ảnh chụp hợp đồng.
        """
        if not self.client:
            raise ValueError("Chưa cấu hình API Key trong file .env để thực hiện OCR Vision.")

        base64_str, mime_type = self.preprocess_image(image_input)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": OCR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Hãy nhận diện và chép lại chính xác toàn bộ chữ trong văn bản hợp đồng này."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_str}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0
        )

        extracted_text = response.choices[0].message.content.strip()

        # Làm sạch các lời dẫn đầu thường gặp
        extracted_text = re.sub(
            r"^(Dưới đây là|Đây là|Nội dung|Sau đây là)[^\n]*:\s*\n*", 
            "", 
            extracted_text, 
            flags=re.IGNORECASE
        )
        return extracted_text.strip()

def extract_text_from_image(image_path: Union[str, Path]) -> str:
    """Hàm tiện ích nhanh để gọi OCR parser từ file ảnh."""
    parser = OCRParser()
    return parser.extract_text(image_path)
