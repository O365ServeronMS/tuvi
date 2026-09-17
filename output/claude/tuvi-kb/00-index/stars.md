# Sổ đăng ký sao

Bảng này là nguồn duy nhất cho id sao. Mọi thẻ trong `10-stars/` đến `60-phu/` chỉ được dùng id có trong bảng. Bản này là **bản nháp khởi tạo** từ mục 3 Tân Biên và mục lục sao của Trần Đoàn; cần rà lại cột `aliases`, `viết tắt` và miếu hãm khi làm lô thẻ sao.

Quy ước cột:

- `id`: slug ASCII không dấu, dùng trong frontmatter, tên file, grep.
- `tên`: tên đầy đủ có dấu như Tân Biên viết.
- `aliases`: cách gọi khác đủ rõ để dò tự động trong nguyên văn, cách nhau bằng `;`. Dò không phân biệt dấu; alias một chữ dò phân biệt hoa thường (chỉ khớp khi viết hoa như tên sao). Cụm nhiều chữ được dò trước và che đi, nên "Tử" không khớp trong "Tử Tức".
- `viết tắt`: cách viết trên web hoặc trong sách quá ngắn, mơ hồ, **không** dùng để dò tự động; SKILL dùng khi đọc ảnh lá số.
- `nhóm`: chinh-tinh, luc-sat, tu-hoa, luc-cat, vong-loc-ton, vong-thai-tue, vong-trang-sinh, tuan-triet, phu-tinh.
- `dò`: `x` nếu cho phép dò tự động.

Sao lưu (lưu Thái Tuế, lưu Kình Dương...) không có hàng riêng: thẻ hạn dùng id `luu-<id>` và validator chấp nhận nếu `<id>` có trong bảng.

