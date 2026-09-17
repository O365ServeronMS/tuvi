# Cách đọc ảnh lá số Tử Vi (web)

> Dự án hướng dẫn người dùng lập lá số ở **thienluong.net** (xem README).
> **Chưa có ảnh lá số mẫu trong repo.** Tài liệu này viết theo kinh nghiệm
> chung về cách các trang lập lá số tiếng Việt (ví dụ tuvi.vn, tuviso.com,
> lasotuvi.vn...) trình bày lá số, không đối chiếu trực tiếp với một ảnh cụ
> thể nào. Khi có ảnh lá số thật, **cần người dùng xác nhận lại từng mục dưới
> đây và chỉnh sửa nếu trang web họ dùng vẽ khác đi** (đặc biệt là hướng vẽ
> Đại Hạn và ký hiệu miếu/hãm, hai chỗ khác biệt nhiều nhất giữa các trang).

## 1. Khung tổng quát: lưới vuông 4×4

Lá số vẽ trên một hình vuông chia 4×4 = 16 ô:

- **12 ô viền ngoài** — mỗi ô là một cung, vị trí cố định theo 12 địa chi
  (xem mục 2), không đổi dù lá số của ai.
- **4 ô giữa** (2×2) — không phải cung, dùng ghi thông tin lá số:
  - Họ tên, giới tính, âm lịch/dương lịch ngày giờ sinh.
  - **Cột giữa ghi tuổi và Cục**: tuổi (can chi năm sinh) và Ngũ Hành Cục
    (ví dụ "Thủy Nhị Cục", "Hỏa Lục Cục").
  - Mệnh chủ, Thân chủ (sao chủ quản theo cung Mệnh/Thân).
  - Có trang còn in thêm bảng Đại Hạn/Tiểu Hạn dạng danh sách ở đây thay vì
    ghi trong từng ô cung.

## 2. Vị trí 12 cung trên lưới (cố định theo địa chi)

12 địa chi có vị trí cố định trên lưới, không phụ thuộc lá số; cung nào rơi
vào địa chi nào thì phụ thuộc giờ/tháng/năm sinh (an theo Cục). Cách sắp xếp
phổ biến nhất (đi theo chiều kim đồng hồ, bắt đầu từ góc trên bên trái):

```
   Tỵ      Ngọ      Mùi      Thân
 (hàng trên, trái → phải)

 Thìn                          Dậu
 (cột trái, trên)    (cột phải, trên)

 Mão                           Tuất
 (cột trái, dưới)    (cột phải, dưới)

   Dần      Sửu      Tý       Hợi
 (hàng dưới, trái → phải)
```

Tức là: hàng trên (trái→phải) Tỵ, Ngọ, Mùi, Thân; cột phải (trên→dưới) Dậu,
Tuất; hàng dưới (phải→trái) Hợi, Tý, Sửu, Dần; cột trái (dưới→trên) Mão,
Thìn. Đây là vị trí "bàn cờ" cố định — cung Mệnh của một lá số cụ thể có thể
rơi vào bất kỳ ô nào trong 12 ô này.

Từ cung Mệnh, 11 cung còn lại xếp theo chiều thuận, tức thuận chiều kim
đồng hồ trên lưới trên (Tân Biên: "Sau khi đã an Mệnh, bắt đầu theo chiều
thuận", tb#0003; "chiều thuận (thuận chiều kim đồng hồ)", tb#0002):
Mệnh, Phụ Mẫu, Phúc Đức, Điền Trạch, Quan Lộc, Nô Bộc, Thiên Di, Tật
Ách, Tài Bạch, Tử Tức, Phu Thê, Huynh Đệ, rồi quay lại Mệnh. Xem id/tên
chuẩn của 12 cung này tại [`palaces.md`](palaces.md).

Cung Thân không có ô riêng: Thân luôn trùng với một trong 6 cung Mệnh, Phu
Thê, Quan Lộc, Thiên Di, Tài Bạch, Phúc Đức (theo giờ sinh); ô đó ghi thêm
nhãn "Thân" bên cạnh tên cung gốc.

## 3. Ghi miếu/hãm của sao

Mỗi sao trong ô cung thường có một chữ hoặc ký hiệu ngay sau tên để chỉ độ
sáng tại vị trí đó:

- Chữ tắt: **M** = Miếu, **V** = Vượng, **Đ** (hoặc **Đắc**) = Đắc địa,
  **H** = Hãm địa. Một số trang thêm **B** = Bình hòa (không miếu không hãm).
- Hoặc ký hiệu dấu: **+** (miếu/vượng/đắc, tốt) và **-** (hãm, xấu); có
  trang chia ba mức `++`/`+`/`-`.

Không có quy ước thống nhất giữa các trang; cần đối chiếu chú thích/legend
của từng trang trước khi đọc.

## 4. Tuần, Triệt

Tuần Không và Triệt Không mỗi sao trấn giữ **hai cung liền kề** (không phải
một ô), nên thường được vẽ như một **đường kẻ (nét đứt hoặc nét đậm) cắt
ngang qua cạnh chung giữa hai ô cung** bị trấn, thay vì nằm gọn trong một ô
như các sao khác. Có trang ghi chữ "Tuần" / "Triệt" nhỏ ở mép ô thay vì vẽ
đường kẻ. Cần xem legend của trang để biết cách trang đó thể hiện.

## 5. Đại Hạn, Tiểu Hạn

- **Đại Hạn** (10 năm/cung): mỗi ô cung thường ghi một cặp số tuổi (ví dụ
  "3-12", "13-22"...) ở một góc của ô — thường là góc trên hoặc góc ứng với
  hướng an Đại Hạn. Tân Biên 10.1 (tb#0013): dương nam, âm nữ đi chiều
  thuận; âm nam, dương nữ đi chiều nghịch. Cách thường dùng ghi số Cục ở
  cung Mệnh; cách thứ hai ghi số Cục ở cung kế bên (Phụ Mẫu hoặc Huynh Đệ).
  **Chép đúng số tuổi trang web in ra**, không tự tính lại; nếu dãy số
  không đi đều 10 năm một cung thì hỏi lại người dùng.
- **Tiểu Hạn** (1 năm/cung): nếu trang có hiển thị, thường ghi ở góc khác
  của ô hoặc trong bảng riêng ở 4 ô giữa, không lồng chung với Đại Hạn.

## 6. Bảng viết tắt tên sao

Không lặp lại danh sách viết tắt ở đây để tránh lệch với sổ gốc khi sổ gốc
cập nhật. Tra cột **`viết tắt`** trong [`stars.md`](stars.md) — cột này ghi
đúng cách viết ngắn gọn hay gặp trên web (ví dụ "Tử" = Tử Vi, "Đồng" = Thiên
Đồng, "K.Dương" = Kình Dương). Cột này **không** dùng để dò tự động trong
nguyên văn (xem ghi chú đầu `stars.md`), chỉ dùng khi đọc ảnh lá số.

## 7. Thứ tự đọc một lá số theo SKILL

Xem quy trình 7 bước đọc/luận đầy đủ tại [`../SKILL.md`](../SKILL.md); tài
liệu này chỉ phục vụ bước đầu tiên — chuẩn hoá ảnh lá số thành bảng dữ liệu
trước khi tra cứu thẻ.
