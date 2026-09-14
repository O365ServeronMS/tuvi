# Schema thẻ tuvi-kb

`scripts/validate_kb.py` kiểm tra đúng những gì ghi ở đây. Khi đổi schema, đổi cả hai.

## 1. Vị trí và tên file

| type | thư mục | tên file | id trong frontmatter |
|---|---|---|---|
| star-card | `10-stars/` | `<star-id>.md` | `star:<star-id>` |
| palace-card | `20-palaces/<thư mục cung>/` | `<sao1>+<sao2>+....md` theo đúng thứ tự `stars` | `palace:<thư mục cung>:<tên file>` |
| combo-card | `30-combos/` | `<slug>.md` | `combo:<slug>` |
| han-card | `40-han/` | `<slug>.md` | `han:<slug>` |
| rule-card | `50-rules/` | `<slug>.md` | `rule:<slug>` |
| phu-card | `60-phu/` | `<slug>.md` | `phu:<slug>` |

Thư mục cung lấy từ cột `thư mục` trong `00-index/palaces.md`. Mệnh và Thân dùng chung `menh-than`. Trong tên file thẻ cung, chính tinh đứng trước phụ tinh.

## 2. Frontmatter

YAML tối giản: `khoá: giá trị`, `khoá: [a, b]`, hoặc `khoá:` rồi các dòng `  - a`. Chuỗi có ký tự đặc biệt để trong dấu nháy kép.

| khoá | bắt buộc | kiểu | ràng buộc |
|---|---|---|---|
| id | có | chuỗi | theo bảng trên |
| type | có | chuỗi | tên type theo thư mục |
| primary | có | danh sách | tập con không rỗng của `[tb, tl]` |
| cross | không | danh sách | tập con của `[td, npl]` |
| chunks | có | danh sách | id khúc trong `90-source/`, ít nhất một |
| stars | tuỳ type | danh sách | id trong `00-index/stars.md`; han-card được dùng `luu-<id>` |
| palace | palace-card | danh sách | id trong `00-index/palaces.md`, cùng thư mục |
| positions | không | danh sách | địa chi: ty, suu, dan, mao, thin, ti, ngo, mui, than, dau, tuat, hoi |
| gender | không | chuỗi | any, nam, nu |
| tags | không | danh sách | slug ASCII |

star-card: `stars` đúng một sao, tên file bằng id sao. combo-card: `stars` ít nhất hai sao. Hai thẻ cung không được trùng cả `palace` lẫn `stars`.

## 3. Thân bài

Dòng đầu là tiêu đề `# ...`. Các mục là `## Tên mục` đúng chính tả dưới đây, không lặp.

| type | mục bắt buộc theo thứ tự |
|---|---|
| star-card | Bản chất, Vị trí miếu hãm, Gặp sao khác, Nam nữ, Đối chứng, Nguyên văn |
| palace-card | Kết luận, Điều kiện và sắc thái, Đối chứng, Nguyên văn (tuỳ chọn: Phú liên quan) |
| combo-card | Thành phần, Điều kiện thành cách, Ý nghĩa, Phá cách, Cung áp dụng, Đối chứng, Nguyên văn |
| han-card | Kết luận, Tốt khi, Xấu khi, Kết hợp Mệnh Thân, Đối chứng, Nguyên văn |
| rule-card | Điều kiện, Kết luận, Ngoại lệ, Ví dụ trong sách, Khi nào không áp dụng, Nguyên văn (tuỳ chọn: Đối chứng) |
| phu-card | Câu phú, Giải nghĩa, Sao và cung liên quan, Nguồn giải, Nguyên văn |

## 4. Nhãn nguồn

- Mỗi gạch đầu dòng (`- `, `+ `, `* `) bắt đầu bằng đúng một nhãn: `[TB]`, `[TL]`, `[TĐ]`, `[NPL]`, rồi một khoảng trắng.
- Ngoài mục Đối chứng chỉ được dùng `[TB]` và `[TL]`, và chỉ nhãn có trong `primary`.
- Trong mục Đối chứng chỉ được dùng `[TĐ]` và `[NPL]`. Mỗi nguồn trong `cross` nên có ít nhất một dòng.
- Các mục không cần nhãn: Nguyên văn, Phú liên quan, Sao và cung liên quan, Thành phần, Cung áp dụng, Câu phú.

## 5. Mục Nguyên văn

Mỗi trích dẫn là một khối blockquote, kết thúc bằng id khúc trong ngoặc đơn:

```
> "Cung Mệnh an tại Mão, Dậu, có Tử tọa thủ, gặp Tham đồng cung, là người yếm thế [...] sớm biết tu hành, tất được yên thân và hưởng phúc." (tb#0042-tu-vi)
```

- Tối đa 400 ký tự sau khi gộp khoảng trắng.
- Được lược bằng `[...]`; từng đoạn phải xuất hiện đúng thứ tự trong khúc đó (so sánh không phân biệt hoa thường và khoảng trắng).
- Id khúc phải có trong `chunks` của frontmatter.
- Ít nhất một trích dẫn hợp lệ mỗi thẻ.

## 6. Kích thước

- Thẻ nên dưới 8 KB (cảnh báo), không được quá 100 KB (lỗi).
- File trong `00-index/` nên dưới 60 KB.

## 7. Khúc nguyên văn (`90-source/`)

Sinh bởi `scripts/chunk_sources.py`, không sửa tay. Frontmatter: `id`, `book`, `book_code`, `title`, `heading_path`, `level`, `ordinal`, `part`, `parts`, `source_file`, `source_lines`, `chars`, `stars_detected`, `stars_in_title`, `palaces_detected`, `non_luan`. Khúc có `non_luan: true` (lập thành, lời nói đầu, tiểu sử, mục lục) không tính vào chỉ tiêu phủ trong `_meta/coverage.json`.
