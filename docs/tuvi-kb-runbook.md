# Runbook tuvi-kb: các lô còn lại (giao cho Sonnet)

Tài liệu này tự chứa. Người thực hiện không cần đọc lịch sử phiên trước. Đọc thêm [tuvi-kb-proposal.md](tuvi-kb-proposal.md) (thiết kế) và [output/tuvi-kb/_meta/schema.md](../output/tuvi-kb/_meta/schema.md) (schema mà validator kiểm) trước khi bắt đầu.

## 0. Trạng thái hiện tại (2026-09-14)

| Thứ | Trạng thái |
|---|---|
| Tầng nguyên văn `output/tuvi-kb/90-source/` | Xong. 664 khúc, 4 sách, id ổn định, không mất ký tự. Không sửa tay. |
| Sổ đăng ký `00-index/stars.md`, `palaces.md` | Xong, 111 sao, 13 cung. Cột alias là bản nháp, được phép sửa nếu phát hiện sai. |
| Thẻ sao `10-stars/` | Xong 111/111, validator sạch. |
| Thẻ cung `20-palaces/` | Mới có 1 thẻ mẫu `menh-than/tu-vi+tham-lang.md`. **Đây là lô kế tiếp.** |
| `30-combos/`, `40-han/`, `50-rules/`, `60-phu/` | Chưa có gì. |
| `00-index/lookup.md`, `chart-reading.md`, `SKILL.md`, `scripts/build_lookup.py` | Chưa có. |
| Script | `scripts/chunk_sources.py` (không cần chạy lại), `scripts/validate_kb.py`, `scripts/dump_chunks.py`. Chỉ cần Python 3, không thư viện ngoài. |

Nhánh làm việc: `SteveJobs/tu-vi-output-optimization-61dfc0`. Mỗi lô là một commit riêng.

## 1. Ba lệnh dùng suốt

Luôn đặt `PYTHONIOENCODING=utf-8` (console Windows mặc định cp1252 sẽ vỡ).

```bash
# Gom nguyên văn cần đọc vào một file scratch (frontmatter đã bỏ), rồi đọc bằng Read
PYTHONIOENCODING=utf-8 python scripts/dump_chunks.py <scratch>/lo4a.md tb#0039-anh-huong-cua-nhung-sao-toa-thu-tai-cung-menh-p01 'tran-doan/0050-*'

# Liệt kê id + tiêu đề khúc của một sách, hoặc tìm khúc chứa một cụm từ
PYTHONIOENCODING=utf-8 python scripts/dump_chunks.py --list tb
PYTHONIOENCODING=utf-8 python scripts/dump_chunks.py --grep "Tử Tức"

# Kiểm tra sau mỗi lô (exit 1 nếu có lỗi). Có thể kiểm riêng một thư mục hoặc file.
PYTHONIOENCODING=utf-8 python scripts/validate_kb.py
PYTHONIOENCODING=utf-8 python scripts/validate_kb.py output/tuvi-kb/20-palaces/menh-than --no-coverage
```

Sau khi validator báo `lỗi: 0`, xoá `scripts/__pycache__` rồi commit:

```bash
rm -rf scripts/__pycache__ && git add -A && git commit -q -F - <<'EOF'
<một dòng mô tả lô>

<2-3 dòng: phạm vi, nguồn, số thẻ>

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>
EOF
```

Không push, không rebase, không đụng `output/gpt_knowledge_merged` và `output/tan-bien`.

## 2. Luật cứng (validator từ chối nếu vi phạm)

