import unittest
from src.segmentation.clause_segmenter import ClauseSegmenter
from src.segmentation.baseline_aligner import BaselineAligner
from src.segmentation.omission_detector import OmissionDetector

class TestSegmentation(unittest.TestCase):
    def setUp(self):
        self.sample_contract = """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
HỢP ĐỒNG THUÊ NHÀ Ở

Điều 1. Đối tượng hợp đồng và tài sản thuê
Bên A đồng ý cho Bên B thuê căn hộ chung cư số 502.

Điều 2. Giá thuê và phương thức thanh toán
Giá thuê căn nhà là 5.000.000 đồng/tháng.

Điều 3. Tiền đặt cọc
Bên B đặt cọc cho Bên A số tiền 10.000.000 đồng.
"""
        self.canonical_clauses = [
            {"clause_id": "B_01", "title": "Đối tượng thuê", "content": "Bên cho thuê cho bên thuê sử dụng nhà ở..."},
            {"clause_id": "B_02", "title": "Giá thuê và thanh toán", "content": "Giá thuê nhà do hai bên thỏa thuận thanh toán định kỳ..."},
            {"clause_id": "B_03", "title": "Nghĩa vụ sửa chữa nhà ở", "content": "Bên cho thuê có nghĩa vụ bảo dưỡng sửa chữa nhà định kỳ...", "is_mandatory": True}
        ]

    def test_clause_segmenter(self):
        segmenter = ClauseSegmenter()
        clauses = segmenter.segment(self.sample_contract)
        self.assertEqual(len(clauses), 3)
        self.assertEqual(clauses[0]["clause_id"], "C_01")
        self.assertIn("502", clauses[0]["raw_text"])

    def test_baseline_aligner(self):
        aligner = BaselineAligner(self.canonical_clauses)
        match = aligner.align_clause("Giá thuê nhà là 5.000.000 đồng mỗi tháng")
        self.assertIsNotNone(match)
        self.assertEqual(match["canonical_clause_id"], "B_02")

    def test_omission_detector(self):
        detector = OmissionDetector(self.canonical_clauses)
        aligned_results = [
            {"canonical_clause_id": "B_01"},
            {"canonical_clause_id": "B_02"}
        ]
        omissions = detector.detect_omissions(aligned_results)
        self.assertEqual(len(omissions), 1)
        self.assertEqual(omissions[0]["omitted_clause_id"], "B_03")

if __name__ == "__main__":
    unittest.main()

