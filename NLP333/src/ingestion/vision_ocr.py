import os
import json
import base64
from pathlib import Path
from typing import Union, Any
from .image_preprocessor import preprocess_image, image_to_base64_jpeg

# Tự động nạp .env nếu biến môi trường chưa có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("GROQ_API_KEY"):
    for env_candidate in [Path(".env"), Path(__file__).resolve().parent.parent.parent / ".env"]:
        if env_candidate.exists():
            try:
                for line in env_candidate.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        os.environ.setdefault(k.strip(), v.strip())
            except Exception:
                pass

def extract_text_from_vision(image_input: Union[str, bytes, Any], api_key: str = None) -> str:
    """
    Sử dụng Vision AI Model (OpenRouter Gemini 2.5 Flash / Groq Vision / OpenAI) để nhận dạng văn bản tiếng Việt từ ảnh chụp hợp đồng.
    """
    # 1. Tiền xử lý ảnh (xoay, tăng tương phản, resize Lanczos) và chuyển base64 JPEG
    processed_img = preprocess_image(image_input)
    b64_img = image_to_base64_jpeg(processed_img)
    if not b64_img:
        return "[LỖI VISION OCR]: Không thể mã hóa hình ảnh hợp đồng."

    # 2. Kiểm tra các API Key theo thứ tự ưu tiên
    openrouter_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    system_prompt = (
        "Bạn là chuyên gia số hóa và OCR hợp đồng, văn bản pháp lý tiếng Việt (Document AI). "
        "Nhiệm vụ của bạn là nhận dạng và trích xuất nguyên văn, chính xác 100% toàn bộ nội dung văn bản trong ảnh "
        "(bao gồm cả chữ in, chữ viết tay, số tiền, ngày tháng, thông tin các bên, số CCCD và tất cả các điều khoản). "
        "Giữ nguyên định dạng tiêu đề và các điều khoản (Điều 1, Điều 2...). Tuyệt đối không tóm tắt hay lược bỏ."
    )
    user_prompt = "Hãy trích xuất chính xác 100% toàn bộ văn bản tiếng Việt trong ảnh chụp hợp đồng này."

    # Ưu tiên 1: OpenRouter (sử dụng mô hình đa phương thức Gemini Flash đã cấu hình sẵn trong .env)
    if openrouter_key:
        base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")

        # Cách 1: Thử qua thư viện openai
        try:
            from openai import OpenAI
            client = OpenAI(base_url=base_url, api_key=openrouter_key)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                            }
                        ]
                    }
                ],
                temperature=0.0
            )
            extracted = response.choices[0].message.content.strip()
            if extracted:
                return extracted
        except Exception as e_openai:
            # Cách 2: Fallback trực tiếp bằng urllib chuẩn của Python
            try:
                import urllib.request
                req_payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                                }
                            ]
                        }
                    ],
                    "temperature": 0.0
                }
                req = urllib.request.Request(
                    f"{base_url.rstrip('/')}/chat/completions",
                    data=json.dumps(req_payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    extracted = resp_data["choices"][0]["message"]["content"].strip()
                    if extracted:
                        return extracted
            except Exception as e_urllib:
                print(f"⚠️ [Vision OCR - OpenRouter Error]: {e_openai} | {e_urllib}. Đang thử kênh fallback...")

    # Ưu tiên 2: Groq Vision (llama-3.2-11b-vision-preview)
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                            }
                        ]
                    }
                ],
                temperature=0.0
            )
            extracted = response.choices[0].message.content.strip()
            if extracted:
                return extracted
        except Exception as e:
            print(f"⚠️ [Vision OCR - Groq Error]: {e}")

    # Ưu tiên 3: OpenAI Vision tiêu chuẩn
    if openai_key and not openrouter_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                            }
                        ]
                    }
                ],
                temperature=0.0
            )
            extracted = response.choices[0].message.content.strip()
            if extracted:
                return extracted
        except Exception as e:
            print(f"⚠️ [Vision OCR - OpenAI Error]: {e}")

    # Nếu không có key nào được cấu hình
    return (
        "[CẢNH BÁO OCR]: Không tìm thấy OPENROUTER_API_KEY hoặc GROQ_API_KEY trong file .env. "
        "Vui lòng kiểm tra lại cấu hình key để kích hoạt tính năng Vision OCR trích xuất ảnh chụp hợp đồng."
    )