1. Mỗi gạch đầu dòng trong thân bài bắt đầu bằng đúng một nhãn `[TB]`, `[TL]`, `[TĐ]`, `[NPL]` rồi một khoảng trắng. Ngoại lệ: các mục Nguyên văn, Phú liên quan, Sao và cung liên quan, Thành phần, Cung áp dụng, Câu phú.
2. Ngoài mục **Đối chứng** chỉ được dùng `[TB]` `[TL]`, và chỉ nhãn có trong `primary`. Trong Đối chứng chỉ được `[TĐ]` `[NPL]`.
3. `primary` là tập con không rỗng của `[tb, tl]`; `cross` là tập con của `[td, npl]`. Sách nào không nói về đề tài thì không đưa vào `cross`, và viết một câu thường (không gạch đầu dòng) trong Đối chứng, ví dụ: `Sách Trần Đoàn không bàn cách này; chưa đối chiếu Nguyễn Phát Lộc.`
4. Mọi id sao phải có trong `stars.md`, id cung trong `palaces.md`. Thẻ hạn được dùng `luu-<id>`.
5. Mỗi thẻ có ít nhất một trích dẫn dạng `> "..." (id-khúc)` trong mục Nguyên văn; id đó phải có trong `chunks` của frontmatter; đoạn trích phải **khớp chuỗi** với khúc sau khi gộp khoảng trắng và bỏ phân biệt hoa thường; tối đa 400 ký tự; được lược bằng `[...]`.
6. Tên file thẻ cung = các id sao nối bằng `+`, đúng thứ tự trong `stars`, chính tinh đứng trước. Id trong frontmatter = `palace:<thư mục cung>:<tên file>`.
7. Không hai thẻ cung nào trùng cả `palace` lẫn `stars`.
8. Thẻ dưới 8 KB.

## 3. Bẫy trích dẫn đã gặp (mất thời gian nhất)

- Bản OCR hay có khoảng trắng trước dấu chấm: `...bất hạnh .` Nếu trích cả câu, hoặc chép đúng ` .`, hoặc dừng trước dấu chấm. **Cách an toàn: kết thúc trích dẫn ở chữ cuối, không lấy dấu câu cuối.**
- Dấu phẩy có khoảng trắng trước: `Tỵ Hợi , Vũ Sát` phải chép y nguyên.
- Khúc có dòng bắt đầu bằng `## ` do OCR biến câu giữa chừng thành heading. Nếu trích dẫn đi xuyên qua dòng đó, phải cắt bằng `[...]` ở chỗ `##`, vì `## ` nằm trong nội dung khúc. Trích bắt đầu ngay sau `## ` thì không sao.
- Ngắt dòng giữa câu trong khúc không thành vấn đề (validator gộp khoảng trắng).
- Lỗi chính tả trong sách phải chép nguyên (`Thiến Tướng`, `Đặt biệt`, `Một tọa thủ` thay vì Mộ). Không sửa trong trích dẫn; diễn đạt đúng ở phần gạch đầu dòng.
- Dấu nháy cong `“Đức”` trong khúc: chép nguyên trong trích dẫn, validator chấp nhận.
- Bỏ các đoạn có ký tự OCR tách chữ kiểu `liên quanđ ến`; chọn câu khác để trích.
- Sau khi dump, **đọc file scratch bằng Read, rồi copy từ đó**. Không gõ lại từ trí nhớ.

## 4. Quy trình một lô (tiết kiệm token)

1. Chọn 10 đến 15 thẻ cho lô. Dump đúng các khúc cần, không dump thừa; file scratch nên dưới 40 KB.
2. Đọc scratch một lần. Ghi ra (trong đầu) danh sách thẻ và các câu sẽ trích.
3. Viết tất cả thẻ của lô trong một lượt (nhiều lệnh Write trong cùng một phản hồi).
4. Chạy validator trên thư mục vừa viết với `--no-coverage`. Sửa đúng dòng lỗi báo. Thường chỉ là trích dẫn; dùng `grep -n -o -E ".{20}<vài chữ>.{40}" output/tuvi-kb/90-source/<sách>/<file>.md | cat -A` để xem bytes thật.
5. Chạy validator toàn bộ (không `--no-coverage`) để cập nhật `_meta/coverage.json`. Commit.
6. Không đọc lại thẻ đã viết để "kiểm tra"; validator làm việc đó.

