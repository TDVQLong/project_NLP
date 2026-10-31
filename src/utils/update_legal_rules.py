import json
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

NEW_RULES = [
    {
        "rule_id": "RULE_DISCLOSURE_LEGAL_STATUS",
        "rule_name": "Che giấu thông tin pháp lý, thế chấp, quy hoạch của bất động sản cho thuê",
        "category": "Thông tin & Điều kiện Nhà ở",
        "risk_level": "",
        "legal_basis": "Điều 6 Nghị định 96/2024/NĐ-CP & Điều 160 Luật Nhà ở 2023",
        "trigger_condition": "Bên cho thuê che giấu hoặc không công khai thông tin về việc nhà ở đang bị thế chấp ngân hàng, nhà xây dựng sai phép, nằm trong diện quy hoạch giải tỏa hoặc đang có tranh chấp quyền sở hữu.",
        "explanation": "Theo Điều 6 Nghị định 96/2024/NĐ-CP và Điều 160 Luật Nhà ở 2023, bên cho thuê nhà ở có nghĩa vụ công khai trung thực tình trạng pháp lý, quyền sở hữu và các hạn chế quyền sử dụng của bất động sản trước khi giao kết hợp đồng. Việc che giấu rủi ro quy hoạch/thế chấp gây nguy cơ người thuê bị mất chỗ ở đột ngột.",
        "suggested_clause": "Bên A cam kết nhà ở cho thuê có đầy đủ giấy tờ hợp pháp, không bị tranh chấp, không bị kê biên và không nằm trong diện đã có quyết định thu hồi đất. Nếu phát sinh tranh chấp hoặc quyết định giải tỏa khiến Bên B không thể tiếp tục thuê, Bên A phải hoàn trả 100% tiền cọc, toàn bộ tiền thuê đã trả trước cho thời gian chưa ở và bồi thường thiệt hại thực tế phát sinh.",
        "keywords": ["nhà đang thế chấp", "quy hoạch giải tỏa", "sai phép xây dựng", "tranh chấp quyền sở hữu", "thu hồi đất"]
    },
    {
        "rule_id": "RULE_FIRE_SAFETY_WARRANTY",
        "rule_name": "Miễn trừ trách nhiệm về an toàn kết cấu và phòng cháy chữa cháy (PCCC)",
        "category": "An toàn & Chất lượng Công trình",
        "risk_level": "",
        "legal_basis": "Điều 160 Luật Nhà ở 2023, Điều 477 & Điều 584 Bộ luật Dân sự 2015",
        "trigger_condition": "Hợp đồng quy định Bên A được miễn trừ trách nhiệm bồi thường khi căn nhà xảy ra sự cố chập điện, hỏa hoạn do lỗi kỹ thuật công trình hoặc do nhà ở không đáp ứng các tiêu chuẩn an toàn PCCC.",
        "explanation": "Điều 160 Luật Nhà ở 2023 quy định nhà ở tham gia giao dịch cho thuê phải bảo đảm chất lượng, an toàn cho tính mạng, tài sản của người thuê và tuân thủ quy chuẩn về PCCC. Thỏa thuận miễn trừ trách nhiệm đối với thiệt hại do lỗi kỹ thuật của chính tài sản cho thuê là trái với Điều 477 và 584 BLDS 2015.",
        "suggested_clause": "Bên A có trách nhiệm bảo đảm nhà ở đáp ứng đầy đủ các tiêu chuẩn an toàn kỹ thuật về điện, nước và phòng cháy chữa cháy theo quy định pháp luật. Trường hợp xảy ra sự cố hư hỏng, chập cháy do lỗi kỹ thuật của hệ thống điện nước âm tường hoặc lỗi kết cấu công trình của Bên A, Bên A chịu trách nhiệm bồi thường toàn bộ thiệt hại thực tế cho Bên B.",
        "keywords": ["miễn trừ trách nhiệm cháy nổ", "chập điện tự chịu", "lỗi kỹ thuật không bồi thường", "không bảo đảm PCCC"]
    },
    {
        "rule_id": "RULE_ASYMMETRIC_HANDOVER_DELAY",
        "rule_name": "Miễn trừ trách nhiệm khi chủ nhà chậm bàn giao nhà nhưng phạt nặng bên thuê",
        "category": "Bàn giao & Thời hạn",
        "risk_level": "",
        "legal_basis": "Mẫu số 04 Phụ lục Nghị định 96/2024/NĐ-CP & Điều 3 Bộ luật Dân sự 2015",
        "trigger_condition": "Hợp đồng quy định Bên A chậm bàn giao nhà không phải chịu chế tài bồi thường, trong khi Bên B nhận nhà trễ quá vài ngày thì bị phạt hủy hợp đồng và tịch thu toàn bộ tiền cọc.",
        "explanation": "Trái với nguyên tắc bình đẳng và thiện chí trong giao dịch dân sự (Điều 3 BLDS 2015) và mẫu hợp đồng thuê nhà theo Mẫu số 04 Nghị định 96/2024/NĐ-CP. Thỏa thuận này tạo ra sự bất bình đẳng cực đoan, tước bỏ quyền lợi chính đáng của người thuê khi không được nhận nhà đúng hạn.",
        "suggested_clause": "Bên A có nghĩa vụ bàn giao nhà ở đúng thời hạn quy định tại Điều 4. Trường hợp Bên A chậm bàn giao quá 05 ngày mà không có lý do bất khả kháng, Bên A phải chịu phạt bằng 0,05%/ngày tính trên số tiền đặt cọc cho mỗi ngày chậm bàn giao và Bên B có quyền đơn phương chấm dứt hợp đồng, nhận lại 100% tiền cọc.",
        "keywords": ["chậm bàn giao không bồi thường", "miễn trừ chậm giao nhà", "nhận nhà trễ bị phạt"]
    },
    {
        "rule_id": "RULE_WAIVER_OF_LEGAL_REMEDIES",
        "rule_name": "Tước đoạt quyền tiếp cận công lý, cấm khiếu nại hoặc khởi kiện ra Tòa án",
        "category": "Giải quyết Tranh chấp",
        "risk_level": "",
        "legal_basis": "Điều 11 & Điều 123 Bộ luật Dân sự 2015, Mẫu 04 Nghị định 96/2024/NĐ-CP",
        "trigger_condition": "Hợp đồng quy định mọi tranh chấp do Bên A đơn phương quyết định và là phán quyết cuối cùng; Bên B cam kết tự nguyện từ bỏ quyền khiếu nại cơ quan chức năng hoặc khởi kiện ra Tòa án.",
        "explanation": "Điều khoản bị vô hiệu tuyệt đối theo Điều 123 và Điều 11 BLDS 2015 cùng Bộ luật Tố tụng Dân sự 2015. Quyền yêu cầu Tòa án bảo vệ quyền và lợi ích hợp pháp là quyền hiến định của công dân, không thể bị tước bỏ bằng bất kỳ thỏa thuận dân sự nào.",
        "suggested_clause": "Trong quá trình thực hiện hợp đồng, nếu phát sinh tranh chấp, hai bên cùng nhau thương lượng trên tinh thần thiện chí và bình đẳng. Trường hợp không tự thỏa thuận được, một trong hai bên có quyền yêu cầu Tòa án nhân dân có thẩm quyền giải quyết theo đúng quy định của pháp luật tố tụng.",
        "keywords": ["từ bỏ quyền khiếu nại", "từ bỏ quyền khởi kiện", "phán quyết của chủ nhà là cuối cùng", "không được kiện ra tòa"]
    },
    {
        "rule_id": "RULE_UNILATERAL_DAMAGE_ASSESSMENT",
        "rule_name": "Tự quyền định đoạt mức bồi thường thiệt hại và khấu trừ cọc không theo chứng từ thực tế",
        "category": "Đặt cọc & Bồi thường",
        "risk_level": "",
        "legal_basis": "Điều 360 & Điều 419 Bộ luật Dân sự 2015, Nghị định 96/2024/NĐ-CP",
        "trigger_condition": "Hợp đồng cho phép Bên A tự quyền định giá mức thiệt hại và tự động khấu trừ tiền cọc theo biểu phí nội bộ của Bên A mà không cần cung cấp hóa đơn, chứng từ chi phí thực tế.",
        "explanation": "Theo Điều 360 và Điều 419 BLDS 2015, trách nhiệm bồi thường chỉ phát sinh đối với thiệt hại thực tế, trực tiếp. Việc chủ nhà tự ấn định mức phạt thiệt hại mà không có hóa đơn chứng từ khách quan là hành vi lạm quyền nhằm chiếm đoạt tiền đặt cọc.",
        "suggested_clause": "Mọi khoản khấu trừ tiền cọc để sửa chữa hư hỏng (nếu có) phải căn cứ trên thiệt hại thực tế phát sinh, có báo giá và hóa đơn dịch vụ hợp pháp, đồng thời phải được hai bên cùng kiểm tra và thống nhất trong biên bản thanh lý hợp đồng.",
        "keywords": ["tự quyền trừ tiền cọc", "biểu phí nội bộ chủ nhà", "khấu trừ không cần hóa đơn", "tự định giá hư hỏng"]
    },
    {
        "rule_id": "RULE_TENANT_UNAUTHORIZED_STRUCTURAL_ALTERATION",
        "rule_name": "Bên thuê tự ý đập phá vách ngăn, thay đổi kết cấu chịu lực của công trình nhà ở",
        "category": "Sử dụng & Cải tạo Nhà ở",
        "risk_level": "",
        "legal_basis": "Điều 174 Luật Nhà ở 2023 & Điều 479 Bộ luật Dân sự 2015",
        "trigger_condition": "Hợp đồng cho phép hoặc bên thuê tự ý đập phá vách ngăn, tháo dỡ tường chịu lực, cơi nới diện tích công trình nhà ở mà không có sự đồng ý bằng văn bản của chủ sở hữu và cơ quan quản lý xây dựng.",
        "explanation": "Trái với Điều 174 Luật Nhà ở 2023 và Điều 479 BLDS 2015. Bên thuê chỉ được tu sửa, cải tạo nhà ở khi có sự đồng ý bằng văn bản của chủ sở hữu và phải tuân thủ nghiêm ngặt quy định pháp luật về xây dựng nhằm bảo đảm an toàn kết cấu công trình.",
        "suggested_clause": "Bên B có nghĩa vụ giữ gìn nguyên trạng kết cấu nhà ở; tuyệt đối không được tự ý đập phá, tháo dỡ tường ngăn hoặc thay đổi kết cấu chịu lực của căn nhà nếu chưa có văn bản chấp thuận của Bên A và giấy phép của cơ quan có thẩm quyền (nếu có).",
        "keywords": ["tự ý đập phá vách ngăn", "thay đổi kết cấu chịu lực", "tự do cơi nới phòng", "đập tường không cần xin phép"]
    },
    {
        "rule_id": "RULE_AUTOMATIC_RENEWAL_PRICE_HIKE",
        "rule_name": "Cài bẫy tự động gia hạn hợp đồng kèm áp đặt tăng giá thuê phi lý",
        "category": "Thời hạn & Gia hạn Hợp đồng",
        "risk_level": "",
        "legal_basis": "Điều 170 Luật Nhà ở 2023 & Điều 401 Bộ luật Dân sự 2015",
        "trigger_condition": "Hợp đồng quy định khi hết hạn thuê, nếu bên thuê không thông báo trước 60 ngày thì hợp đồng đương nhiên tự động gia hạn thêm 01 năm với giá thuê tăng thêm 20-30% mà không cần hai bên ký kết lại.",
        "explanation": "Trái với nguyên tắc tự do thỏa thuận và tự nguyện cam kết tại Điều 3 và Điều 401 BLDS 2015. Việc gia hạn hợp đồng và điều chỉnh giá thuê nhà ở phải dựa trên sự đồng thuận rõ ràng của các bên tại thời điểm hết hạn theo Điều 170 Luật Nhà ở 2023.",
        "suggested_clause": "Khi hết hạn hợp đồng, nếu Bên B có nhu cầu tiếp tục thuê thì phải thông báo trước cho Bên A tối thiểu 30 ngày. Việc gia hạn thời hạn thuê và điều chỉnh giá thuê (nếu có) phải được hai bên cùng thỏa thuận và ký kết phụ lục hợp đồng bằng văn bản.",
        "keywords": ["tự động gia hạn kèm tăng giá", "tự động gia hạn thêm 1 năm", "không báo trước 60 ngày bị gia hạn"]
    },
    {
        "rule_id": "RULE_RESTRICTION_FREE_SPEECH",
        "rule_name": "Cấm người thuê phản ánh chất lượng cơ sở vật chất, review lên mạng xã hội",
        "category": "Quyền tự do & Chế tài",
        "risk_level": "",
        "legal_basis": "Điều 25 Hiến pháp 2013 & Nguyên tắc thiện chí Điều 3 Bộ luật Dân sự 2015",
        "trigger_condition": "Hợp đồng cấm người thuê đăng tải phản ánh, hình ảnh hoặc nhận xét về tình trạng xuống cấp của căn nhà lên mạng xã hội, nếu vi phạm bị phạt tiền hoặc tịch thu toàn bộ tiền đặt cọc.",
        "explanation": "Trái với quyền tự do ngôn luận tại Điều 25 Hiến pháp 2013 và nguyên tắc thiện chí trong hợp đồng. Người thuê có quyền phản ánh đúng sự thật về chất lượng dịch vụ; chủ nhà không được dùng chế tài tịch thu tiền cọc để ngăn chặn phản hồi chính đáng của khách hàng.",
        "suggested_clause": "Người thuê có quyền phản ánh trung thực về tình trạng cơ sở vật chất và dịch vụ. Hai bên cam kết tiếp nhận và giải quyết các khiếu nại, phản ánh trên tinh thần hợp tác, tôn trọng quyền lợi của nhau.",
        "keywords": ["cấm đăng lên mạng xã hội", "cấm review tiêu cực", "phạt tiền khi phản ánh chất lượng", "tịch thu cọc khi đăng bài"]
    }
]

def main():
    rules_file = os.path.join("data", "legal_rules.json")
    with open(rules_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_ids = {r["rule_id"] for r in data.get("rules", [])}
    added = 0
    for nr in NEW_RULES:
        if nr["rule_id"] not in existing_ids:
            data["rules"].append(nr)
            added += 1

    data["version"] = "1.2"
    data["total_rules"] = len(data["rules"])
    data["description"] = (
        "Bộ quy tắc rà soát rủi ro pháp lý & thương mại cho hợp đồng thuê nhà theo "
        "Bộ luật Dân sự 2015, Luật Nhà ở 2023 (Luật số 27/2023/QH15), "
        "Luật Kinh doanh bất động sản 2023 & Nghị định 96/2024/NĐ-CP (Cơ sở dữ liệu Quốc gia vbpl.vn)"
    )

    with open(rules_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã bổ sung thành công {added} quy tắc mới vào legal_rules.json!")
    print(f"📊 Tổng số rules hiện tại: {data['total_rules']} rules.")

if __name__ == "__main__":
    main()
