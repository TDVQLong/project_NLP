import json
import random
import os

# Danh sách họ tên, CCCD, địa chỉ đa dạng để sinh metadata thực tế
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương"]
DEM_NAM = ["Văn", "Đức", "Hải", "Minh", "Quốc", "Hữu", "Thành", "Tuấn", "Anh", "Hoàng", "Trọng"]
TEN_NAM = ["An", "Bình", "Cường", "Dũng", "Đạt", "Huy", "Hùng", "Khoa", "Long", "Nam", "Phúc", "Quân", "Sơn", "Thắng", "Tùng", "Việt"]
DEM_NU = ["Thị", "Thu", "Mai", "Phương", "Ngọc", "Thanh", "Bích", "Hồng", "Kim", "Ánh"]
TEN_NU = ["Anh", "Chi", "Dung", "Giang", "Hà", "Hương", "Linh", "Mai", "Nga", "Nhung", "Oanh", "Phương", "Quỳnh", "Thảo", "Trang", "Yến"]

def random_person(is_female=False):
    ho = random.choice(HO)
    if is_female:
        ten = f"{ho} {random.choice(DEM_NU)} {random.choice(TEN_NU)}"
    else:
        ten = f"{ho} {random.choice(DEM_NAM)} {random.choice(TEN_NAM)}"
    cccd = f"0{random.randint(10, 99)}0{random.randint(70, 99)}{random.randint(100000, 999999)}"
    return f"{ten} (CCCD: {cccd})"

TAI_SAN_TEMPLATES = [
    "Căn hộ số {num}, Tòa nhà {building}, Khu đô thị {area}, Phường {ward}, Quận {dist}, TP. Hà Nội",
    "Phòng trọ số {num}, Số {house} ngõ {lane} đường {street}, Phường {ward}, Quận {dist}, TP. Hà Nội",
    "Căn hộ mini tầng {floor}, Số {house} đường {street}, Phường {ward}, Quận {dist}, TP. Hồ Chí Minh",
    "Căn hộ chung cư {building}, Tầng {floor}, Căn {num}, Đường {street}, Quận {dist}, TP. Hồ Chí Minh",
    "Nhà nguyên căn 03 tầng tại số {house} đường {street}, Phường {ward}, Quận {dist}, TP. Đà Nẵng",
    "Căn hộ Studio số {num}, Tòa {building}, Phường {ward}, TP. Thủ Đức, TP. Hồ Chí Minh",
    "Phòng khép kín tầng {floor}, số nhà {house}, ngách {lane}, đường {street}, Quận {dist}, TP. Cần Thơ"
]

BUILDINGS = ["Vinhomes Smart City", "Masteri West Heights", "The Sun Avenue", "Sky Park Residence", "Landmark 81", "Goldmark City", "Eco Green", "D'Leroi Soleil", "Sunrise City"]
AREAS = ["Tây Mỗ", "An Khánh", "Mễ Trì", "Cầu Giấy", "Dịch Vọng", "Bình Thạnh", "Tân Bình", "Quận 7", "Hòa Cường"]
STREETS = ["Nguyễn Trãi", "Xuân Thủy", "Trần Duy Hưng", "Lê Văn Lương", "Giải Phóng", "Điện Biên Phủ", "Cách Mạng Tháng 8", "Nguyễn Thị Minh Khai", "Ngô Quyền", "Võ Văn Kiệt"]
DISTRICTS = ["Cầu Giấy", "Thanh Xuân", "Nam Từ Liêm", "Đống Đa", "Bình Thạnh", "Quận 1", "Quận 7", "Hải Châu", "Ninh Kiều"]
WARDS = ["Phường 1", "Phường 5", "Phường 12", "Trung Hòa", "Mai Dịch", "Khương Mai", "Bến Nghé", "Thảo Điền", "Thuận Phước"]

def random_property():
    tpl = random.choice(TAI_SAN_TEMPLATES)
    return tpl.format(
        num=random.randint(101, 2809),
        floor=random.randint(2, 25),
        house=random.randint(12, 388),
        lane=random.randint(10, 185),
        building=random.choice(BUILDINGS),
        area=random.choice(AREAS),
        street=random.choice(STREETS),
        ward=random.choice(WARDS),
        dist=random.choice(DISTRICTS)
    )

# ==========================================
# POOL 25 LOẠI ĐIỀU KHOẢN SAI PHẠM (CHIA THEO ĐỘ KHÓ)
# ==========================================