Mức effort: lô 4 và 5 nên dùng Sonnet **high** (nội dung dày, nhiều quyết định tách thẻ). Lô 7, 9, 10 dùng **medium** được.

## 5. Mẫu thẻ

Mục bắt buộc phải đúng chính tả và thứ tự như dưới. Mục tùy chọn ghi trong ngoặc.

### palace-card (`20-palaces/<cung>/<sao1>+<sao2>.md`)

```markdown
---
id: palace:menh-than:tu-vi
type: palace-card
palace: [menh, than]
stars: [tu-vi]
positions: []
gender: any
tags: []
primary: [tb]
cross: [td]
chunks:
  - tb#0039-anh-huong-cua-nhung-sao-toa-thu-tai-cung-menh-p01
  - td#0050-sao-tu-vi-de-nhat-tinh-tren-bau-troi-cung-menh
---
# Tử Vi tại Mệnh Thân

## Kết luận
- [TB] ...

## Điều kiện và sắc thái
- [TB] Miếu, vượng: ...
- [TB] Nam mệnh: ...
- [TB] Nữ mệnh: ...
- [TB] Gặp Tuần Triệt: ...

## Đối chứng
- [TĐ] ...

## Phú liên quan
- "Tử Vi cư Ngọ, vô Hình Kỵ, Giáp Đinh Kỷ vị chí công khanh" → ghi tạm câu phú và ý giải; thẻ phú riêng làm ở lô 9.

## Nguyên văn
> "..." (tb#0039-...-p01)
```

`palace`: dùng `[menh, than]` khi Tân Biên viết chung "cung Mệnh, Thân"; `[menh]` khi văn bản nói riêng cung Mệnh. Thư mục luôn là `menh-than`. `positions` chỉ điền khi thẻ nói riêng vị trí (ví dụ Tử Tham chỉ ở Mão Dậu). `gender`: `any`, `nam`, `nu`; nếu nội dung chia Nam mệnh/Nữ mệnh trong cùng thẻ thì để `any` và ghi trong Điều kiện.

### combo-card (`30-combos/<slug>.md`, id `combo:<slug>`)

Mục: Thành phần, Điều kiện thành cách, Ý nghĩa, Phá cách, Cung áp dụng, Đối chứng, Nguyên văn. `stars` ít nhất 2 sao. Thành phần và Cung áp dụng không cần nhãn.

### han-card (`40-han/<slug>.md`, id `han:<slug>`)

Mục: Kết luận, Tốt khi, Xấu khi, Kết hợp Mệnh Thân, Đối chứng, Nguyên văn. Sao lưu ghi `luu-thai-tue`, `luu-kinh-duong`...

### rule-card (`50-rules/<slug>.md`, id `rule:<slug>`)

Mục: Điều kiện, Kết luận, Ngoại lệ, Ví dụ trong sách, Khi nào không áp dụng, Nguyên văn (Đối chứng tùy chọn). Một quy tắc một thẻ. Không đưa cả bài Thiên Lương vào một thẻ; tách theo từng mệnh đề "nếu... thì...".

### phu-card (`60-phu/<slug>.md`, id `phu:<slug>`)

Mục: Câu phú, Giải nghĩa, Sao và cung liên quan, Nguồn giải, Nguyên văn. Câu phú và Sao và cung liên quan không cần nhãn; Giải nghĩa ghi nhãn theo sách giải (Tân Biên giải thì `[TB]`).

## 6. Các lô còn lại, kèm id khúc

Dùng `dump_chunks.py --list <sách>` để xem tiêu đề nếu cần; id dưới đây là tiền tố, script tự khớp phần còn lại.

### Lô 4. Thẻ cung Mệnh Thân (ước 60 đến 80 thẻ, chia 5 lô con)

