import io
from typing import Union, Tuple, Any

try:
    from PIL import Image, ImageOps, ImageEnhance
except ImportError:
    Image = None
    ImageOps = None
    ImageEnhance = None

def preprocess_image(
    image_input: Union[str, bytes, Any],
    max_dimension: int = 1800,
    enhance_contrast: bool = True
) -> Any:
    """
    Tiền xử lý ảnh tài liệu/hợp đồng trước khi đưa vào Vision OCR:
    1. Chuẩn hóa xoay ảnh theo EXIF orientation.
    2. Chuyển đổi RGB / Grayscale.
    3. Tăng cường độ tương phản để làm rõ chữ mờ hoặc scan lem.
    4. Resize với bộ lọc Lanczos nếu kích thước vượt ngưỡng.
    """
    if Image is None:
        return image_input

    if isinstance(image_input, bytes):
        image = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, str):
        image = Image.open(image_input)
    elif hasattr(image_input, "size"):
        image = image_input
    else:
        raise ValueError("image_input must be a file path, bytes, or PIL Image object.")

    try:
        if ImageOps:
            image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    if hasattr(image, "mode") and image.mode != "RGB":
        image = image.convert("RGB")

    if enhance_contrast and ImageEnhance:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)

    w, h = image.size
    if max(w, h) > max_dimension:
        scale = max_dimension / float(max(w, h))
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = image.resize((new_w, new_h), resample=getattr(Image, "Resampling", Image).LANCZOS)

    return image

def image_to_base64_jpeg(image: Any, quality: int = 85) -> str:
    """Chuyển PIL Image, bytes, hoặc filepath sang Base64 string chuẩn để gửi API LLM."""
    import base64
    import os
    if image is None:
        return ""
    if hasattr(image, "save"):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    elif isinstance(image, bytes):
        return base64.b64encode(image).decode("utf-8")
    elif isinstance(image, str) and os.path.exists(image):
        with open(image, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    elif hasattr(image, "read"):
        data = image.read()
        return base64.b64encode(data).decode("utf-8")
    return ""
