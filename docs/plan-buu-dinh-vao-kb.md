# Plan: đưa nguồn Bửu Đình [BĐ] vào tuvi-kb

Trạng thái: dữ liệu đã làm sạch và chia khúc (Pha 0 xong). Các pha sau chưa làm.

## 1. Quyết định nền

Đã chốt (2026-10-02): commit cả `90-source/buu-dinh/` và `output/buu-dinh/` (không ignore); khái niệm chỉ [BĐ] có thì không tạo thẻ, chỉ thêm Đối chứng vào thẻ sao/combo sẵn có. Chất lượng nguồn [BĐ] được đánh giá khá tốt, nên khi viết Đối chứng hãy khai thác kỹ, nhưng vẫn là đối chứng, không thay TB/TL.

| Quyết định | Đề xuất | Lý do |
|---|---|---|
| Vai trò của [BĐ] | **Đối chứng**, như [TĐ]/[NPL]; không phải nguồn chính | Ràng buộc nguồn của dự án: TB/TL là chính. Blog là văn nói, nhiều ý kiến cá nhân, có chỗ lệch TB. |
| Chỗ [BĐ] xuất hiện trong thẻ | Chỉ mục `## Đối chứng` và `## Nguyên văn`; frontmatter `cross: [..., bd]` | Giữ nguyên quy tắc 2–3 của CLAUDE.md. |
| [BĐ] khác TB/TL | Nêu cả hai, ghi rõ "lệch", không để [BĐ] bác TB/TL | Quy tắc 3. |
| Khái niệm chỉ có ở [BĐ] (nhóm Thị Phi, "nhóm Bất Ngờ"…) | Thẻ combo, phần chính chỉ chứa ý TB/TL; phần gom nhóm nằm ở Đối chứng | Mẫu `30-combos/nhom-thi-phi.md`. Nếu một khái niệm hoàn toàn không có ở TB/TL thì thẻ không có `primary` hợp lệ: cần quyết định (xem Rủi ro 1). |
| Q&A, bình luận độc giả, lá số người cụ thể | Loại | Không phải lý thuyết; đã loại ở Pha 0. |

## 2. Pha 0 — Dữ liệu (XONG)

Quy trình lặp lại được: `scripts/crawl_buudinh.py` (feed JSON Blogger, 519 bài) rồi `scripts/chunk_buudinh.py` (lọc, làm sạch, chia khúc).

Kết quả hiện tại:
- 271 bài lý thuyết giữ lại / 248 bài loại (hỏi đáp, người nổi tiếng, thơ, video, bài quá ngắn); 681 khúc `bd#NNNN-slug[-pNN]`, trung vị 3.627 ký tự, tối đa 6.508 (5 khúc vượt 6.000), 3,9 triệu ký tự.
- Làm sạch đã thực hiện:
  - Cắt khối bình luận Yahoo 360 lẫn trong thân bài (127 bài, ~3,9 triệu ký tự HTML). Đây là phần nhiễu lớn nhất; trước khi cắt có 997 khúc.
  - Bỏ ~630 đoạn/dòng bản dịch tiếng Anh, 11 đoạn thông báo quản trị (tên miền, email, tải phần mềm), 8 heading mồ côi.
  - Bỏ ảnh, liên kết, URL trần, thẻ HTML sót, đường kẻ chấm; đổi bullet Wingdings (`ü`) thành `- `; nối dòng cứng; đổi đoạn in đậm/viết hoa ngắn thành heading.
  - Không sửa chính tả của tác giả, để trích dẫn khớp nguyên văn.
- Báo cáo: `output/buu-dinh/chunking-report.json`, `dropped-paragraphs.json` (mọi đoạn bị bỏ kèm lý do, để duyệt), `selected.json` (bài giữ/loại và lý do).
- Validator: `validate_kb.py` ra `lỗi: 0` với 1.345 khúc nguồn.

Hạn chế đã biết:
1. Ảnh bị bỏ, chưa OCR; ảnh có thể chứa bảng hoặc sơ đồ.
2. Lọc bài theo tiêu đề (heuristic); 8 bài thêm tay bằng `INCLUDE_IDX`. Có thể còn thiếu hoặc thừa vài bài.
3. Cắt bình luận làm mất câu trả lời của tác giả trong phần bình luận (có thể có ý giải lá số cụ thể). Chấp nhận, vì đó là Q&A.
4. ~30 khúc có đoạn "Trả lời câu hỏi" do tác giả chèn vào thân bài; còn lại, chưa gắn cờ.
5. `stars_in_title` nhận `tu-vi` ở 98 khúc vì chữ "Tử Vi" trong tên blog/chủ đề; không dùng trường này một mình để chọn khúc cho sao Tử Vi.
6. Khúc ghép nhiều mục nhỏ (ví dụ "Nhóm Thị Phi" cùng khúc với "Nhóm Bất Ngờ"); khi viết thẻ chỉ trích đoạn liên quan.