Nguồn chính: Tân Biên mục 4.2, gồm 31 phần `tb#0039-anh-huong-cua-nhung-sao-toa-thu-tai-cung-menh-p01` đến `-p31`. Bảng phần → sao:

| Phần | Nội dung | Phần | Nội dung |
|---|---|---|---|
| p01, p02 | 4.2.1 Tử Vi (p01 có cả Đại cương, Nam, Nữ, Phú giải; p02 tiếp Phú giải) | p17, p18 | 4.2.12 Thiên Lương |
| p03 | 4.2.2 Liêm Trinh | p19 | 4.2.13 Thất Sát (phần đầu nằm cuối p18) |
| p04 | 4.2.3 Thiên Đồng | p20, p21 | 4.2.14 Phá Quân |
| p05, p06 | 4.2.4 Vũ Khúc | p22 | 4.2.14 Xương Khúc (đầu nằm cuối p21) |
| p07, p08, p09 | 4.2.5 Thái Dương (cuối p09 bắt đầu Thiên Cơ) | p23 | 4.2.16 Khôi Việt |
| p10 | 4.2.6 Thiên Cơ, 4.2.7 Thiên Phủ bắt đầu | p24 | 4.2.17 Lộc Tồn |
| p11 | 4.2.8 Thái Âm (Thiên Phủ nằm cuối p10, đầu p11) | p25 | 4.2.18 Tả Hữu |
| p12, p13 | 4.2.9 Tham Lang | p26 | 4.2.19 Kình Dương |
| p14, p15 | 4.2.10 Cự Môn | p27 | 4.2.20 Đà La, 4.2.21 Hỏa Linh |
| p16 | 4.2.11 Thiên Tướng | p28 | 4.2.22 Không Kiếp |
| | | p29, p30 | 4.2.23 Tứ Hóa |
| | | p31 | 4.2.25 Lục Bại (Song Hao, Tang Hổ, Khốc Hư) |

Thêm `tb#0038-cac-nhan-dinh` (4.1 nhận định khái quát Mệnh Thân, dùng cho rule-card ở lô 8, đọc để hiểu ngữ cảnh) và `tb#0093`, `tb#0094` (17. Phụ luận Mệnh Thân: thượng cách, hạ cách).

