# Skill: luận giải lá số Tử Vi bằng knowledge base `tuvi-kb`

Skill này dùng knowledge base trong thư mục này (`00-index/` đến `60-phu/`)
để luận giải một lá số cụ thể. Đặt ở `output/tuvi-kb/SKILL.md` để có thể
copy hoặc symlink vào `.claude/skills/tuvi/` mà không cần sửa gì.

## Ràng buộc bắt buộc (không được bỏ qua)

1. **Luôn in bảng chuẩn hoá lá số cho người dùng xác nhận trước khi luận
   giải bất cứ điều gì.** Không tự suy luận tiếp nếu người dùng chưa xác
   nhận hoặc chưa sửa bảng. Đây không phải bước tuỳ chọn.
2. **Mọi nhận định trong bài luận phải ghi nhãn nguồn** (`[TB]`, `[TL]`,
   `[TĐ]`, `[NPL]`) như trong thẻ gốc — sao chép nguyên nhãn khi trích dẫn
   một gạch đầu dòng của thẻ. Không nêu điều gì không có trong thẻ; nếu tự
   suy diễn thêm (ví dụ khớp hai thẻ với nhau) thì phải nói rõ đó là suy
   diễn của Claude, không phải nguyên văn sách.
3. **Khi Tân Biên (`[TB]`) và Thiên Lương (`[TL]`) nói khác nhau về cùng
   một điểm, nêu cả hai, không tự chọn thay người dùng.** Trần Đoàn
   (`[TĐ]`) và Nguyễn Phát Lộc (`[NPL]`) chỉ là đối chứng — không dùng
   để phủ quyết khi TB/TL đã có ý kiến, chỉ nêu thêm nếu người dùng muốn
   xem đối chiếu.

## Quy trình 7 bước

### Bước 1 — Đọc ảnh và in bảng chuẩn hoá (bắt buộc dừng lại chờ xác nhận)

Đọc ảnh lá số theo hướng dẫn ở [`00-index/chart-reading.md`](00-index/chart-reading.md).
Xuất ra một bảng gồm:

- Tuổi (can chi năm sinh), âm/dương nam/nữ.
- Cục (Ngũ Hành Cục).
- Mệnh ở cung nào, Thân ở cung nào.
- Mỗi cung trong 12 cung: tên cung, các sao tọa thủ kèm miếu/hãm, có Tuần
  hoặc Triệt án ngữ hay không.
- Các mốc Đại Hạn (tuổi bắt đầu mỗi cung).

In bảng này ra cho người dùng đọc và **hỏi xác nhận đúng/sai** trước khi đi
tiếp. Nếu ảnh mờ, thiếu, hoặc người dùng sửa lại, dừng ở đây cho đến khi có
bảng đã xác nhận. Sai một ô trong bảng này (đọc nhầm sao, nhầm miếu hãm) làm
sai toàn bộ phần luận phía sau, nên không được bỏ qua bước xác nhận.

### Bước 2 — Chuẩn hoá tên sao sang id

Dùng bảng alias trong [`00-index/stars.md`](00-index/stars.md) để đổi mọi
tên sao (kể cả viết tắt) trong bảng đã xác nhận sang id chuẩn (`tu-vi`,
`thien-phu`, `kinh-duong`...). Đây là khoá dùng để tra `lookup.md`.

### Bước 3 — Luận Mệnh, Thân

Với cung Mệnh và cung Thân:

1. Tra [`00-index/lookup.md`](00-index/lookup.md) (bảng "Sao → thẻ sao" và
   phần "(Cung, bộ sao) → thẻ cung", tách riêng ở
   [`00-index/lookup-palaces.md`](00-index/lookup-palaces.md) nếu quá lớn để
   nhúng) để lấy thẻ chính tinh và thẻ bộ sao đồng cung tương ứng trong
   `20-palaces/menh-than/`.
2. Tra `30-combos/` xem bộ sao có khớp cách cục nào không (bảng "Cách cục →
   thẻ combo" trong `lookup.md`).
3. Tra `50-rules/` về quy tắc chính diệu/sao hội chiếu theo hướng chiếu
   (tam hợp, xung chiếu, nhị hợp, giáp cung).

### Bước 4 — Luận 11 cung còn lại

Lặp lại cách làm ở Bước 3 cho từng cung trong 11 cung còn lại (thư mục
tương ứng trong `20-palaces/`), ưu tiên cung mà người dùng hỏi trước nếu
họ chỉ hỏi một vài cung cụ thể thay vì toàn bộ lá số.

### Bước 5 — Áp dụng quy tắc Thiên Lương

Tra `50-rules/` các quy tắc riêng của Thiên Lương áp dụng cho toàn lá số,
không riêng một cung: vòng Thái Tuế, vòng Lộc Tồn, vòng Tràng Sinh theo
tuổi; nguyên tắc nhị hợp; và nguyên tắc "chính không bằng chiếu" (sao tọa
thủ có trọng lượng khác sao chỉ hội chiếu).

### Bước 6 — Hạn

Tra `40-han/` theo sao nhập hạn tại cung đang xét ở Đại Hạn/Tiểu Hạn hiện
tại, và các thẻ liên hệ giữa Đại Hạn/Tiểu Hạn với Mệnh Thân.

### Bước 7 — Viết luận giải

Viết bài luận từ các thẻ đã tra ở Bước 3–6, tuân thủ đúng 3 ràng buộc bắt
buộc ở đầu tài liệu này (nhãn nguồn trên từng nhận định; nêu cả hai khi TB
và TL khác nhau; không suy diễn ngoài thẻ mà không nói rõ).