Việc còn lại của Pha 0 (nhỏ):
- Duyệt tay ~30 dòng ngẫu nhiên của `dropped-paragraphs.json` (mục tiêu: 0 đoạn lý thuyết bị bỏ nhầm).
- Đã chốt: commit khúc [BĐ] (~3,9 MB) và cả `output/buu-dinh/` (29 MB gồm raw HTML), không ignore.

## 3. Pha 1 — Phía đọc hiểu nhãn [BĐ]

Làm trước khi có thẻ nào mang [BĐ] vào bài, nếu không `kiem_bai.py`/`kiem-nguon` sẽ báo lỗi hoặc bỏ sót. Đã xong: `LABEL_RE` trong `validate_kb.py` và `kb_the.py`, `Book("bd")`, `SOURCE_LABELS`.

| Việc | File | Ghi chú |
|---|---|---|
| Cho phép `cross: [td, npl, bd]` | `_meta/schema.md`, mục 2 | Validator đã nhận; sửa tài liệu. |
| Mô tả khúc `bd#` và nhãn `[BĐ]` | `_meta/schema.md` mục "Nguyên văn"/"Đối chứng" | |
| `kiem_bai.py` coi [BĐ] như [TĐ]/[NPL]: chỉ hợp lệ trong dòng đối chứng, không dùng bác TB/TL | `scripts/kiem_bai.py` | Có `--self-test`; thêm ca [BĐ]. |
| `lay_mau_nguon.py` lấy mẫu cả dòng [BĐ] | `scripts/lay_mau_nguon.py` | |
| Hướng dẫn agent: [BĐ] chỉ đối chứng | `.claude/agents/{xem-tu-vi,kiem-nguon,tra-the}.md`, `SKILL.md` | Giữ ràng buộc "không dùng kiến thức ngoài thẻ". |
| `tong-luan` không dùng [BĐ] | `.claude/agents/tong-luan.md`, E-check trong `kiem_bai.py` | Mục 0 hiện chỉ cho TB/TL/[Claude]; giữ nguyên. |
| CLAUDE.md: bảng bố cục, quy tắc nguồn mục 2 | `CLAUDE.md` | Thêm [BĐ] vào danh sách nhãn đối chứng. |
| `tra_cuu.py --pack` không làm vỡ khi thẻ có [BĐ] | đã kiểm với thang-pham: chạy được | Chạy `--self-test` các script. |

Kiểm xong pha: `--self-test` của mọi script đạt; `validate_kb.py` `lỗi: 0`; `--pack` + `kiem_bai.py` trên thang-pham-v3 không phát sinh lỗi mới.

## 4. Pha 2 — Gắn [BĐ] vào thẻ sẵn có (ưu tiên cao, giá trị chắc)

Mục tiêu: mỗi thẻ sao/cách cục đã có mà [BĐ] có bài riêng thì thêm một vài dòng `[BĐ]` vào `## Đối chứng` và một đoạn nguyên văn.

Thứ tự:
1. **Thẻ sao (`10-stars/`, 111 thẻ).** Tập trước: sao có bài riêng của BĐ (khúc mà tiêu đề có tên sao, ngoài `tu-vi`): Bạch Hổ, Cự Môn, Thiên Cơ, Thái Âm, Liêm Trinh, Thiên Lương, Thái Dương, Tấu Thư, Thất Sát, Lộc Tồn, Thiên Hình, Đào Hoa, Vũ Khúc, Hóa Kỵ… (59 sao có ít nhất một khúc). Dùng `dump_chunks.py --grep` hoặc `stars_in_title` để lấy khúc.
2. **Thẻ cách cục / combo (`30-combos/`, 23 thẻ)**: bộ sao BĐ viết thành bài ("Bộ Thiên Hình Thiên Diêu", "Bộ Không Kiếp", "Dương Lương Mão Dậu", "Liêm Tham Tỵ Hợi"…) thêm Đối chứng vào thẻ tương ứng nếu có.
3. **Thẻ cung (`20-palaces/`, 364 thẻ):** chỉ khi BĐ có đoạn nói đúng bộ sao tại đúng cung; làm sau cùng, theo nhu cầu.

Quy trình mỗi thẻ (nhỏ, lặp lại được, giao sub-agent):
1. Lấy các khúc `bd#` có sao đó; đọc phần liên quan.
2. Viết 2–5 dòng `[BĐ]` rút gọn trong `## Đối chứng`. Chỉ ghi ý có thật trong khúc; ý lệch TB/TL nêu rõ "lệch".
3. Thêm 1–3 đoạn trích nguyên văn ≤ 400 ký tự vào `## Nguyên văn`, id khúc vào `chunks:` và `cross: [..., bd]`.
4. `validate_kb.py` đến `lỗi: 0`.

Đo hiệu quả: số thẻ có [BĐ] / số thẻ sao có khúc BĐ; theo dõi bằng script nhỏ đếm thẻ có `bd` trong `cross`.

## 5. Pha 3 — Thẻ mới cho nội dung chỉ [BĐ] có