Đối chứng: Trần Đoàn `td#0049` đến `td#0056` (Thập nhị cung luận, Nhất cung Mệnh; td#0050 là Tử Vi tại Mệnh và có phú, td#0052 Tham Lang, td#0053 Tả Phụ, td#0054 Kình Dương, td#0055 Thiên Không Địa Kiếp Hóa Lộc Quyền Khoa, td#0056 Hóa Khoa Hóa Kỵ Thái Tuế), `td#0071-luan-ve-nu-menh-p01..p04` (nữ mệnh). Nguyễn Phát Lộc `npl#0125-cung-menh`, `npl#0151-cung-menh-cung-than`, `npl#0047-sao-menh-chu-sao-than-chu`, `npl#0057`, `npl#0058` (cung cường của nam, nữ).

Cách tách thẻ từ một tiểu mục 4.2.N:

- Một thẻ chính cho chính tinh đơn thủ: `menh-than/<sao>.md` với `palace: [menh, than]`. Đại cương → Kết luận và Điều kiện; các đoạn "Nam mệnh" "Nữ mệnh" → gạch đầu dòng trong Điều kiện với tiền tố `Nam mệnh:` `Nữ mệnh:`.
- Mỗi bộ sao có đoạn riêng dài từ hai câu trở lên (ví dụ "Tử gặp Tham đồng cung", "Tử Phủ đồng cung", "Cơ Cự Mão Dậu") → thẻ combo tại cung: `menh-than/<chính tinh>+<sao>.md`. Thẻ mẫu `tu-vi+tham-lang.md` là chuẩn để bắt chước. Bộ chỉ có một câu thì giữ trong Điều kiện của thẻ chính.
- Phần "Phú giải" của 4.2.N: mỗi câu phú ghi một dòng trong "Phú liên quan" của thẻ chính, dạng `- "câu phú" → ý giải ngắn`. Thẻ phú riêng làm ở lô 9, khi đó quay lại đổi thành liên kết.
- Phụ tinh tại Mệnh (p22 đến p31): mỗi bộ một thẻ, `stars` là các sao trong bộ theo thứ tự Tân Biên, ví dụ `menh-than/van-xuong+van-khuc.md`, `menh-than/hoa-loc.md`, `menh-than/dia-khong+dia-kiep.md`, `menh-than/dai-hao+tieu-hao.md`.
- Thứ tự lô con đề nghị: (a) p01–p06 Tử Vi, Liêm, Đồng, Vũ; (b) p07–p13 Nhật, Cơ, Phủ, Nguyệt, Tham; (c) p14–p21 Cự, Tướng, Lương, Sát, Phá; (d) p22–p31 phụ tinh; (e) nữ mệnh và đối chứng bổ sung từ td#0071 và NPL cho các thẻ đã có (chỉ thêm dòng vào Đối chứng, không tạo thẻ mới).

### Lô 5. Thẻ 11 cung còn lại (ước 300 đến 400 thẻ)

Tân Biên mục 5 đến 15, mỗi tiểu mục ### là một sao hoặc bộ sao. Khúc theo cung:

| Cung (thư mục) | Tân Biên | Trần Đoàn | Nguyễn Phát Lộc |
|---|---|---|---|
| phu-mau | `tb#0040` (Nhật Nguyệt 12 vị trí), `tb#0041-...-p01..p06` | `td#0062` | xem `--grep "Phụ Mẫu"` |
| phuc-duc | `tb#0042-...-p01..p13` (6.1 phúc trạch), `tb#0043` (6.2 âm phần) | `td#0061` | `npl#0124`, `npl#0150` |
| dien-trach | `tb#0044` đến `tb#0052` (7.1 đến 7.63) | `td#0064` | `--grep "Điền Trạch"` |
| quan-loc | `tb#0053` đến `tb#0061` (8.x) | `td#0058` | `npl#0127`, `npl#0114`, `npl#0115-p01..p06` |
| no-boc | `tb#0062` (9.1), `tb#0063` (9.2) | `td#0063` | `npl#0087` |
| thien-di | `tb#0064` đến `tb#0069` (10.x) | `td#0057` | |
| tat-ach | `tb#0070` (11.1 sao cứu giải), `tb#0071` (11.2 sao tác họa, 9 KB, nhiều sao) | `td#0065` | `npl#0088` |
| tai-bach | `tb#0072` đến `tb#0078` (12.x) | `td#0059` | `npl#0126`, `npl#0128` đến `npl#0133` |
| tu-tuc | `tb#0079` (13.1), `tb#0080-...-p01..p06` (13.2, 13.3) | `td#0048`, `td#0049` có đoạn | `--grep "Tử Tức"` |
| phu-the | `tb#0081` đến `tb#0089` (14.x) | `td#0060`, `td#0072` | `--grep "cung Phối"` |
| huynh-de | `tb#0090` (15.1), `tb#0091` (15.2, 8 KB) | | |

Ghi chú: các tiểu mục kiểu "7.34 Nhật, Hổ", "7.41 Cơ, Nguyệt, Đà, Kỵ" là combo tại cung → tên file nối `+` theo thứ tự chính tinh trước. Tiểu mục chỉ hai ba dòng vẫn làm thẻ riêng vì đó là khoá tra cứu. Với `tb#0071` (Tật Ách sao tác họa) và `tb#0091` (Huynh Đệ) là khúc lớn gồm nhiều mục 11.2.N, 15.2.N liền nhau: tách mỗi N một thẻ.

Trần Đoàn có chương riêng từng cung (td#0057 đến td#0065) viết theo sao: đọc một lần cho mỗi cung, rải vào Đối chứng của các thẻ tương ứng.

### Lô 6. Cách cục `30-combos/` (ước 60 đến 100 thẻ)

Nguồn: Tân Biên `tb#0096` (19.2 Quý cục), `tb#0097` (19.3 Bần tiện cục), `tb#0098` (19.5 Phụ luận), `tb#0099` đến `tb#0101` (20. Nhận xét số mệnh của một vài hạng người), `tb#0104`; Thiên Lương `tl#0022` (Liêm Tham Tỵ Hợi, Liêm Sát Sửu Mùi), `tl#0025` (bốn bộ chính tinh), `tl#0038` (14 chính tinh), `tl#0083` (Tử Vi và Phá Quân), `tl#0084` (Thất Sát triều đẩu), `tl#0088` (Lương Nguyệt Đồng Cơ Cự Nhật), `tl#0090` (Tam hóa liên châu), `tl#0068` (Vô chính diệu đắc tam không); Trần Đoàn `td#0081` (Đoán định cách cục), `td#0086` đến `td#0089` (Cách cục, hợp cách, phá cách, tật yểu, tăng đạo), `td#0112`; Nguyễn Phát Lộc `npl#0055`, `npl#0065`, `npl#0073`, `npl#0131`.

Tên thẻ là slug của tên cách: `tu-phu-vu-tuong`, `sat-pha-liem-tham`, `co-nguyet-dong-luong`, `cu-nhat`, `nhat-nguyet-sang-hoi-mui`, `vo-chinh-dieu`, `tam-hoa-lien-chau`, `kinh-duong-doc-thu`... Cách đã có thẻ cung (Tử Tham Mão Dậu) vẫn cần thẻ combo nếu sách bàn ngoài phạm vi một cung; nếu chỉ bàn tại Mệnh thì không lặp.

### Lô 7. Hạn `40-han/` (ước 40 đến 60 thẻ)

Tân Biên Phần III: `tb#0002` (Phần III giới thiệu), `tb#0108` (1.2 Kết hợp nhận định), `tb#0109` đến `tb#0111` (2. liên hệ đại hạn tiểu hạn, Mệnh Thân với hạn, năm tuổi năm xung), `tb#0112-...-p01..p13` (3.2 ảnh hưởng từng sao nhập hạn: mỗi sao một thẻ `han:<sao>-nhap-han`), `tb#0113` đến `tb#0115` (4. lưu Thái Tuế Tang Hổ, lưu Khốc Hư, lưu Lộc Kình Đà, lưu Mã), `tb#0116` (5.2 đám tang; 5.1 Hạn chết nằm cuối `tb#0115`), `tb#0105` (22.1 luận đoán vận hạn theo bản mệnh). Thiên Lương `tl#0028` (Thương Sứ, các năm 49 53 67), `tl#0057` (Vận hạn nên tính thế nào), `tl#0058` (Thế nào là vận hội tốt), `tl#0014` (Đẩu Quân tiểu vận), `tl#0029-p02` (bốn nguyên tắc hạn Thái Tuế, Thiên Không). Trần Đoàn `td#0066` đến `td#0070` (hạn, sao nhập hạn). Nguyễn Phát Lộc `npl#0059` đến `npl#0063`.

Thẻ liên hệ hạn (không gắn sao) đặt tên theo nội dung: `dai-han-tieu-han-lien-he`, `nam-tuoi-nam-xung`, `han-49-53-67-thuong-su`.

### Lô 8. Quy tắc suy luận `50-rules/` (ước 40 đến 60 thẻ)

Thiên Lương là nguồn chính, một quy tắc một thẻ: `tl#0044` (chính không bằng chiếu, chiếu không bằng giáp), `tl#0040` (nhị hợp, tam hợp, xung chiếu; Tỵ với Thân, Ngọ với Mùi), `tl#0085` (năng lực nhị hợp), `tl#0045` (đâu là số đẹp), `tl#0047` (bản thể Thái Tuế), `tl#0048` (bốn tam hợp cục), `tl#0050` đến `tl#0054` (Bào với Nô, Phụ Mẫu với Tật Ách), `tl#0055`, `tl#0056` (giàu nhờ bạn sang vì vợ), `tl#0059` (triết lý chính danh), `tl#0032` (Mệnh Thân ở tứ Sinh, tứ Chính, tứ Mộ), `tl#0033` (Phúc Đức Mệnh Thân), `tl#0034` (khu đất phì nhiêu trong 12 cung), `tl#0039` (Tuần Triệt với Mệnh có chính diệu, đắc ngộ kiến Không), `tl#0041` (quyết định giờ sinh), `tl#0042`, `tl#0043` (vòng Tràng Sinh), `tl#0087` (Di), `tl#0089` (tứ hóa theo 10 can), `tl#0092` (năm tuổi ở mộ cung), `tl#0094` (nghịch lý âm dương), `tl#0095` đến `tl#0097` (bốn tuổi Ất Mậu Tân Nhâm), `tl#0019`, `tl#0020` (lục sát tinh ngộ chế, đã dùng một phần ở thẻ sao). Tân Biên: `tb#0019`, `tb#0020` (mục 1. Những điều phải chú ý trước khi luận đoán và mục 2. Định danh; hai khúc này gom nhiều tiểu mục 1.x, 2.x, tiêu đề chỉ hiện tiểu mục đầu), `tb#0013` (9.1 Tam chiếu), `tb#0038` (4.1 nhận định Mệnh Thân), `tb#0092` (16. mùa sinh giờ sinh), `tb#0102`, `tb#0103` (21. tiểu nhi), `tb#0104` (bản mệnh ngũ hành). Nguyễn Phát Lộc: `npl#0009`, `npl#0011` (giới hạn khoa Tử Vi), `npl#0014` (phương pháp tổng hợp), `npl#0029`, `npl#0030` (động tính 12 cung, phối chiếu), `npl#0033` đến `npl#0036`, `npl#0040`, `npl#0041` (quan niệm về sao, độ số), `npl#0046` (chín sao lưu động), `npl#0057`, `npl#0058` (cung cường theo phái), `npl#0064`.

Với quy tắc NPL: vì NPL không phải nguồn chính, thẻ rule chỉ có `primary` là tb/tl; nội dung NPL đưa vào Đối chứng. Nếu quy tắc chỉ có ở NPL, tạo thẻ với `primary: [tb]` hoặc `[tl]` là sai; thay vào đó gom vào một thẻ rule tổng "giới hạn của khoa Tử Vi" mà mục Kết luận trích Tân Biên 1. Những điều phải chú ý, còn NPL nằm ở Đối chứng.

### Lô 9. Phú `60-phu/` (ước 200 đến 300 thẻ)

Nguồn: mục "Phú giải" trong từng 4.2.N của Tân Biên (đã liệt kê tạm ở "Phú liên quan" của thẻ cung lô 4); Trần Đoàn `td#0090` đến `td#0111` (Đẩu số cốt tủy phú chú giải, mỗi khúc nhiều câu) và danh sách phú cuối mỗi chương sao (td#0008 đến td#0047); Thiên Lương `tl#0007` (Những câu phú nên thận trọng áp dụng). Tên thẻ: slug của câu phú rút gọn, ví dụ `tu-vi-cu-ngo-vo-hinh-ky`. Nếu Tân Biên và Trần Đoàn cùng giải một câu, gộp một thẻ, Trần Đoàn ở Đối chứng. Sau lô này, quay lại các thẻ cung đổi dòng "Phú liên quan" thành liên kết `60-phu/<slug>.md`.

### Lô 10. Index, SKILL, đọc ảnh (làm cuối, medium effort)

1. `scripts/build_lookup.py`: đọc frontmatter mọi thẻ, sinh `00-index/lookup.md` gồm ba bảng: sao → thẻ sao; (cung, bộ sao) → thẻ cung; cách cục → thẻ combo; và danh sách rule, han, phu theo tag. File dưới 60 KB; nếu vượt, tách `lookup-palaces.md`. Dùng `tuvi_kb_common.parse_frontmatter`, không thêm thư viện.
2. `00-index/chart-reading.md`: cách đọc ảnh lá số web: vị trí 12 cung trên lưới 4×4, cột giữa ghi tuổi và cục, cách ghi miếu hãm (M V Đ H hoặc dấu +/-), Tuần Triệt vẽ giữa hai cung, đại hạn ghi số tuổi ở góc cung, bảng viết tắt lấy từ cột `viết tắt` của stars.md. Không có ảnh mẫu trong repo, viết theo kinh nghiệm chung và ghi rõ là cần người dùng bổ sung ảnh để chỉnh.
3. `output/tuvi-kb/SKILL.md`: quy trình 7 bước như mục 7 của proposal, thêm ràng buộc: trước khi luận phải in bảng chuẩn hoá lá số cho người dùng xác nhận; mọi nhận định ghi nhãn nguồn; khi Tân Biên và Thiên Lương khác nhau thì nêu cả hai.
4. Đối chứng NPL bổ sung: chạy `dump_chunks.py --grep "<tên sao>"` trên NPL cho 14 chính tinh, thêm dòng `[NPL]` vào Đối chứng của thẻ sao tương ứng và thêm `npl` vào `cross`. Không sửa phần khác.

## 7. Quyết định đã chốt, không hỏi lại

- Nguồn chính là Tân Biên và Thiên Lương; Trần Đoàn và Nguyễn Phát Lộc chỉ đối chứng.
- Khi hai nguồn chính khác nhau, ghi cả hai với nhãn riêng, không chọn thay người dùng.
- Không viết module an sao. Không sửa tầng nguyên văn. Không đổi schema; nếu schema thiếu, ghi vào `docs/tuvi-kb-runbook.md` mục "Đề xuất sửa schema" và làm theo schema hiện có.
- Slug tiếng Việt không dấu, chữ thường, gạch nối. Địa chi: ty, suu, dan, mao, thin, ti (Tỵ), ngo, mui, than, dau, tuat, hoi.
- Sao có tên trùng: Quan Phù vòng Thái Tuế là `quan-phu`; Quan Phủ vòng Lộc Tồn là `quan-phu-loc-ton`; sao Phúc Đức là `phuc-duc-tinh`; Tử vòng Tràng Sinh là `tu`.
- Trong Tân Biên, "Lộc" ở mục Tứ Hóa là Hóa Lộc, ở "Lộc Tồn" mới là Lộc Tồn; "Lộc, Mã" đi cặp thường là Lộc Tồn. Khi không rõ, ghi cả hai id trong `stars` là sai; chọn theo ngữ cảnh và ghi chú trong Điều kiện.

## 8. Prompt mẫu cho phiên Sonnet

```
Bạn tiếp tục dự án tuvi-kb trong repo này. Đọc docs/tuvi-kb-runbook.md rồi làm Lô 4, lô con (a): thẻ cung Mệnh Thân cho Tử Vi, Liêm Trinh, Thiên Đồng, Vũ Khúc từ các khúc tb#0039 p01 đến p06, đối chứng td#0050 đến td#0056. Làm đúng quy trình mục 4 của runbook: dump, đọc, viết cả lô, chạy validator, sửa, commit. Không hỏi lại các quyết định ở mục 7. Khi xong, báo số thẻ, kết quả validator và commit hash.
```

Mỗi phiên giao một lô con. Sau lô 4 và lô 5, người dùng nên xem ngẫu nhiên 5 thẻ để kiểm chất lượng diễn đạt, vì validator chỉ kiểm hình thức và trích dẫn, không kiểm ý.
