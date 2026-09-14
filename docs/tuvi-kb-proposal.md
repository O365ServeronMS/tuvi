# Đề xuất cấu trúc output `tuvi-kb` cho Claude luận giải lá số

Ngày: 2026-09-14. Trạng thái: đề xuất, chờ duyệt trước khi triển khai.

## 0. Các quyết định đã chốt

| Vấn đề | Quyết định |
|---|---|
| Kênh tiêu thụ | Claude Code / Skill đọc thư mục bằng grep, ls, read |
| Mức biến đổi | Hybrid: tầng thẻ chuẩn hoá + tầng nguyên văn chia khúc |
| Nguồn | Tân Biên (TB) và Thiên Lương (TL) là chuẩn; Trần Đoàn (TĐ) và Nguyễn Phát Lộc (NPL) là đối chứng có nhãn |
| Đầu vào | Ảnh chụp lá số từ web (tuvi.vn, lyso.vn...) |
| Phạm vi | Mệnh, Thân, 12 cung; đại hạn, tiểu hạn, lưu niên; hệ thống riêng của Thiên Lương |
| Sản xuất | Script cắt khúc và kiểm tra; Claude trích thẻ theo lô |
| Output cũ | Giữ nguyên; bộ mới nằm ở `output/tuvi-kb/` |

## 1. Vì sao hai bộ output hiện tại chưa tra cứu được

- Cả hai đều cắt theo heading rồi gom nhóm bằng từ khoá. Kết quả là file `02_chart_setup...` nặng 545 KB, `16_unsorted` có 388 mục, và bộ `tan-bien` xếp 76/100 file vào `palaces` kể cả các mục nói về sao.
- Câu hỏi thực tế khi luận giải là "Tử Vi gặp Tham Lang tại Mệnh ở Mão thì sao" hoặc "Không Kiếp tại Điền Trạch". Không bộ nào trả lời được bằng một lệnh grep hay một lần đọc file, vì khoá tra cứu (bộ sao × cung) không nằm trong tên file hay metadata.
- Không có bảng chuẩn hoá tên sao. Sách viết "Kình", "Đà", "Nhật", "Nguyệt", "Tướng", "Phủ", "Lộc" với nhiều nghĩa. Claude đọc ảnh lá số cũng gặp tên viết tắt khác nhau theo từng web.
- Bốn nguồn bị trộn ngang hàng, Claude không biết đang dựa vào ai.

## 2. Cấu trúc sách gốc quyết định cấu trúc output

Khảo sát heading cho thấy ba kiểu tổ chức khác nhau, nên cần ba kiểu thẻ:

- **Tân Biên** là ma trận cung × sao. Mục 3 có 85 tiểu mục đặc tính từng sao. Mục 4.2 luận sao tại Mệnh Thân theo từng sao, chia Đại cương, Nam mệnh, Nữ mệnh, Phú giải. Các cung Điền Trạch (63 tiểu mục), Tài Bạch (56), Phu Thê (54), Quan Lộc (46), Thiên Di (36) mỗi tiểu mục là một sao hoặc bộ sao. Phần III là hạn. Đây là nguồn chính cho **thẻ cung** và **thẻ sao**.
- **Trần Đoàn** có chương riêng từng sao, rồi chương riêng từng cung, rồi Phú cách, Quý cách, Bần tiện cách, Mệnh vô chính diệu. Dùng làm **đối chứng** cho thẻ sao, thẻ cung và **thẻ cách cục**.
- **Thiên Lương** là tiểu luận theo chủ đề: vòng Thái Tuế, Lộc Tồn, Tràng Sinh, nhị hợp tam hợp xung chiếu, chính không bằng chiếu, tam hợp tuổi, Tuần Triệt với chính diệu. Không tra theo sao được. Cần **thẻ quy tắc suy luận**: điều kiện → kết luận → ngoại lệ → ví dụ.
- **Nguyễn Phát Lộc** là giáo trình phương pháp và giới hạn của khoa Tử Vi, cộng nhiều chương ứng dụng. Dùng làm đối chứng và bổ sung cho thẻ quy tắc.

## 3. Cây thư mục đề xuất

