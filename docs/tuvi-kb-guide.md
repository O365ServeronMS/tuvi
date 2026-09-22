# Sửa và mở rộng `tuvi-kb`

KB đã xây xong (2026-09): 111 thẻ sao, 364 thẻ cung, 22 cách cục, 63 thẻ hạn,
39 quy tắc, 325 thẻ phú, trên tầng nguyên văn 664 khúc của 4 sách. Tài liệu này
dành cho việc **sửa hoặc thêm thẻ** về sau, không phải cho việc xây lại từ đầu.

Lịch sử xây dựng (đề xuất cấu trúc, lộ trình 10 lô) nằm trong git history:
`git show 3099ef9:docs/tuvi-kb-proposal.md` và các commit của nhánh
`SteveJobs/tu-vi-output-optimization-61dfc0`.

Quy tắc hình thức mà validator kiểm — frontmatter, thứ tự mục bắt buộc theo
từng type, nhãn nguồn, dạng trích dẫn, kích thước — nằm ở
[`output/claude/tuvi-kb/_meta/schema.md`](../output/claude/tuvi-kb/_meta/schema.md).
**Đọc file đó trước.** Ở đây chỉ ghi những thứ schema không nói: cách làm việc,
các bẫy đã gặp, và các quyết định đã chốt.

## 1. Ba lệnh dùng suốt

Luôn đặt `PYTHONIOENCODING=utf-8` (console Windows mặc định cp1252 sẽ vỡ).
Chỉ cần Python 3, không thư viện ngoài.

```bash
# Gom nguyên văn cần đọc vào một file scratch (frontmatter đã bỏ), rồi đọc bằng Read
PYTHONIOENCODING=utf-8 python3 scripts/dump_chunks.py <scratch>/doc.md tb#0039-anh-huong-cua-nhung-sao-toa-thu-tai-cung-menh-p01 'tran-doan/0050-*'

# Liệt kê id + tiêu đề khúc của một sách, hoặc tìm khúc chứa một cụm từ
PYTHONIOENCODING=utf-8 python3 scripts/dump_chunks.py --list tb
PYTHONIOENCODING=utf-8 python3 scripts/dump_chunks.py --grep "Tử Tức"

# Kiểm tra sau khi sửa (exit 1 nếu có lỗi). Kiểm riêng một thư mục hoặc file cũng được.
PYTHONIOENCODING=utf-8 python3 scripts/validate_kb.py
PYTHONIOENCODING=utf-8 python3 scripts/validate_kb.py output/claude/tuvi-kb/20-palaces/menh-than --no-coverage

# Sinh lại bảng tra sau khi frontmatter đổi
PYTHONIOENCODING=utf-8 python3 scripts/build_lookup.py
```

Mã sách: `tb` Tân Biên, `tl` Thiên Lương, `td` Trần Đoàn, `npl` Nguyễn Phát Lộc.

## 2. Quy trình sửa hoặc thêm thẻ

1. Dump đúng các khúc cần, không dump thừa; file scratch nên dưới 40 KB.
2. **Đọc scratch bằng Read, rồi copy trích dẫn từ đó.** Không gõ lại từ trí nhớ —
   validator so khớp chuỗi với nguyên văn, sai một dấu là hỏng.
3. Viết cả lô thẻ trong một lượt (nhiều lệnh Write trong cùng một phản hồi).
4. Chạy validator trên thư mục vừa viết với `--no-coverage`. Sửa đúng dòng lỗi
   báo. Xem bytes thật khi trích dẫn không khớp:
   `grep -n -o -E ".{20}<vài chữ>.{40}" output/claude/tuvi-kb/90-source/<sách>/<file>.md | cat -A`
5. Chạy validator toàn bộ (không `--no-coverage`) để cập nhật `_meta/coverage.json`.
   Chạy `build_lookup.py` nếu frontmatter đổi.
6. `rm -rf scripts/__pycache__` rồi commit.