Chỉ làm khi có nhu cầu từ luận giải thật (thang-pham và các lá số sau), không làm hàng loạt.
- Mẫu đã có: `30-combos/nhom-thi-phi.md`.
- Ứng viên (theo tiêu đề bài): các "nhóm sao" khác trong `bd#0516` (Nhóm Bất Ngờ…), bài "Tuần và Triệt", "Hóa Kỵ", "Vô Chính Diệu", "Thái Tuế", "Kiếp Sát", "La Võng".
- Vấn đề cần quyết: thẻ combo hiện bắt buộc `primary` ⊆ `[tb, tl]`. Với khái niệm chỉ [BĐ] có, hoặc (a) không tạo thẻ (chỉ Đối chứng vào thẻ sao), hoặc (b) mở `primary` cho `bd` với nhãn cảnh báo. Đã chốt (a). `nhom-thi-phi.md` giữ làm mẫu vì phần chính dựa trên TB/TL.

## 6. Pha 4 — Chọn thẻ theo lá số (`tra_cuu.py`)

Hiện thẻ `nhom-thi-phi` được chọn cho Mệnh/Thân của thang-pham theo luật cũ (≥2 sao thẻ trong tam hợp + xung chiếu, ≥1 sao tại cung). Không cần đổi code nếu Pha 2 chỉ thêm dòng vào thẻ sẵn có (thẻ vẫn được chọn như trước, ngữ cảnh dài hơn một chút).

Cần theo dõi ngân sách ngữ cảnh: mỗi thẻ thêm vài dòng [BĐ] và 1–3 đoạn nguyên văn làm gói `--pack` phình. Đo bằng cảnh báo ngân sách của `tra_cuu.py --pack`; nếu vượt thì chuyển đoạn nguyên văn [BĐ] ra thẻ riêng không đưa vào gói (chỉ `kiem-nguon` đọc).

## 7. Pha 5 — Thử trên thang-pham và đánh giá

1. Dựng lại gói: `tra_cuu.py --pack output/luan-giai/thang-pham-v3.json <D>/`.
2. Chạy lại lượt B (Mệnh, Thân) bằng `xem-tu-vi`, rồi `ghep_bai.py`, `kiem_bai.py` (`lỗi: 0`), `kiem-nguon` (25 mẫu).
3. So sánh với bản cũ (không [BĐ]): bài có thêm gì ở Đối chứng, có dòng [BĐ] nào bị `kiem-nguon` đánh `lệch ý`/`sai nhãn`, [BĐ] có lọt vào phần chính hay mục 0 không.
4. Tiêu chí đạt: `kiem_bai` lỗi 0; `kiem-nguon` không có mẫu [BĐ] sai; không dòng [BĐ] nào bác TB/TL; mục 0 không có [BĐ].
5. Nếu đạt thì mở rộng sang lá số khác; nếu không thì sửa quy tắc ở Pha 1 trước khi làm Pha 2 tiếp.

## 8. Rủi ro

| # | Rủi ro | Cách giảm |
|---|---|---|
| 1 | [BĐ] là blog có ý kiến cá nhân, văn nói; có thể mâu thuẫn TB/TL | Chỉ đối chứng; luôn nêu cả hai; `kiem-nguon` kiểm nhãn. |
| 2 | Văn bản OCR/gõ lỗi chính tả, dấu rời | Giữ nguyên để khớp trích; chọn đoạn nguyên văn sạch. |
| 3 | Lọc theo tiêu đề bỏ sót/nhầm bài | Duyệt `selected.json`; chỉnh `INCLUDE_IDX`/`NOT_THEORY`, chạy lại (script idempotent). |
| 4 | Bài blog bị sửa sau khi crawl | `updated` lưu trong manifest; chạy lại crawl, id `bd#` theo thứ tự ngày đăng nên ổn định khi thêm bài mới ở cuối; bài chèn giữa chừng sẽ làm lệch NNNN: nếu vậy phải cập nhật `chunks:` của thẻ. |
| 5 | Gói ngữ cảnh phình, vượt ngân sách | Pha 4. |
| 6 | Người dùng không muốn nguồn blog trong bài luận | Công tắc: `kiem_bai`/agent bỏ qua dòng [BĐ] nếu cần; [BĐ] chỉ ở mục Đối chứng nên dễ tắt. |

## 9. Thứ tự đề xuất và ước lượng

1. Pha 0 phần còn lại + `.gitignore` (nhỏ).
2. Pha 1 (vừa): sửa 6–7 file, có self-test.
3. Pha 5 thử sớm với `nhom-thi-phi` trên thang-pham để xác nhận quy trình trước khi nhân rộng.
4. Pha 2 nhóm sao có bài riêng (~15–25 thẻ), giao sub-agent từng lô 5 thẻ, validate sau mỗi lô.
5. Pha 3–4 theo nhu cầu.

Không commit/gộp vào `main` trước khi Pha 1 và bước thử ở mục 3 đạt.
