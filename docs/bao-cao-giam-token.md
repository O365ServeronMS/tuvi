# Báo cáo giảm token luận giải (G6)

Ngày 2026-09-24. Plan: [plan-giam-token.md](plan-giam-token.md). Lá số thử:
`output/luan-giai/thang-pham-2026.json`, thư mục `output/luan-giai/thang-pham-2026-v2/`.

**G6 dừng giữa chừng.** Lượt A chạy xong. B, C, D chạy song song thì cả ba bị
ngắt vì hết hạn mức phiên (HTTP 429): B và D kịp ghi file, C không ghi được gì.
Người dùng quyết định không gọi lại sub-agent để thử tiếp, vì quá tốn token.
Số liệu dưới đây đo trên những gì đã chạy.

## 1. Số trước và sau

Mốc "trước" là một sub-agent luận cả bài (plan mục 1). "Sau" là 4 lượt, đo
bằng `scripts/do_token.py` trên transcript sub-agent.

| Chỉ số | Trước (1 agent) | A | B | C (dở) | D | A lần 1 (429) |
|---|---|---|---|---|---|---|
| Số lượt gọi model | 64 | 55 | 15 | 12 | 4 | 47 |
| cache_read | 5,97 tr | 4,68 tr | 1,41 tr | 0,99 tr | 0,07 tr | 4,02 tr |
| cache_write | 365 ng | 747 ng | 159 ng | 157 ng | 81 ng | 781 ng |
| output | 61 ng | 129 ng | 50 ng | 27 ng | 39 ng | 62 ng |
| Ngữ cảnh lớn nhất | 167 ng | 173 ng | 166 ng | 165 ng | 89 ng | 174 ng |
| Bash có `90-source` | ~15 | 0 | 0 | 0 | 0 | 0 |
| File ghi được | cả bài | phan-a, phan-a-cach-cuc, tom-tat-a | phan-b (đủ 6 cung) | — | phan-d (đủ) | — |

Tổng 5 transcript: 11,17 triệu cache_read, 1,93 triệu cache_write, 307 nghìn
output. Riêng 4 lượt không tính lần A hỏng: 7,15 triệu cache_read.
**Chưa rẻ hơn cách cũ**, dù đã bỏ được toàn bộ phần grep `90-source`.

## 2. Kết quả từng mục tiêu

| Chỉ số | Mục tiêu | Kết quả | Đạt |
|---|---|---|---|
| Số lượt mỗi sub-agent | ≤ 15 | A 55, B 15, C ≥12 (dở), D 4 | Không (A) |
| Ngữ cảnh lớn nhất | ≤ 120 ng | A 173, B 166, C 165, D 89 | Không (A, B, C) |
| Bash có `90-source` | 0 | 0 ở cả 5 transcript | Đạt |
| Đọc thẻ gốc `10-`…`60-` | 0 | 0 ở cả 5 transcript | Đạt |
| `kiem_bai.py` bài hoàn chỉnh | `lỗi: 0` | Bài ghép A+B+D: `lỗi: 0, cảnh báo: 49`; 188 câu trích chèn và khớp nguyên văn; mục 8 tự sinh 184 thẻ | Đạt trên phần có |
| Độ phủ | 12 cung, cách cục, hạn 2026 | Thiếu Tài Bạch, Tử Tức, Phu Thê, Huynh Đệ (lượt C) | Không |
| Truy nguồn 20 dòng | ghi từng dòng | Chưa làm, vì bài chưa đủ | Không |

Cảnh báo W1: 48 cái nằm ở `phan-d.md`, phần lớn là dòng ghi chú phương pháp
(ví dụ "Cung tiểu hạn Thìn do script tính theo Tân Biên 10.3") chứ không phải
nhận định. A, B không có W1 đáng kể.

Bài ghép (thiếu C) dài 208 KB, dài hơn bài cũ 144 KB (bài cũ gồm cả 2027):
độ chi tiết không giảm.

## 3. Vì sao chưa đạt (đọc từ transcript)

1. **Gói lượt A quá lớn so với ngân sách thật.** Ước tính 99 nghìn token
   (byte/1,9), nhưng đọc xong gói ngữ cảnh đã khoảng 130 nghìn. Ngữ cảnh chạm
   ~170 nghìn và bị nén 3 lần (172→31, 164→52, 161→44 nghìn); sau mỗi lần nén
   agent đọc lại gói. `quy-tac.md` (~50 nghìn) chiếm gần nửa gói A và phải đọc
   theo khúc. Tỷ lệ 1,9 byte/token đánh giá thấp chi phí thật của gói.
2. **Agent tra `trich.json` để biết mã Q nói gì.** Từ khi bỏ xem trước (sửa
   G3), dòng `Trích:` chỉ còn mã. Số lệnh đụng `trich.json`: A 12, A lần 1 14,
   B 5, C 2, D 0. Mỗi lần in ra vài chục nghìn token vào ngữ cảnh.
3. **Agent đọc mã nguồn `kiem_bai.py`** để hiểu luật W1 (A 2, B 1, C 3 lệnh).
4. B, C đọc thêm khúc `quy-tac.md` không được giao (qua `sed`), vì
   `tom-tat-a.md` nhắc quy tắc theo tên.

D là lượt duy nhất đạt mọi chỉ số: đọc 3 file, viết thẳng, 4 lượt, 89 nghìn.

## 4. Các dòng lọc đáng ngờ đã sửa ở G2

- R4 (sao đi kèm): bộ nhận sao viết tắt ("Tả Hữu", "Xương Khúc", "Kình Đà"…)
  ban đầu bỏ sót, làm lọc nhầm dòng có sao kèm; đã sửa `r4_detector`.
- P1/P2 (thẻ phú): thẻ phú không có `stars` trong frontmatter bị lọc nhầm; đã
  thêm điều kiện chặn.

Sau G2, gói lọc 101 dòng (51 sai miếu/hãm, 43 sai giới tính, 7 thiếu sao kèm),
ghi đủ ở `loc-bo.md`; `--kiem-pack` xác nhận mọi thẻ `report()` liệt kê đều có
trong gói trừ 7 thẻ phú nữ mệnh.

## 5. Còn chưa đạt / việc có thể làm tiếp (chưa làm, chờ người dùng quyết)

- Hạ ngữ cảnh lượt A dưới 120 nghìn: tách `quy-tac.md` hoặc cách cục sang lượt
  riêng; hạ ngân sách ước tính (đổi hệ số 1,9 theo số đo thật).
- Cho agent biết mã Q nói gì mà không phải dump `trich.json`: ví dụ một dòng
  tóm vài chữ đầu câu trích (chính là phần xem trước đã bỏ ở G3 — cần người
  dùng quyết lại, vì đó là quyết định đã duyệt).
- Ghi luật W1 thẳng vào `xem-tu-vi.md` để agent khỏi đọc mã `kiem_bai.py`.
- Chạy lại lượt C và truy nguồn 20 dòng khi có hạn mức.
- Lượt A báo cung Sửu ghi "Quan Phủ" hai lần. Đây là lỗi hiển thị của
  `tra_cuu.py` (tên "Quan Phủ" bỏ dấu trùng id `quan-phu` của Quan Phù), không
  phải lỗi đọc ảnh. Một phiên khác đã sửa, commit cùng đợt push lên main; bản
  sửa đổi đúng 2 dòng output so với mốc ("Quan Phù, Quan Phủ"), self-test 7/7.
  Gói `thang-pham-2026-v2` dựng trước bản sửa này.