```
output/tuvi-kb/
  SKILL.md                    quy trình luận giải, thứ tự tra cứu, luật trích nguồn
  00-index/
    stars.md                  sổ đăng ký sao: id, tên, alias, hành, âm dương, nhóm, miếu vượng đắc hãm theo TB và TĐ
    palaces.md                12 cung + Mệnh + Thân, alias, cung đối xung, tam hợp
    combos.md                 sổ đăng ký bộ sao và cách cục có tên
    lookup.md                 bảng sao × cung → đường dẫn thẻ (script sinh ra)
    chart-reading.md          cách đọc ảnh lá số: bố cục web phổ biến, viết tắt, ký hiệu miếu hãm, Tuần Triệt
  10-stars/                   một file mỗi sao: bản chất, vị trí, gặp sao khác, nam nữ
    tu-vi.md ... (khoảng 110 sao)
  20-palaces/                 một thư mục mỗi cung, một file mỗi sao hoặc bộ sao tại cung đó
    menh-than/ phu-mau/ phuc-duc/ dien-trach/ quan-loc/ no-boc/
    thien-di/ tat-ach/ tai-bach/ tu-tuc/ phu-the/ huynh-de/
  30-combos/                  cách cục và bộ sao có tên, không phụ thuộc cung
  40-han/                     đại hạn, tiểu hạn, lưu niên, sao nhập hạn, sao lưu động
  50-rules/                   quy tắc suy luận: TL (Thái Tuế, Lộc Tồn, Tràng Sinh, nhị hợp...), TB (hướng chiếu, kết hợp nhận định), NPL (giới hạn)
  60-phu/                     câu phú và lời giải, gắn với sao và cung
  90-source/                  nguyên văn chia khúc, id ổn định
    tan-bien/ thien-luong/ tran-doan/ nguyen-phat-loc/
  _meta/
    schema.md                 định nghĩa frontmatter và các mục bắt buộc
    coverage.json             khúc nào đã được thẻ nào tham chiếu
```

Nguyên tắc kích thước: thẻ 2 đến 8 KB, khúc nguyên văn 3 đến 10 KB, bảng index dưới 60 KB, không file nào quá 100 KB để lệnh Read đọc trọn một lần.

## 4. Khoá tra cứu và định danh

- **Id sao là slug ASCII không dấu**: `tu-vi`, `kinh-duong`, `hoa-ky`. Grep không phụ thuộc dấu và cách gõ. Tên có dấu nằm trong nội dung.
- **Tên file thẻ cung** mã hoá bộ sao, sắp theo thứ tự chính tinh trước, phụ tinh sau, nối bằng `+`: `20-palaces/menh-than/tu-vi+tham-lang.md`. Địa chi và miếu hãm nằm trong frontmatter và nội dung, không đưa vào tên file vì quá thưa.
- **Bảng alias bắt buộc** trong `stars.md`. Ví dụ cần xử lý: Kình = Kình Dương = Dương Nhận; Nhật = Thái Dương; Nguyệt = Thái Âm; Tướng = Thiên Tướng (không phải Tướng Quân); Phủ = Thiên Phủ (không phải Quan Phủ, Đường Phù); Lộc = Lộc Tồn hay Hoá Lộc tuỳ ngữ cảnh, thẻ phải ghi rõ. Bảng ghi cả cách viết tắt trên web: K.Dương, Đ.La, T.Phủ, H.Kỵ.
- **Id khúc nguyên văn** = `mã sách#số-thứ-tự-slug-tiêu-đề[-pNN]`, ví dụ `tb#0005-anh-huong-cua-nhung-sao-toa-thu-tai-cung-menh-p12` (khúc thứ 5 của Tân Biên, phần 12 của mục 4.2, chính là tiểu mục "4.2.9. Tham Lang"). Dùng số thứ tự thay số mục trong sách vì Tân Biên đánh số lỗi (7.8 và 7.14 xuất hiện hai lần). Frontmatter khúc ghi `heading_path`, `title` và `source_lines` để đối chiếu ngược về file input.

## 5. Schema thẻ

Frontmatter YAML, sau đó thân bài với các mục cố định. Ví dụ thẻ cung:

```markdown
---
id: palace:menh-than:tu-vi+tham-lang
type: palace-card
palace: [menh, than]
stars: [tu-vi, tham-lang]
positions: [mao, dau]
gender: any
tags: [yem-the, tu-hanh, bi-quan]
primary: [tb]
cross: [td, npl]
chunks:
  - tb#p2-04-menh-than-001-tu-vi
  - td#sao-tu-vi-004
---
# Tử Vi + Tham Lang đồng cung tại Mệnh (Mão, Dậu)

## Kết luận
- [TB] Người yếm thế, nhìn đời bi quan, có ý lánh trần tu dưỡng.
- [TB] Còn chen vào chốn phồn tạp thì lao khổ; sớm tu hành thì yên thân, hưởng phúc.

## Điều kiện và sắc thái
- [TB] Nam mệnh: chỉ tu hành mới mong yên thân.
- [TB] Gặp thêm Không Kiếp: suốt đời lao tâm khổ tứ.

## Đối chứng
- [TĐ] Đồng ý về hướng tu đạo; thêm ý "dâm" khi hãm địa gặp sát tinh.
- [NPL] Không bàn riêng cách này.

## Phú liên quan
- "Tử Tham Mão Dậu..." → xem `60-phu/tu-tham-mao-dau.md`

## Nguyên văn
> "Cung Mệnh an tại Mão, Dậu, có Tử tọa thủ, gặp Tham đồng cung, là người yếm thế..." (tb#p2-04-menh-than-001-tu-vi)
```

Luật cứng cho thân bài:

- Mỗi gạch đầu dòng bắt đầu bằng đúng một nhãn nguồn `[TB]`, `[TL]`, `[TĐ]`, `[NPL]`.
- Mục Kết luận chỉ chứa nhãn TB hoặc TL. TĐ và NPL chỉ xuất hiện ở mục Đối chứng, ghi rõ đồng ý, bổ sung hay khác biệt.
- Mục Nguyên văn trích tối đa 400 ký tự, phải khớp chuỗi với khúc nguồn sau khi chuẩn hoá khoảng trắng. Script kiểm tra điều này, đây là hàng rào chống bịa.
- Thẻ cung chỉ ghi điều riêng của cung đó. Bản chất chung của sao nằm ở `10-stars/`, thẻ cung liên kết sang, không chép lại.

Các loại thẻ khác dùng cùng frontmatter, khác mục thân bài:

| type | thân bài |
|---|---|
| star-card | Bản chất, Vị trí miếu hãm (bảng theo TB và TĐ), Gặp sao khác, Nam nữ, Đối chứng, Nguyên văn |
| combo-card | Thành phần, Điều kiện thành cách, Ý nghĩa, Phá cách, Cung áp dụng, Đối chứng, Nguyên văn |
| han-card | Sao nhập hạn hoặc liên hệ hạn, Tốt khi, Xấu khi, Kết hợp Mệnh Thân, Đối chứng, Nguyên văn |
| rule-card | Điều kiện, Kết luận, Ngoại lệ, Ví dụ trong sách, Khi nào không áp dụng, Nguyên văn |
| phu-card | Câu phú, Giải nghĩa, Sao và cung liên quan, Nguồn giải |

## 6. Tầng nguyên văn `90-source/`

- Script cắt bốn sách theo heading, mỗi khúc một file, frontmatter gồm `book`, `heading_path`, `ordinal`, `chars`, `stars_detected`, `palaces_detected` (regex từ bảng alias).
- Giữ nguyên chữ, chỉ sửa lỗi OCR tách chữ ("Kh ắc", "ng ười") bằng danh sách thay thế có kiểm soát như script cũ đã làm. Ghi tỉ lệ mất mát vào `_meta`.
- Khúc quá dài (trên 10 KB) cắt tiếp theo đoạn trống, giữ cùng tiền tố id.
- Mọi thẻ tham chiếu khúc bằng id. `coverage.json` liệt kê khúc chưa được thẻ nào dùng, kèm cờ `non-luan` cho phần lập thành, thơ, tiểu sử, mục lục để loại khỏi chỉ tiêu phủ.

## 7. `SKILL.md`: quy trình Claude luận giải

1. Đọc ảnh theo `00-index/chart-reading.md`, xuất ra bảng chuẩn: tuổi can chi, âm dương nam nữ, cục, Mệnh và Thân ở cung nào, mỗi cung có sao gì kèm miếu hãm, Tuần Triệt ở đâu, các mốc đại hạn. Nếu ảnh mờ hoặc thiếu, hỏi lại trước khi luận.
2. Chuẩn hoá tên sao sang id bằng bảng alias.
3. Với Mệnh, Thân: tra `lookup.md` lấy thẻ chính tinh và bộ sao đồng cung, rồi thẻ cách cục trong `30-combos/`, rồi thẻ sao hội chiếu theo `50-rules/` về hướng chiếu.
4. Với 12 cung còn lại: cùng cách, ưu tiên cung người dùng hỏi.
5. Áp dụng thẻ quy tắc Thiên Lương: vòng Thái Tuế, Lộc Tồn, Tràng Sinh của tuổi; nhị hợp; chính không bằng chiếu.
6. Hạn: tra `40-han/` theo sao nhập hạn và liên hệ hạn với Mệnh Thân.
7. Viết luận giải. Mỗi nhận định ghi nhãn nguồn. Không nêu điều không có trong thẻ; nếu suy diễn thì nói rõ là suy diễn. Khi TB và TL khác nhau, nêu cả hai và không tự chọn thay người dùng.

