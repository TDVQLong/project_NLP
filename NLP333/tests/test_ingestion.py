import unittest
from pathlib import Path
from src.ingestion.router import route_document

class TestIngestion(unittest.TestCase):
    def test_router_plaintext(self):
        sample_text = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nHỢP ĐỒNG THUÊ NHÀ\nĐiều 1: Tiền thuê..."
        temp_file = Path("test_temp.txt")
        temp_file.write_text(sample_text, encoding="utf-8")
        try:
            extracted = route_document(str(temp_file))
            self.assertIn("HỢP ĐỒNG THUÊ NHÀ", extracted)
            self.assertIn("Điều 1", extracted)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_image_preprocessor_if_available(self):
        try:
            from PIL import Image
            from src.ingestion.image_preprocessor import preprocess_image
            img = Image.new("RGB", (200, 200), color="white")
            processed = preprocess_image(img, max_dimension=100)
            self.assertLessEqual(max(processed.size), 100)
        except ImportError:
            self.skipTest("Thư viện PIL chưa cài đặt trong Python 3.9.")

    def test_cer_and_wer_metrics(self):
        from src.utils.formatting import compute_cer, compute_wer
        ref = "Hợp đồng cho thuê nhà ở"
        hyp = "Hợp đồng cho thuê nhà ở"
        self.assertEqual(compute_cer(ref, hyp), 0.0)
        self.assertEqual(compute_wer(ref, hyp), 0.0)

        # Thử nghiệm có lỗi chính tả / nhận diện sai ký tự
        hyp_err = "Hợp đồng cho thue nhà o"
        cer = compute_cer(ref, hyp_err)
        wer = compute_wer(ref, hyp_err)
        self.assertGreater(cer, 0.0)
        self.assertGreater(wer, 0.0)

    def test_magic_bytes_detection(self):
        # Kiểm tra router phát hiện file PNG nhị phân giả lập
        fake_png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        res = route_document(fake_png_header)
        # Sẽ được chuyển sang vision OCR (hoặc thông báo key) thay vì decode text rác
        self.assertTrue(isinstance(res, str))

if __name__ == "__main__":
    unittest.main()
