# Báo cáo chạy thử tổng luận (Z7)

Ngày 2026-09-29. Plan: [plan-tong-luan.md](plan-tong-luan.md). Bài thử: `thang-pham-v3`
(bài ghép sẵn người dùng tải lên, chép vào `output/luan-giai/thang-pham-v3.md`,
gitignore). Không có thư mục `phan-*.md` và gói gốc của bài này.

## 1. Số đo

| Chỉ số | Plan ước | Đo được |
|---|---|---|
| Bài ghép | 150–210 KB | **405 KB** (3.153 dòng, hạn hai năm 2026–2027), 223 dòng Tổng kết (tổng ~64.000 ký tự, TB 288/dòng) |
| `tong-luan-nguon.md` chưa cắt | — | 114 KB (~60 nghìn token), 54 mục, 222 đơn vị |
| Sau khi cắt mức 1 (bỏ Tổng kết từng sao ở 5.x) | ≤ 30 KB | **86 KB** (~45 nghìn token) |
| Mức cắt sâu hơn (đo, không dùng) | — | mức 2: 71 KB; mức 3 (chỉ dòng Tổng kết của khối): 44 KB |
| Lượt Z (`tong-luan`, Sonnet) | ≤ 6 lượt gọi | 5 lượt gọi công cụ, 71 nghìn token (số `subagent_tokens` của harness), 66 giây |
| Mục 0 | 9.000 ký tự, trần 10.000 | **7.508 ký tự**, `lỗi: 0`, `cảnh báo: 0` |
| Ý bị bỏ vì không có TB/TL | — | 1 (mục 4.24 "Quy tắc không áp dụng") |

⛔ Nguồn vượt 30 KB sau khi cắt → dừng hỏi người dùng. Người dùng chọn **mức 1, trần
90 KB** (giữ đủ nhất, gấp đôi token vào so với mức 3). `TRAN` và `TRAN_TONG_LUAN` đã
nâng lên 90.000. Đọc cả bài thay vì file nguồn sẽ tốn khoảng 230 nghìn token.

## 2. Lỗi tìm thấy khi chạy trên bài thật (đã sửa)

1. `trich_tong_ket.py` chỉ nhận thư mục `phan-*.md` → thêm nhận thẳng bài đã ghép
   (`<bài>.md` → `<bài>/pack/tong-luan-nguon.md`).
2. Tiêu đề `### 7.1.6. Tổng kết năm 2026` bị gắn vào mục 7.1.5 → khối "Tổng kết" có
   đánh số giờ thuộc **mục cha** (7.1).
3. **Nặng nhất:** `nhãn mục` chỉ tính gạch đầu dòng trực tiếp của mục, nên 7.1, 7.2
   (tổng kết năm) và 2.3, 3.2 (khối "Tổng kết cung Mệnh/Thân" đặt dưới mục "Sao hội
   chiếu") ra "không có nhãn sách" → theo luật nhãn, agent sẽ bỏ hết tổng kết năm và
   tổng kết Mệnh, Thân. Sửa: nhãn mục gồm cả mục con; mục có khối tổng kết mà vẫn không
   có TB/TL thì lấy cả nhóm mục cùng cha.
4. Không có cách chèn mục 0 vào bài đã ghép sẵn → thêm `ghep_bai.py --chen-z <bài.md>
   <phan-z.md> [<ra.md>]` (thay mục 0 cũ nếu có; kết quả y như ghép thư mục có `phan-z.md`).
5. File nguồn 86 KB quá một lần Read → agent `tong-luan` đọc theo khúc `offset`/`limit`
   trong cùng một message; phiên chính ghi sẵn điểm chia (ranh giới mục gần giữa file).

## 3. Đối chiếu nhãn (tay, 9 dòng)

So nhãn dòng mục 0 với `nhãn:`/`nhãn mục:` của đơn vị gốc trong `tong-luan-nguon.md`:
Sát Phá Tham `[TL]` ← `TL 3, NPL 1`; Triều Đẩu `[TB]` ← `TB 4, TĐ 1`; Đẩu Quân `[TL]` ←
`TL 4`; Mệnh thắng Thiên Di `[TL]` ← mục 4.12 `TL`; Phi Liêm `[TB][TL]` ← `TB 2, TL 1`;
Phụ Mẫu, Tài Bạch, Điền Trạch `[TB][TL]` ← nhãn mục có TB, TL; hạn 2027 `[TB]` ← 7.2.x.
Không thấy ý nào ngoài các dòng Tổng kết trong 9 dòng này. Mục "TB và TL nói khác nhau"
có một cặp (Thiên La), khớp gạch `[Claude]` trong khối Tổng kết cung Mệnh nói hai sách
hiểu khác; 6 cờ `TB≠TL?` còn lại agent không đưa vào vì Tổng kết không xác nhận.

## 4. Kiểm sau khi chèn

- `kiem_bai.py` bài trước khi chèn: `lỗi: 0`; sau khi chèn: `mục 0: 7508 ký tự`,
  `cảnh báo: 0`, `lỗi: 0` (không `--pack` vì không có gói gốc).
- Chạy lại `trich_tong_ket.py` trên bài đã có mục 0: file nguồn giống hệt (mục 0 không
  bị rút ngược).

## 5. Còn lại / có thể làm tiếp

- Trần 90 KB đo trên một bài hạn hai năm. Bài xem một năm có lẽ ~60–70 KB; bài có hạn
  tháng (mục 8) chưa đo.
- W8 chỉ kiểm được dòng có `**<Tên>:**` trùng tên mục; các dòng ở "Đúc kết", "Hạn năm"
  không có máy kiểm nhãn, chỉ trông vào agent và đối chiếu tay.
- `kiem-nguon` chưa lấy mẫu mục 0 (plan để ngỏ); đối chiếu tay ở mục 3 thay thế lần này.