Không đọc lại thẻ vừa viết để "kiểm tra"; validator làm việc đó. Nhưng validator
chỉ kiểm hình thức và trích dẫn, **không kiểm ý** — sau một lô lớn nên để người
dùng xem ngẫu nhiên 5 thẻ.

Thêm thẻ mới thì `primary` phải là tập con không rỗng của `[tb, tl]`. Sách nào
không bàn về đề tài thì không đưa vào `cross`, và viết một câu thường (không
gạch đầu dòng, nên không cần nhãn) trong mục Đối chứng, ví dụ:
`Sách Trần Đoàn không bàn cách này; chưa đối chiếu Nguyễn Phát Lộc.`

## 3. Bẫy trích dẫn đã gặp (tốn thời gian nhất)

- Bản OCR hay có khoảng trắng trước dấu chấm: `...bất hạnh .` Nếu trích cả câu,
  hoặc chép đúng ` .`, hoặc dừng trước dấu chấm. **Cách an toàn: kết thúc trích
  dẫn ở chữ cuối, không lấy dấu câu cuối.**
- Dấu phẩy có khoảng trắng trước: `Tỵ Hợi , Vũ Sát` phải chép y nguyên.
- Khúc có dòng bắt đầu bằng `## ` do OCR biến câu giữa chừng thành heading. Trích
  dẫn đi xuyên qua dòng đó phải cắt bằng `[...]` ở chỗ `##`, vì `## ` nằm trong
  nội dung khúc. Trích bắt đầu ngay sau `## ` thì không sao.
- Ngắt dòng giữa câu trong khúc không thành vấn đề (validator gộp khoảng trắng).
- Lỗi chính tả trong sách phải chép nguyên (`Thiến Tướng`, `Đặt biệt`, `Một tọa
  thủ` thay vì Mộ). Không sửa trong trích dẫn; diễn đạt đúng ở phần gạch đầu dòng.
- Dấu nháy cong `"Đức"` trong khúc: chép nguyên, validator chấp nhận.
- Bỏ các đoạn có ký tự OCR tách chữ kiểu `liên quanđ ến`; chọn câu khác để trích.

## 4. Quyết định đã chốt, không mở lại

- Nguồn chính là Tân Biên và Thiên Lương; Trần Đoàn và Nguyễn Phát Lộc chỉ đối chứng.
- Khi hai nguồn chính khác nhau, ghi cả hai với nhãn riêng, không chọn thay người dùng.
- **Không viết module an sao.** Lá số đến từ ảnh người dùng đã xác nhận.
- Không sửa tầng nguyên văn `90-source/` (sinh bởi `chunk_sources.py`, id ổn định).
- Không đổi schema. Nếu schema thiếu, ghi đề xuất vào file này rồi làm theo schema hiện có.
- Slug tiếng Việt không dấu, chữ thường, gạch nối. Địa chi: `ty, suu, dan, mao,
  thin, ti` (Tỵ)`, ngo, mui, than, dau, tuat, hoi`.
- Sao trùng tên: Quan Phù vòng Thái Tuế là `quan-phu`; Quan Phủ vòng Lộc Tồn là
  `quan-phu-loc-ton`; sao Phúc Đức là `phuc-duc-tinh` (phân biệt với cung
  `phuc-duc`); Tử vòng Tràng Sinh là `tu`.
- Trong Tân Biên, "Lộc" ở mục Tứ Hóa là Hóa Lộc, ở "Lộc Tồn" mới là Lộc Tồn;
  "Lộc, Mã" đi cặp thường là Lộc Tồn. Khi không rõ, **chọn theo ngữ cảnh và ghi
  chú trong Điều kiện** — ghi cả hai id vào `stars` là sai.
- Thẻ cung: `palace: [menh, than]` khi Tân Biên viết chung "cung Mệnh, Thân";
  `[menh]` khi văn bản nói riêng cung Mệnh. Thư mục luôn là `menh-than`.
  `positions` chỉ điền khi thẻ nói riêng vị trí (ví dụ Tử Tham chỉ ở Mão Dậu).