| id | tên | aliases | viết tắt | nhóm | hành | âm dương | dò | ghi chú |
|---|---|---|---|---|---|---|---|---|
| tu-vi | Tử Vi | Đế tinh | Tử; T.Vi | chinh-tinh | Thổ | Dương | x | Nam Bắc Đẩu tinh, Đế tinh |
| liem-trinh | Liêm Trinh | | Liêm; L.Trinh | chinh-tinh | Hỏa | Âm | x | Tù tinh, Đào Hoa thứ hai |
| thien-dong | Thiên Đồng | | Đồng; T.Đồng | chinh-tinh | Thủy | Dương | x | Phúc tinh |
| vu-khuc | Vũ Khúc | | Vũ; V.Khúc | chinh-tinh | Kim | Âm | x | Tài tinh |
| thai-duong | Thái Dương | Nhật | T.Dương | chinh-tinh | Hỏa | Dương | x | Quý tinh; biểu tượng cha, chồng |
| thien-co | Thiên Cơ | | Cơ; T.Cơ | chinh-tinh | Mộc | Âm | x | Thiện tinh |
| thien-phu | Thiên Phủ | | Phủ; T.Phủ | chinh-tinh | Thổ | Âm | x | Tài tinh, Quyền tinh; "Phủ" một chữ mơ hồ với Quan Phủ, Đường Phù |
| thai-am | Thái Âm | Nguyệt | T.Âm | chinh-tinh | Thủy | Âm | x | Phú tinh; biểu tượng mẹ, vợ |
| tham-lang | Tham Lang | | Tham; T.Lang | chinh-tinh | Thủy | Âm | x | Hung tinh, Dâm tinh |
| cu-mon | Cự Môn | | Cự; C.Môn | chinh-tinh | Thủy | Âm | x | Ám tinh |
| thien-tuong | Thiên Tướng | | Tướng; T.Tướng | chinh-tinh | Thủy | Dương | x | Quyền tinh; "Tướng" một chữ mơ hồ với Tướng Quân |
| thien-luong | Thiên Lương | | Lương; T.Lương | chinh-tinh | Mộc | Âm | x | Thọ tinh, Ấm tinh; trùng bút danh tác giả Thiên Lương |
| that-sat | Thất Sát | | Sát; T.Sát | chinh-tinh | Kim | Dương | x | Quyền tinh, Dũng tinh; "Sát" một chữ mơ hồ với sát tinh |
| pha-quan | Phá Quân | | Phá; P.Quân | chinh-tinh | Thủy | Âm | x | Hung tinh, Hao tinh |
| kinh-duong | Kình Dương | Dương Nhận; Kình | K.Dương | luc-sat | Kim | Dương | x | Kim đới Hỏa |
| da-la | Đà La | Đa La; Đà | Đ.La | luc-sat | Kim | Âm | x | |
| hoa-tinh | Hỏa Tinh | Hỏa; Hoả | H.Tinh | luc-sat | Hỏa | Dương | x | Hỏa đới Kim; "Hỏa" một chữ mơ hồ với hành Hỏa, chỉ dò khi viết hoa đúng dấu |
| linh-tinh | Linh Tinh | Linh | L.Tinh | luc-sat | Hỏa | Âm | x | |
| dia-khong | Địa Không | | Không; Đ.Không | luc-sat | Hỏa | Âm | x | Sát tinh; "Không" mơ hồ với Thiên Không, Tuần Triệt |
| dia-kiep | Địa Kiếp | | Kiếp; Đ.Kiếp | luc-sat | Hỏa | Dương | x | Sát tinh; "Kiếp" mơ hồ với Kiếp Sát |
| hoa-loc | Hóa Lộc | | Lộc; H.Lộc | tu-hoa | Mộc | | x | "Lộc" mơ hồ với Lộc Tồn, thẻ phải ghi id đầy đủ |
| hoa-quyen | Hóa Quyền | | Quyền; H.Quyền | tu-hoa | Mộc | | x | |
| hoa-khoa | Hóa Khoa | | Khoa; H.Khoa | tu-hoa | Mộc | | x | |
| hoa-ky | Hóa Kỵ | Hóa Kị | Kỵ; Kị; H.Kỵ | tu-hoa | Thủy | | x | Trần Đoàn viết Hoá Kị |
| van-xuong | Văn Xương | | Xương; V.Xương | luc-cat | Kim | Dương | x | |
| van-khuc | Văn Khúc | | Khúc; V.Khúc | luc-cat | Thủy | Âm | x | |
| thien-khoi | Thiên Khôi | | Khôi; T.Khôi | luc-cat | Hỏa | Dương | x | |
| thien-viet | Thiên Việt | | Việt; T.Việt | luc-cat | Hỏa | Âm | x | |
| ta-phu | Tả Phụ | Tả Phù | Tả; T.Phụ | luc-cat | Thổ | Dương | x | |
| huu-bat | Hữu Bật | | Hữu; H.Bật | luc-cat | Thổ | Dương | x | |
| loc-ton | Lộc Tồn | | Lộc; L.Tồn | vong-loc-ton | Thổ | Dương | x | Quý tinh; "Lộc" mơ hồ với Hóa Lộc |
| bac-sy | Bác Sỹ | Bác Sĩ | B.Sỹ | vong-loc-ton | Thủy | | x | |
| luc-sy | Lực Sỹ | Lực Sĩ | L.Sỹ | vong-loc-ton | Hỏa | | x | |
| thanh-long | Thanh Long | | T.Long | vong-loc-ton | Thủy | | x | |
| tieu-hao | Tiểu Hao | | T.Hao | vong-loc-ton | Hỏa | | x | Bại tinh; Song Hao = Đại Hao + Tiểu Hao |
| tuong-quan | Tướng Quân | | T.Quân | vong-loc-ton | Mộc | | x | |
| tau-thu | Tấu Thư | | T.Thư | vong-loc-ton | Kim | | x | |
| phi-liem | Phi Liêm | | P.Liêm | vong-loc-ton | Hỏa | | x | |
| hy-than | Hỷ Thần | Hỉ Thần | H.Thần | vong-loc-ton | Hỏa | | x | |
| benh-phu | Bệnh Phù | | B.Phù | vong-loc-ton | Thổ | | x | |
| dai-hao | Đại Hao | | Đ.Hao | vong-loc-ton | Hỏa | | x | Bại tinh |
| phuc-binh | Phục Binh | | P.Binh | vong-loc-ton | Hỏa | | x | |
| quan-phu-loc-ton | Quan Phủ | | Q.Phủ | vong-loc-ton | Hỏa | | | Vòng Lộc Tồn. Không dò tự động vì bỏ dấu trùng "Quan Phù" vòng Thái Tuế (Tân Biên 3.73 cũng viết Quan Phù); thẻ phải phân giải theo ngữ cảnh vòng sao |
| thai-tue | Thái Tuế | | T.Tuế | vong-thai-tue | Hỏa | | x | |
| thieu-duong | Thiếu Dương | | T.Dương | vong-thai-tue | Hỏa | | x | |
| tang-mon | Tang Môn | Tang | T.Môn | vong-thai-tue | Mộc | | x | Bại tinh |
| thieu-am | Thiếu Âm | | T.Âm | vong-thai-tue | Thủy | | x | |
| quan-phu | Quan Phù | | Q.Phù | vong-thai-tue | Hỏa | | x | Vòng Thái Tuế (Tân Biên 3.60) |
| tu-phu | Tử Phù | | T.Phù | vong-thai-tue | Hỏa | | x | |
| tue-pha | Tuế Phá | | T.Phá | vong-thai-tue | Hỏa | | x | |
| long-duc | Long Đức | | L.Đức | vong-thai-tue | Thủy | | x | |
| bach-ho | Bạch Hổ | Hổ | B.Hổ | vong-thai-tue | Kim | | x | Bại tinh |
| phuc-duc-tinh | Phúc Đức | | P.Đức | vong-thai-tue | Thổ | | | Sao Phúc Đức; không dò vì trùng tên cung Phúc Đức |
| dieu-khach | Điếu Khách | | Đ.Khách | vong-thai-tue | Hỏa | | x | |
| truc-phu | Trực Phù | | Tr.Phù | vong-thai-tue | Hỏa | | x | |
| trang-sinh | Tràng Sinh | Trường Sinh | Tr.Sinh | vong-trang-sinh | Thủy | | x | |
| moc-duc | Mộc Dục | | M.Dục | vong-trang-sinh | Thủy | | x | |
| quan-doi | Quan Đới | | Q.Đới | vong-trang-sinh | Kim | | x | |
| lam-quan | Lâm Quan | | L.Quan | vong-trang-sinh | Kim | | x | |
| de-vuong | Đế Vượng | | Đ.Vượng | vong-trang-sinh | Kim | | x | |
| suy | Suy | | | vong-trang-sinh | Thủy | | | Tên một chữ, không dò |
| benh | Bệnh | | | vong-trang-sinh | Hỏa | | | Tên một chữ, không dò |
| tu | Tử | | | vong-trang-sinh | Thủy | | | Tên một chữ, không dò; mơ hồ với Tử Vi |
| mo | Mộ | | | vong-trang-sinh | Thổ | | | Tên một chữ, không dò |
| tuyet | Tuyệt | | | vong-trang-sinh | Thổ | | | Tên một chữ, không dò |
| thai | Thai | | | vong-trang-sinh | Thổ | | | Tên một chữ, không dò; mơ hồ với Tam Thai, Thai Phụ |
| duong | Dưỡng | | | vong-trang-sinh | Mộc | | | Tên một chữ, không dò |
| tuan | Tuần | Tuần Trung Không Vong; Tuần Không | | tuan-triet | | | x | |
| triet | Triệt | Triệt Lộ Không Vong; Triệt Không | | tuan-triet | | | x | |
| thien-khong | Thiên Không | | T.Không | phu-tinh | Hỏa | | x | |
| thien-ma | Thiên Mã | Mã | T.Mã | phu-tinh | Hỏa | | x | |
| thien-hinh | Thiên Hình | Hình | T.Hình | phu-tinh | Hỏa | | x | "Hình" mơ hồ với hình ngục, chỉ dò khi viết hoa |
| thien-rieu | Thiên Riêu | Riêu; Thiên Diêu | T.Riêu | phu-tinh | Thủy | | x | |
| thien-y | Thiên Y | | T.Y | phu-tinh | Thủy | | x | |
| long-tri | Long Trì | | L.Trì | phu-tinh | Thủy | | x | Long Phượng = Long Trì + Phượng Các |
| phuong-cac | Phượng Các | Phụng Các | P.Các | phu-tinh | Mộc | | x | |
| tam-thai | Tam Thai | | T.Thai | phu-tinh | Thủy | | x | Thai Tọa = Tam Thai + Bát Tọa |
| bat-toa | Bát Tọa | | B.Tọa | phu-tinh | Mộc | | x | |
| an-quang | Ân Quang | | Â.Quang | phu-tinh | Mộc | | x | Quang Quý = Ân Quang + Thiên Quý |
| thien-quy | Thiên Quý | | T.Quý | phu-tinh | Thổ | | x | |
| dao-hoa | Đào Hoa | Đào | Đ.Hoa | phu-tinh | Mộc | | x | |
| hong-loan | Hồng Loan | Hồng | H.Loan | phu-tinh | Thủy | | x | Hồng Hỷ = Hồng Loan + Thiên Hỷ |
| thien-hy | Thiên Hỷ | Thiên Hỉ | T.Hỷ | phu-tinh | Thủy | | x | |
| thai-phu | Thai Phụ | | Th.Phụ | phu-tinh | Kim | | x | Thai Cáo = Thai Phụ + Phong Cáo |
| phong-cao | Phong Cáo | | P.Cáo | phu-tinh | Thổ | | x | |
| quoc-an | Quốc Ấn | | Q.Ấn | phu-tinh | Thổ | | x | Ấn Phù = Quốc Ấn + Đường Phù |
| duong-phu | Đường Phù | Đường Phú | Đ.Phù | phu-tinh | Mộc | | x | |
| thien-tho | Thiên Thọ | | T.Thọ | phu-tinh | Thổ | | x | Tài Thọ = Thiên Tài + Thiên Thọ |
| luu-nien-van-tinh | Lưu Niên Văn Tinh | | L.N.V.Tinh | phu-tinh | Hỏa | | x | |
| hoa-cai | Hoa Cái | | H.Cái | phu-tinh | Kim | | x | |
| thien-tru | Thiên Trù | | T.Trù | phu-tinh | Thổ | | x | |
| thien-quan | Thiên Quan | Thiên Quan Quý Nhân | T.Quan | phu-tinh | Hỏa | | x | |
| thien-phuc | Thiên Phúc | Thiên Phúc Quý Nhân | T.Phúc | phu-tinh | Thổ | | x | |
| thien-giai | Thiên Giải | | T.Giải | phu-tinh | Hỏa | | x | |
| dia-giai | Địa Giải | | Đ.Giải | phu-tinh | Thổ | | x | |
| giai-than | Giải Thần | | G.Thần | phu-tinh | Mộc | | x | |
| thien-duc | Thiên Đức | | T.Đức | phu-tinh | Hỏa | | x | |
| nguyet-duc | Nguyệt Đức | | N.Đức | phu-tinh | Hỏa | | x | |
| co-than | Cô Thần | | C.Thần | phu-tinh | Thổ | | x | Cô Quả = Cô Thần + Quả Tú |
| qua-tu | Quả Tú | | Q.Tú | phu-tinh | Thổ | | x | |
| dau-quan | Đẩu Quân | Đầu Quân | Đ.Quân | phu-tinh | Hỏa | | x | Trần Đoàn viết Đầu Quân |
| thien-thuong | Thiên Thương | | T.Thương | phu-tinh | Thổ | | x | Thương Sứ = Thiên Thương + Thiên Sứ |
| thien-su | Thiên Sứ | | T.Sứ | phu-tinh | Thủy | | x | |
| kiep-sat | Kiếp Sát | | K.Sát | phu-tinh | Hỏa | | x | |
| luu-ha | Lưu Hà | | L.Hà | phu-tinh | Thủy | | x | |
| pha-toai | Phá Toái | | P.Toái | phu-tinh | Hỏa | | x | |
| thien-tai | Thiên Tài | | T.Tài | phu-tinh | Thổ | | x | |
| thien-la | Thiên La | | T.La | phu-tinh | Thổ | | x | La Võng = Thiên La + Địa Võng; vị trí cố định Thìn |
| dia-vong | Địa Võng | | Đ.Võng | phu-tinh | Thổ | | x | Vị trí cố định Tuất |
| thien-khoc | Thiên Khốc | Khốc | T.Khốc | phu-tinh | Thủy | | x | Bại tinh; Khốc Hư = Thiên Khốc + Thiên Hư |
| thien-hu | Thiên Hư | Hư | T.Hư | phu-tinh | Thủy | | x | Bại tinh |
