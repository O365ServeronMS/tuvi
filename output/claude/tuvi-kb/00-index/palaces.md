# Sổ đăng ký cung

Bảng này là nguồn duy nhất cho id cung. Script `chunk_sources.py` dùng cột `aliases` để dò tên cung trong nguyên văn, `validate_kb.py` dùng cột `id` và `thư mục` để kiểm tra thẻ.

- `id`: slug ASCII dùng trong frontmatter và tên file.
- `aliases`: các cách gọi đủ rõ để dò tự động, cách nhau bằng `;`.
- `thư mục`: thư mục con trong `20-palaces/`. Mệnh và Thân dùng chung một thư mục vì Tân Biên luận chung.
- `dò`: `x` nếu cho phép dò tự động trong nguyên văn.

| id | tên | aliases | thư mục | dò | ghi chú |
|---|---|---|---|---|---|
| menh | Mệnh | cung Mệnh; Mệnh viên; Mệnh cung; thủ Mệnh; Mệnh Thân | menh-than | x | "Mệnh" đứng một mình quá phổ biến nên không dò |
| than | Thân | cung Thân; Thân cung; Thân cư; Mệnh Thân | menh-than | x | "Thân" trùng địa chi Thân nên chỉ dò cụm |
| phu-mau | Phụ Mẫu | cung Phụ Mẫu; Phụ Mẫu | phu-mau | x | |
| phuc-duc | Phúc Đức | cung Phúc Đức; Phúc Đức | phuc-duc | x | Trùng tên sao Phúc Đức (id sao: phuc-duc-tinh) |
| dien-trach | Điền Trạch | cung Điền Trạch; Điền Trạch; cung Điền | dien-trach | x | |
| quan-loc | Quan Lộc | cung Quan Lộc; Quan Lộc; cung Quan | quan-loc | x | |
| no-boc | Nô Bộc | cung Nô Bộc; Nô Bộc; cung Nô | no-boc | x | |
| thien-di | Thiên Di | cung Thiên Di; Thiên Di | thien-di | x | |
| tat-ach | Tật Ách | cung Tật Ách; Tật Ách; cung Tật | tat-ach | x | |
| tai-bach | Tài Bạch | cung Tài Bạch; Tài Bạch; cung Tài | tai-bach | x | |
| tu-tuc | Tử Tức | cung Tử Tức; Tử Tức; cung Tử | tu-tuc | x | |
| phu-the | Phu Thê | cung Phu Thê; Phu Thê; Thê Thiếp; Phu Quân; cung Thê; cung Phu | phu-the | x | Tân Biên gọi là Thê Thiếp (Phu Quân) |
| huynh-de | Huynh Đệ | cung Huynh Đệ; Huynh Đệ; cung Bào | huynh-de | x | |