# NHÓM 1: DỄ (Blatant / Explicit - Vi phạm trực diện các quy định cấm của luật)
VIOLATIONS_EASY = [
    {
        "id": "E_01",
        "ten_dieu_khoan": "Điều 6: Quyền và nghĩa vụ của Bên cho thuê",
        "noi_dung_van_ban": "Bên A có quyền giữ chìa khóa phụ và được phép tự ý vào phòng kiểm tra hiện trạng, an ninh vào bất kỳ thời điểm nào trong ngày mà không cần sự đồng ý hay báo trước cho Bên B.",
        "loai_sai_pham": "Xâm phạm quyền bất khả xâm phạm về chỗ ở",
        "giai_thich_phap_ly": "Trái với Điều 22 Hiến pháp 2013 và Điều 10 Luật Nhà ở 2023. Bên cho thuê không được tự ý xâm nhập vào chỗ ở hợp pháp của người thuê nếu không có sự đồng ý của họ, trừ trường hợp khẩn cấp luật định."
    },
    {
        "id": "E_02",
        "ten_dieu_khoan": "Điều 10: Chấm dứt hợp đồng và biện pháp xử lý",
        "noi_dung_van_ban": "Bên A được quyền đơn phương lấy lại nhà bất cứ lúc nào khi có nhu cầu sử dụng, chỉ cần thông báo cho Bên B trước 24 giờ mà không phải bồi thường bất kỳ khoản tiền nào.",
        "loai_sai_pham": "Đơn phương chấm dứt hợp đồng trái luật với thời hạn báo trước quá ngắn",
        "giai_thich_phap_ly": "Vi phạm khoản 4 Điều 172 Luật Nhà ở 2023. Bên đơn phương chấm dứt hợp đồng thuê nhà phải thông báo trước bằng văn bản cho bên kia ít nhất 30 ngày (trừ trường hợp hai bên có thỏa thuận hợp lý khác nhưng không được tước đoạt quyền có chỗ ở tối thiểu)."
    },
    {
        "id": "E_03",
        "ten_dieu_khoan": "Điều 9: Phạt vi phạm hợp đồng",
        "noi_dung_van_ban": "Trường hợp Bên B chậm thanh toán tiền thuê nhà dù chỉ 01 ngày, Bên B sẽ bị phạt số tiền cố định là 500.000 đồng cho mỗi ngày chậm nộp.",
        "loai_sai_pham": "Phạt vi phạm chậm thanh toán vượt quá mức trần luật định",
        "giai_thich_phap_ly": "Trái với Điều 418 và Điều 468 Bộ luật Dân sự 2015. Tiền phạt chậm thanh toán và lãi suất chậm trả trong giao dịch dân sự không được vượt quá trần 20%/năm trên số tiền thực tế chậm trả."
    },
    {
        "id": "E_04",
        "ten_dieu_khoan": "Điều 8: Trách nhiệm do vi phạm hợp đồng",
        "noi_dung_van_ban": "Nếu Bên B chậm thanh toán tiền thuê quá 03 ngày, Bên A có toàn quyền khóa cửa phòng, cắt toàn bộ điện nước sinh hoạt và có quyền tịch thu, tự do thanh lý toàn bộ tài sản cá nhân của Bên B có trong phòng.",
        "loai_sai_pham": "Tự ý cưỡng chế, chiếm giữ và phát mại tài sản cá nhân trái pháp luật",
        "giai_thich_phap_ly": "Vi phạm nghiêm trọng quyền sở hữu tài sản theo Điều 158 Bộ luật Dân sự 2015. Bên cho thuê không có thẩm quyền tư pháp để tự ý tịch thu, chiếm giữ hay thanh lý tài sản riêng của công dân."
    },
    {
        "id": "E_05",
        "ten_dieu_khoan": "Điều 5: Sử dụng nhà ở thuê",
        "noi_dung_van_ban": "Bên B có quyền tự ý đập phá vách ngăn, tháo dỡ tường chịu lực và thay đổi toàn bộ kết cấu căn nhà để phục vụ kinh doanh mà không cần sự đồng ý hay văn bản phê duyệt của Bên A.",
        "loai_sai_pham": "Tự ý cải tạo, thay đổi kết cấu công trình nhà ở",
        "giai_thich_phap_ly": "Trái với Điều 174 Luật Nhà ở 2023 và Điều 479 Bộ luật Dân sự 2015. Bên thuê chỉ được cải tạo nhà ở khi có sự đồng ý bằng văn bản của chủ sở hữu và phải tuân thủ pháp luật về xây dựng."
    },
    {
        "id": "E_06",
        "ten_dieu_khoan": "Điều 10: Chấm dứt hợp đồng thuê nhà",
        "noi_dung_van_ban": "Bên B bị cấm tuyệt đối việc đơn phương chấm dứt hợp đồng trước hạn trong mọi trường hợp; nếu Bên B trả phòng sớm vì bất kỳ lý do gì thì bị mất toàn bộ tiền cọc và phải nộp đủ 100% tiền thuê cho các tháng còn lại của hợp đồng.",
        "loai_sai_pham": "Tước đoạt quyền đơn phương chấm dứt hợp đồng hợp pháp của người thuê",
        "giai_thich_phap_ly": "Trái với Điều 428 Bộ luật Dân sự 2015 và Điều 172 Luật Nhà ở 2023. Pháp luật cho phép bên thuê đơn phương chấm dứt hợp đồng khi có lý do chính đáng hoặc khi bên cho thuê vi phạm nghiêm trọng nghĩa vụ."
    },
    {
        "id": "E_07",
        "ten_dieu_khoan": "Điều 3: Tiền đặt cọc và phương thức thanh toán",
        "noi_dung_van_ban": "Bên B nộp tiền đặt cọc tương đương 02 tháng tiền nhà. Số tiền này thuộc quyền sở hữu vĩnh viễn của Bên A ngay tại thời điểm ký kết và sẽ không được hoàn lại cho Bên B trong bất kỳ trường hợp nào.",
        "loai_sai_pham": "Tịch thu toàn bộ tiền đặt cọc vô điều kiện",
        "giai_thich_phap_ly": "Trái với bản chất của biện pháp bảo đảm đặt cọc quy định tại Điều 328 Bộ luật Dân sự 2015. Khi hợp đồng kết thúc hợp pháp, tiền đặt cọc phải được hoàn trả cho bên đặt cọc sau khi đã thanh toán xong các nghĩa vụ tài chính."
    },
    {
        "id": "E_08",
        "ten_dieu_khoan": "Điều 6: Quyền và nghĩa vụ của Bên cho thuê",
        "noi_dung_van_ban": "Bên A không có nghĩa vụ phối hợp hay hỗ trợ Bên B thực hiện thủ tục đăng ký tạm trú với cơ quan Công an có thẩm quyền. Mọi vi phạm hành chính về cư trú do Bên B tự chịu trách nhiệm.",
        "loai_sai_pham": "Trốn tránh nghĩa vụ tạo điều kiện đăng ký cư trú",
        "giai_thich_phap_ly": "Trái với Luật Cư trú 2020 và nghĩa vụ của chủ cơ sở cho thuê lưu trú. Chủ sở hữu nhà ở có nghĩa vụ cung cấp hồ sơ pháp lý hợp pháp để người thuê thực hiện quyền đăng ký tạm trú theo quy định."
    }
]