Skill này đặt ở `output/tuvi-kb/SKILL.md` để có thể copy hoặc symlink vào `.claude/skills/tuvi/` mà không sửa gì.

## 8. Quy trình sản xuất

| Bước | Ai | Sản phẩm | Kiểm tra |
|---|---|---|---|
| 1. Cắt khúc | script `chunk_sources.py` | `90-source/` | mất mát dưới 0,5%, mỗi khúc dưới 10 KB |
| 2. Sổ đăng ký | Claude viết, script kiểm | `00-index/stars.md`, `palaces.md`, `combos.md` | mọi sao trong TB mục 3 và TĐ chương sao đều có id |
| 3. Thẻ sao | Claude, lô theo nhóm sao | `10-stars/` | 100% sao trong sổ có thẻ |
| 4. Thẻ Mệnh Thân | Claude, lô theo chính tinh | `20-palaces/menh-than/` | mọi khúc TB 4.2 được tham chiếu |
| 5. Thẻ 11 cung | Claude, lô theo cung | `20-palaces/*` | mọi khúc TB mục 5 đến 15 được tham chiếu |
| 6. Cách cục | Claude | `30-combos/` | phủ TĐ Phú cách, Quý cách, Bần tiện cách |
| 7. Hạn | Claude | `40-han/` | phủ TB Phần III |
| 8. Quy tắc | Claude, lô theo bài TL | `50-rules/` | mọi bài TL được tham chiếu |
| 9. Phú | Claude | `60-phu/` | mọi câu phú trong TB Phú giải và TL |
| 10. Index | script `build_lookup.py` | `lookup.md`, `coverage.json` | sinh từ frontmatter, không viết tay |

`validate_kb.py` chạy sau mỗi lô: schema frontmatter, id sao và cung tồn tại trong sổ, id khúc tồn tại, trích nguyên văn khớp nguồn, giới hạn kích thước, phát hiện thẻ trùng bộ sao và cung. Mỗi lô là một commit riêng để dễ soát và làm lại.

## 9. Ước lượng khối lượng

| Nhóm | Số thẻ ước tính |
|---|---|
| Thẻ sao | 110 |
| Thẻ cung | 500 đến 700 |
| Cách cục | 60 đến 100 |
| Hạn | 40 đến 60 |
| Quy tắc | 40 đến 60 |
| Phú | 200 đến 300 |

Khoảng 1.000 thẻ, mỗi thẻ vài KB. Thẻ Mệnh Thân là lô nặng nhất và nên làm đầu tiên vì đó là phần người dùng hỏi nhiều nhất.

## 10. Rủi ro và cách chặn

- **Bịa nội dung khi trích thẻ.** Chặn bằng luật nguyên văn khớp chuỗi và bắt buộc id khúc trên mỗi thẻ.
- **Tên sao mơ hồ.** Chặn bằng sổ đăng ký với quy tắc phân giải theo ngữ cảnh; thẻ nào dùng tên mơ hồ phải ghi id đầy đủ.
- **Trộn nguồn.** Chặn bằng nhãn trên từng gạch đầu dòng và validator từ chối nhãn TĐ, NPL trong mục Kết luận.
- **OCR lỗi trong sách.** Sửa có kiểm soát ở bước cắt khúc, ghi log thay thế.
- **Đọc ảnh sai.** Bước 1 của SKILL bắt buộc xuất bảng chuẩn để người dùng xác nhận trước khi luận.

## 11. Giả định tôi tự chốt, sửa nếu bạn muốn khác

- Nội dung tiếng Việt có dấu; id, tên file, tag dùng ASCII không dấu.
- Không viết module an sao từ ngày giờ sinh. Lá số đến từ ảnh đã an sẵn.
- Không đụng vào `output/gpt_knowledge_merged` và `output/tan-bien`. Script cũ `split_tuvi_markdown.py` được tái dùng phần sửa OCR và tính mất mát.
- Bước 4 và 5 làm theo Tân Biên trước, sau đó mới bổ sung đối chứng TĐ và NPL vào cùng thẻ, không tạo thẻ riêng cho nguồn phụ.