# NHÓM 2: TRUNG BÌNH (Commercial Imbalance / Hidden Traps - Bất bình đẳng thương mại, chế tài kép)
VIOLATIONS_MEDIUM = [
    {
        "id": "M_01",
        "ten_dieu_khoan": "Điều 9: Phạt vi phạm hợp đồng",
        "noi_dung_van_ban": "Nếu Bên B chấm dứt hợp đồng trước hạn mà không được Bên A đồng ý, Bên B vừa bị tịch thu toàn bộ 100% số tiền cọc, vừa phải nộp thêm khoản tiền phạt vi phạm tương đương 02 tháng tiền thuê nhà.",
        "loai_sai_pham": "Áp dụng chế tài phạt kép trái nguyên tắc công bằng",
        "giai_thich_phap_ly": "Theo Điều 328 và Điều 418 Bộ luật Dân sự 2015, tiền cọc đã mang bản chất bảo đảm và bù đắp rủi ro chấm dứt hợp đồng. Việc áp dụng đồng thời vừa mất toàn bộ cọc vừa phạt thêm nhiều tháng tiền thuê là chế tài phạt kép bất hợp lý, xâm phạm quyền lợi người thuê."
    },
    {
        "id": "M_02",
        "ten_dieu_khoan": "Điều 2: Giá thuê nhà ở và điều chỉnh giá",
        "noi_dung_van_ban": "Trong thời hạn hợp đồng 12 tháng, Bên A có toàn quyền điều chỉnh tăng giá thuê nhà bất kỳ lúc nào nếu thấy giá cả thị trường biến động, mức tăng từ 10% đến 20% mỗi lần và chỉ cần thông báo trước 07 ngày.",
        "loai_sai_pham": "Đơn phương tăng giá thuê trong thời hạn hợp đồng",
        "giai_thich_phap_ly": "Trái với Điều 170 Luật Nhà ở 2023 và Điều 473 Bộ luật Dân sự 2015. Giá thuê nhà phải giữ nguyên trong suốt thời hạn hợp đồng; mọi sự điều chỉnh giá chỉ được thực hiện khi hai bên cùng thỏa thuận đồng thuận."
    },
    {
        "id": "M_03",
        "ten_dieu_khoan": "Điều 10: Chấm dứt hợp đồng và chuyển giao quyền sở hữu",
        "noi_dung_van_ban": "Trong trường hợp Bên A bán, chuyển nhượng hoặc thế chấp căn nhà cho bên thứ ba, hợp đồng thuê nhà này đương nhiên chấm dứt hiệu lực và Bên B phải dọn ra khỏi nhà trong vòng 07 ngày mà không được đòi bồi thường.",
        "loai_sai_pham": "Xâm phạm quyền tiếp tục thuê nhà khi chuyển quyền sở hữu",
        "giai_thich_phap_ly": "Trái với Điều 480 Bộ luật Dân sự 2015 và Luật Nhà ở 2023. Khi chủ sở hữu chuyển quyền sở hữu nhà ở đang cho thuê, bên thuê vẫn có quyền tiếp tục thuê nhà đến hết hạn hợp đồng, chủ sở hữu mới phải kế thừa toàn bộ nghĩa vụ."
    },
    {
        "id": "M_04",
        "ten_dieu_khoan": "Điều 7: Quyền và nghĩa vụ của Bên thuê",
        "noi_dung_van_ban": "Bên B có trách nhiệm tự bỏ 100% chi phí sửa chữa mọi hỏng hóc phát sinh trong quá trình thuê, bao gồm cả các hư hỏng kết cấu lớn như nứt trần, sụt lún móng, thấm dột mái nhà do hao mòn tự nhiên hoặc lỗi công trình.",
        "loai_sai_pham": "Đẩy toàn bộ trách nhiệm bảo trì kết cấu lớn cho người thuê",
        "giai_thich_phap_ly": "Trái với Điều 477 Bộ luật Dân sự 2015. Bên cho thuê có nghĩa vụ bảo đảm tài sản cho thuê trong tình trạng tốt và chịu trách nhiệm sửa chữa các hư hỏng lớn, khuyết tật kỹ thuật thuộc về kết cấu của tài sản."
    },
    {
        "id": "M_05",
        "ten_dieu_khoan": "Điều 2: Giá thuê và chi phí dịch vụ",
        "noi_dung_van_ban": "Bên B thanh toán tiền điện với đơn giá cố định là 5.500 đồng/kWh và tiền nước là 150.000 đồng/người/tháng, không căn cứ vào chỉ số công tơ thực tế hay hóa đơn của đơn vị cấp điện nước.",
        "loai_sai_pham": "Thu tiền điện nước vượt quá biểu giá quy định của nhà nước",
        "giai_thich_phap_ly": "Vi phạm quy định của Bộ Công Thương về giá bán lẻ điện cho người thuê nhà (Quyết định số 2941/QĐ-BCT và Nghị định 134/2013/NĐ-CP được sửa đổi bổ sung). Hành vi thu giá điện sinh hoạt của người thuê nhà cao hơn biểu giá quy định là hành vi vi phạm hành chính."
    },
    {
        "id": "M_06",
        "ten_dieu_khoan": "Điều 4: Thời hạn bàn giao và chế tài chậm bàn giao",
        "noi_dung_van_ban": "Nếu Bên A chậm bàn giao nhà ở quá thời hạn đã cam kết, Bên A được miễn trừ toàn bộ trách nhiệm bồi thường; ngược lại nếu Bên B nhận nhà trễ quá 03 ngày thì bị hủy hợp đồng và tịch thu toàn bộ tiền cọc.",
        "loai_sai_pham": "Điều khoản bất bình đẳng nghiêm trọng về trách nhiệm bàn giao tài sản",
        "giai_thich_phap_ly": "Trái với nguyên tắc bình đẳng, thiện chí quy định tại Điều 3 Bộ luật Dân sự 2015. Quy định miễn trừ trách nhiệm cho một bên trong khi áp chế tài cực đoan cho bên còn lại làm mất cân bằng quyền lợi hợp đồng."
    },
    {
        "id": "M_07",
        "ten_dieu_khoan": "Điều 4: Tự động gia hạn hợp đồng",
        "noi_dung_van_ban": "Khi hết hạn hợp đồng, nếu Bên B không thông báo trước 60 ngày bằng văn bản, hợp đồng này sẽ đương nhiên tự động gia hạn thêm 01 năm với giá thuê tăng thêm 25% so với giá cũ mà không cần hai bên ký kết lại.",
        "loai_sai_pham": "Cài bẫy tự động gia hạn kèm áp đặt tăng giá",
        "giai_thich_phap_ly": "Trái với nguyên tắc tự do thỏa thuận và tự nguyện cam kết tại Điều 3 và Điều 401 Bộ luật Dân sự 2015. Việc gia hạn hợp đồng và tăng giá thuê phải dựa trên sự đồng thuận rõ ràng của các bên tại thời điểm hết hạn."
    },
    {
        "id": "M_08",
        "ten_dieu_khoan": "Điều 8: Giới hạn trách nhiệm tài sản",
        "noi_dung_van_ban": "Bên A hoàn toàn không chịu trách nhiệm trong trường hợp nhà cho thuê bị chập điện, cháy nổ do hệ thống dây điện âm tường cũ kỹ của tòa nhà gây thiệt hại đến tài sản, tính mạng của Bên B.",
        "loai_sai_pham": "Thỏa thuận miễn trừ trách nhiệm đối với thiệt hại do lỗi kỹ thuật tài sản",
        "giai_thich_phap_ly": "Trái với Điều 477 và Điều 584 Bộ luật Dân sự 2015. Chủ sở hữu tài sản phải bồi thường thiệt hại do tài sản gây ra nếu lỗi bắt nguồn từ tình trạng kỹ thuật, hư hỏng của chính tài sản đó."
    }
]

# NHÓM 3: KHÓ (Subtle / Ambiguous / Camouflaged - Bẫy tinh vi, ngụy trang dưới từ ngữ thỏa thuận, mập mờ)
VIOLATIONS_HARD = [
    {
        "id": "H_01",
        "ten_dieu_khoan": "Điều 3: Điều kiện hoàn trả tiền đặt cọc",
        "noi_dung_van_ban": "Tiền đặt cọc chỉ được Bên A hoàn trả sau khi Bên B đã bàn giao lại căn nhà nguyên trạng như mới 100%, không có bất kỳ vết trầy xước nào dù là nhỏ nhất, và chỉ được chi trả sau khi Bên A đã tìm được khách thuê mới vào thay thế.",
        "loai_sai_pham": "Điều kiện hoàn cọc bất khả thi và bẫy giam giữ tiền cọc",
        "giai_thich_phap_ly": "Điều khoản vi phạm nguyên tắc công bằng tại Điều 3 và Điều 328 Bộ luật Dân sự 2015. Hao mòn tự nhiên trong quá trình sử dụng là bình thường và không thể buộc người thuê trả nhà 'nguyên trạng như mới 100%'. Việc gắn nghĩa vụ trả cọc vào việc tìm người thuê mới là chuyển giao rủi ro kinh doanh trái luật cho bên thuê."
    },
    {
        "id": "H_02",
        "ten_dieu_khoan": "Điều 3: Quyền khấu trừ tiền đặt cọc",
        "noi_dung_van_ban": "Khi thanh lý hợp đồng, Bên A có toàn quyền tùy nghi xác định và tự động khấu trừ tiền cọc vào các khoản 'chi phí tân trang, sơn sửa, hao hụt giá trị căn nhà' theo biểu phí nội bộ của Bên A mà không cần cung cấp hóa đơn chứng từ thực tế.",
        "loai_sai_pham": "Quyền tự do khấu trừ chi phí mơ hồ không có chứng từ",
        "giai_thich_phap_ly": "Trái với nguyên tắc xác định thiệt hại thực tế theo Điều 360 và Điều 419 Bộ luật Dân sự 2015. Mọi khoản khấu trừ tiền cọc phải căn cứ trên chi phí bồi thường thiệt hại thực tế có chứng từ hợp lệ, không thể dựa trên đánh giá chủ quan một phía của bên cho thuê."
    },
    {
        "id": "H_03",
        "ten_dieu_khoan": "Điều 11: Cơ chế giải quyết tranh chấp",
        "noi_dung_van_ban": "Trong trường hợp xảy ra tranh chấp giữa hai bên, phán quyết cuối cùng của Bên A là quyết định có giá trị bắt buộc thi hành; Bên B cam kết tự nguyện từ bỏ quyền khiếu nại, khiếu kiện ra Tòa án hoặc cơ quan chức năng.",
        "loai_sai_pham": "Tước đoạt quyền tiếp cận công lý và quyền khởi kiện",
        "giai_thich_phap_ly": "Điều khoản bị vô hiệu theo Điều 123 và Điều 11 Bộ luật Dân sự 2015 cùng Bộ luật Tố tụng Dân sự 2015. Quyền yêu cầu Tòa án bảo vệ quyền và lợi ích hợp pháp là quyền hiến định không thể bị tước bỏ bằng bất kỳ thỏa thuận dân sự nào."
    },
    {
        "id": "H_04",
        "ten_dieu_khoan": "Điều 5: Quy định sinh hoạt và sử dụng chỗ ở",
        "noi_dung_van_ban": "Bên B tuyệt đối không được phép cho bất kỳ người thân, bạn bè nào vào phòng thăm hoặc ở lại quá 15 phút vào ban ngày. Nếu Bên A phát hiện có người lạ xuất hiện trong phòng, Bên B sẽ bị phạt 1.000.000 đồng/lần.",
        "loai_sai_pham": "Xâm phạm quyền tự do sinh hoạt và đời sống riêng tư trong chỗ ở hợp pháp",
        "giai_thich_phap_ly": "Trái với Điều 21 Hiến pháp 2013 và quyền sử dụng nhà ở hợp pháp theo Luật Nhà ở 2023. Trong thời hạn thuê, người thuê có quyền sinh hoạt cá nhân hợp pháp, đón tiếp người thân mà không bị hạn chế một cách vô lý."
    },
    {
        "id": "H_05",
        "ten_dieu_khoan": "Điều 9: Chế tài bảo vệ uy tín cơ sở cho thuê",
        "noi_dung_van_ban": "Bên B cam kết không được đăng tải bất kỳ phản ánh, hình ảnh hoặc nhận xét tiêu cực nào về tình trạng cơ sở vật chất của căn nhà lên mạng xã hội. Nếu vi phạm, Bên B đồng ý bị tịch thu toàn bộ tiền cọc và chấm dứt hợp đồng ngay lập tức.",
        "loai_sai_pham": "Hạn chế quyền tự do ngôn luận và phản ánh thông tin thực tế",
        "giai_thich_phap_ly": "Trái với Điều 25 Hiến pháp 2013 và nguyên tắc thiện chí trong hợp đồng. Bên thuê có quyền phản ánh đúng sự thật về chất lượng dịch vụ; bên cho thuê không được dùng chế tài cọc để bịt miệng hoặc ngăn chặn phản hồi chính đáng."
    },
    {
        "id": "H_06",
        "ten_dieu_khoan": "Điều 10: Rủi ro pháp lý về quy hoạch và xây dựng",
        "noi_dung_van_ban": "Trường hợp căn nhà bị cơ quan nhà nước đình chỉ hoạt động hoặc cưỡng chế do sai phạm giấy phép xây dựng hoặc nằm trong diện quy hoạch thu hồi đất, Bên A được miễn trừ nghĩa vụ hoàn trả tiền thuê đã thanh toán trước của Bên B.",
        "loai_sai_pham": "Chuyển giao rủi ro pháp lý của tài sản cho người thuê",
        "giai_thich_phap_ly": "Trái với Điều 472 và Điều 476 Bộ luật Dân sự 2015. Bên cho thuê phải cam kết tài sản cho thuê đủ điều kiện pháp lý để ở. Khi hợp đồng chấm dứt do sự kiện bất khả kháng hoặc lỗi pháp lý của công trình, bên cho thuê bắt buộc phải hoàn trả tiền thuê của thời gian chưa sử dụng."
    },
    {
        "id": "H_07",
        "ten_dieu_khoan": "Điều 3: Thời hạn hoàn trả tiền đặt cọc",
        "noi_dung_van_ban": "Khoản tiền đặt cọc của Bên B sẽ được Bên A thu xếp hoàn trả vào thời điểm Bên A cân đối được nguồn tài chính nhàn rỗi sau khi hai bên ký biên bản thanh lý hợp đồng.",
        "loai_sai_pham": "Mập mờ, vô hiệu hóa nghĩa vụ hoàn trả tiền cọc đúng hạn",
        "giai_thich_phap_ly": "Trái với Điều 278 và Điều 328 Bộ luật Dân sự 2015 về thời hạn thực hiện nghĩa vụ. Quy định nghĩa vụ hoàn trả phụ thuộc hoàn toàn vào ý chí chủ quan và tình trạng tài chính của một bên là điều khoản cài cắm nhằm trì hoãn vô thời hạn nghĩa vụ trả tiền."
    },
    {
        "id": "H_08",
        "ten_dieu_khoan": "Điều 8: Bồi thường chi phí hành chính và tư vấn",
        "noi_dung_van_ban": "Trong mọi trường hợp Bên B có ý định đơn phương chấm dứt hợp đồng, Bên B phải thanh toán một khoản 'chi phí tư vấn thủ tục hành chính' trị giá 01 tháng tiền nhà cho Bên A trước khi nộp đơn xin chấm dứt.",
        "loai_sai_pham": "Đặt ra rào cản tài chính vô lý cản trở quyền chấm dứt hợp đồng",
        "giai_thich_phap_ly": "Trái với Điều 428 Bộ luật Dân sự 2015 và Điều 172 Luật Nhà ở 2023. Quyền đơn phương chấm dứt hợp đồng khi có thông báo trước hợp lệ không thể bị ràng buộc bởi các khoản 'phí hành chính' tự đặt ra nhằm thu lợi bất chính."
    }
]

# Đánh giá tổng thể theo số lượng và độ nghiêm trọng
def generate_overall_assessment(violations):
    if len(violations) == 0:
        return "Hợp đồng tuân thủ đúng các quy định của Bộ luật Dân sự 2015 và Luật Nhà ở 2023; quyền và nghĩa vụ giữa hai bên được phân định rõ ràng, bình đẳng, không phát hiện điều khoản vi phạm pháp luật hay bẫy thương mại."
    
    has_easy = any(v["id"].startswith("E_") for v in violations)
    has_med = any(v["id"].startswith("M_") for v in violations)
    has_hard = any(v["id"].startswith("H_") for v in violations)
    
    if len(violations) >= 3:
        return "Hợp đồng tiềm ẩn rủi ro pháp lý đặc biệt nghiêm trọng; chứa nhiều điều khoản vô hiệu do vi phạm trực tiếp các điều cấm của luật và cài cắm bẫy tài chính bất bình đẳng, gây thiệt hại nghiêm trọng cho quyền lợi người thuê."
    elif has_easy:
        return "Hợp đồng vô hiệu một phần do chứa điều khoản xâm phạm quyền cơ bản luật định (quyền về chỗ ở, quyền sở hữu tài sản hoặc vượt trần chế tài vi phạm)."
    elif has_med and has_hard:
        return "Hợp đồng có độ rủi ro thương mại cao; tồn tại các điều khoản bất bình đẳng và bẫy giam giữ tiền cọc tinh vi cần đàm phán sửa đổi trước khi ký kết."
    elif has_med:
        return "Hợp đồng có sự mất cân bằng về quyền và nghĩa vụ thương mại; chứa điều khoản thiên vị bên cho thuê về điều chỉnh giá hoặc nghĩa vụ bảo trì tài sản."
    else:
        return "Hợp đồng chứa các điều khoản bẫy ngôn từ và hạn chế quyền dân sự tinh vi ngụy trang dưới dạng thỏa thuận tự nguyện, người thuê cần yêu cầu loại bỏ."

def generate_dataset(total_samples=120):
    dataset = []
    
    # 1. Tạo 10 mẫu SẠCH (Clean negative control - 0 rủi ro)
    num_clean = 10
    for i in range(1, num_clean + 1):
        sample_id = f"HD_{i:03d}"
        sample = {
            "sample_id": sample_id,
            "metadata": {
                "ben_cho_thue": random_person(is_female=random.choice([True, False])),
                "ben_thue": random_person(is_female=random.choice([True, False])),
                "tai_san_thue": random_property()
            },
            "dieu_khoan_vi_pham": [],
            "danh_gia_tong_the": generate_overall_assessment([])
        }
        dataset.append(sample)
    
    # 2. Tạo 110 mẫu có vi phạm (chia đều các kiểu lỗi, phân tầng độ khó)
    # Ta sẽ phân bổ:
    # - 35 mẫu Độ khó DỄ (1-2 lỗi DỄ)
    # - 40 mẫu Độ khó TRUNG BÌNH (1-2 lỗi TRUNG BÌNH hoặc kết hợp DỄ)
    # - 35 mẫu Độ khó KHÓ (1-3 lỗi KHÓ hoặc phối hợp KHÓ + TRUNG BÌNH)
    
    sample_counter = num_clean + 1
    
    # Tier DỄ (35 mẫu)
    for _ in range(35):
        sample_id = f"HD_{sample_counter:03d}"
        sample_counter += 1
        num_v = random.choice([1, 2])
        chosen_v = random.sample(VIOLATIONS_EASY, num_v)
        
        dieu_khoan = []
        for v in chosen_v:
            dieu_khoan.append({
                "ten_dieu_khoan": v["ten_dieu_khoan"],
                "noi_dung_van_ban": v["noi_dung_van_ban"],
                "loai_sai_pham": v["loai_sai_pham"],
                "giai_thich_phap_ly": v["giai_thich_phap_ly"]
            })
            
        dataset.append({
            "sample_id": sample_id,
            "metadata": {
                "ben_cho_thue": random_person(is_female=random.choice([True, False])),
                "ben_thue": random_person(is_female=random.choice([True, False])),
                "tai_san_thue": random_property()
            },
            "dieu_khoan_vi_pham": dieu_khoan,
            "danh_gia_tong_the": generate_overall_assessment(chosen_v)
        })
        
    # Tier TRUNG BÌNH (40 mẫu)
    for _ in range(40):
        sample_id = f"HD_{sample_counter:03d}"
        sample_counter += 1
        num_v = random.choice([1, 2])
        if num_v == 1:
            chosen_v = [random.choice(VIOLATIONS_MEDIUM)]
        else:
            chosen_v = [random.choice(VIOLATIONS_MEDIUM), random.choice(VIOLATIONS_MEDIUM + VIOLATIONS_EASY)]
            # ensure distinct
            if chosen_v[0]["id"] == chosen_v[1]["id"]:
                chosen_v = [chosen_v[0]]
                
        dieu_khoan = []
        for v in chosen_v:
            dieu_khoan.append({
                "ten_dieu_khoan": v["ten_dieu_khoan"],
                "noi_dung_van_ban": v["noi_dung_van_ban"],
                "loai_sai_pham": v["loai_sai_pham"],
                "giai_thich_phap_ly": v["giai_thich_phap_ly"]
            })
            
        dataset.append({
            "sample_id": sample_id,
            "metadata": {
                "ben_cho_thue": random_person(is_female=random.choice([True, False])),
                "ben_thue": random_person(is_female=random.choice([True, False])),
                "tai_san_thue": random_property()
            },
            "dieu_khoan_vi_pham": dieu_khoan,
            "danh_gia_tong_the": generate_overall_assessment(chosen_v)
        })

    # Tier KHÓ & PHỐI HỢP PHỨC TẠP (35 mẫu)
    for _ in range(35):
        sample_id = f"HD_{sample_counter:03d}"
        sample_counter += 1
        num_v = random.choice([1, 2, 3])
        if num_v == 1:
            chosen_v = [random.choice(VIOLATIONS_HARD)]
        elif num_v == 2:
            chosen_v = [random.choice(VIOLATIONS_HARD), random.choice(VIOLATIONS_HARD + VIOLATIONS_MEDIUM)]
            if chosen_v[0]["id"] == chosen_v[1]["id"]:
                chosen_v = [chosen_v[0]]
        else:
            chosen_v = [random.choice(VIOLATIONS_HARD), random.choice(VIOLATIONS_MEDIUM), random.choice(VIOLATIONS_HARD)]
            # make unique by id
            unique_dict = {v["id"]: v for v in chosen_v}
            chosen_v = list(unique_dict.values())
            
        dieu_khoan = []
        for v in chosen_v:
            dieu_khoan.append({
                "ten_dieu_khoan": v["ten_dieu_khoan"],
                "noi_dung_van_ban": v["noi_dung_van_ban"],
                "loai_sai_pham": v["loai_sai_pham"],
                "giai_thich_phap_ly": v["giai_thich_phap_ly"]
            })
            
        dataset.append({
            "sample_id": sample_id,
            "metadata": {
                "ben_cho_thue": random_person(is_female=random.choice([True, False])),
                "ben_thue": random_person(is_female=random.choice([True, False])),
                "tai_san_thue": random_property()
            },
            "dieu_khoan_vi_pham": dieu_khoan,
            "danh_gia_tong_the": generate_overall_assessment(chosen_v)
        })
        
    return dataset

if __name__ == "__main__":
    random.seed(42)  # Cố định seed để tái lập kết quả
    data = generate_dataset(120)
    
    output_path = os.path.join("data", "golden_dataset_120.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Da tao thanh cong {len(data)} bo du lieu tai: {output_path}")
    
    # Thống kê nhanh
    total_samples = len(data)
    clean_count = sum(1 for d in data if len(d["dieu_khoan_vi_pham"]) == 0)
    has_violations = total_samples - clean_count
    total_violation_clauses = sum(len(d["dieu_khoan_vi_pham"]) for d in data)
    
    print(f"- Tong so mau: {total_samples}")
    print(f"- Mau hop dong sach (Clean/0 loi): {clean_count}")
    print(f"- Mau co dieu khoan vi pham: {has_violations}")
    print(f"- Tong so dieu khoan vi pham duoc gieo: {total_violation_clauses}")
