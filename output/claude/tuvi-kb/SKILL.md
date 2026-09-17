---
name: xem-tu-vi
description: Luận giải lá số Tử Vi Đẩu Số từ ảnh lá số (ví dụ thienluong.net) chỉ bằng knowledge base tuvi-kb (Tân Biên, Thiên Lương; đối chứng Trần Đoàn, Nguyễn Phát Lộc), có nhãn nguồn trên từng nhận định. Dùng khi người dùng gửi ảnh hoặc dữ liệu lá số Tử Vi, hỏi về cung Mệnh, Thân, 12 cung, cách cục, đại hạn, tiểu hạn hay vận hạn một năm.
---

# Luận giải lá số Tử Vi bằng `tuvi-kb`

Mọi đường dẫn trong tài liệu này tính từ thư mục chứa file này (thư mục
skill). Thư mục tự chứa đủ thẻ, chỉ mục và script, chép đi đâu cũng dùng
được, không phụ thuộc repo gốc. Kiến thức luận giải **chỉ** lấy từ các thẻ
`10-stars/` đến `60-phu/`; không dùng hiểu biết Tử Vi ngoài thẻ.

## Ràng buộc bắt buộc

1. **Không luận khi chưa có bảng lá số đã được người dùng xác nhận.** In
   bảng chuẩn hoá (Bước 1), hỏi đúng/sai, dừng lại chờ trả lời.
2. **Mỗi nhận định mang nhãn nguồn** sao chép từ gạch đầu dòng của thẻ:
   `[TB]` Tân Biên, `[TL]` Thiên Lương là nguồn chính; `[TĐ]` Trần Đoàn,
   `[NPL]` Nguyễn Phát Lộc chỉ lấy từ mục **Đối chứng**. Ghép hai thẻ hoặc
   suy ra điều thẻ không viết thì ghi rõ `(suy luận của Claude, không phải
   nguyên văn sách)`.
3. **TB và TL nói khác nhau thì nêu cả hai**, không tự chọn. `[TĐ]`/`[NPL]`
   chỉ để đối chiếu, không dùng để bác TB/TL.
4. **Chỉ dùng gạch đầu dòng có điều kiện thật sự thỏa lá số**: đúng vị trí
   (địa chi), đúng miếu/hãm (sáng sủa/mờ ám), đúng nam/nữ, đúng sao đồng
   cung hay hội chiếu như thẻ ghi. Thẻ nói "gặp X" mà lá số không có X thì
   bỏ dòng đó.
5. Không có thẻ cho một bộ sao thì nói thẳng "sách trong kho không có đoạn
   riêng cho trường hợp này", không bịa.

## Bước 1 — Đọc ảnh, in bảng, chờ xác nhận

Đọc ảnh theo [`00-index/chart-reading.md`](00-index/chart-reading.md). In:

- Giới tính, năm sinh âm lịch (can chi), âm/dương nam/nữ, Cục, Bản Mệnh (nạp âm).
- Mệnh ở cung (địa chi) nào, Thân cư cung nào.
- Bảng 12 dòng: địa chi | tên cung | số đại hạn | sao tọa thủ kèm miếu/hãm | Tuần/Triệt.
- Năm người dùng muốn xem hạn (hỏi nếu chưa nói).

Ô nào đọc không chắc thì đánh dấu `?` và hỏi riêng. Đọc sai một sao làm
sai toàn bộ phần sau, nên không được bỏ qua bước xác nhận.

## Bước 2 — Ghi lá số ra JSON và chạy script tra cứu

Sau khi người dùng xác nhận, ghi file JSON (ở thư mục tạm, không ghi vào
kho) theo mẫu:

```json
{
  "gioi_tinh": "nam",
  "nam_sinh": 1984,
  "nam_xem": 2026,
  "menh": "dan",
  "than": "ngo",
  "cung": {
    "dan": {"ten": "Mệnh", "dai_han": 2, "sao": ["tu-vi:V", "thien-phu:M", "loc-ton", "ta-phu"]},
    "mao": {"ten": "Phụ Mẫu", "dai_han": 12, "sao": ["thai-am:H", "kinh-duong:H"]}
  }
}
```

- Đủ 12 cung. Khoá địa chi: `ty`=Tý, `suu`, `dan`, `mao`, `thin`, `ti`=Tỵ,
  `ngo`, `mui`, `than`, `dau`, `tuat`, `hoi` (hoặc tên có dấu).
- `sao`: id trong [`00-index/stars.md`](00-index/stars.md) (hoặc tên đầy
  đủ); miếu/hãm ghi sau dấu `:`. Tuần/Triệt ghi `tuan`/`triet` ở **cả hai**
  cung bị án. Không ghi sao lưu (script tự an theo `nam_xem`).
- `nam_sinh`, `nam_xem`: năm âm lịch dạng số (sinh trước Tết thì lấy năm trước).

Chạy (Python 3, không cần thư viện):

```bash
python <thư-mục-skill>/scripts/tra_cuu.py <file-la-so>.json
```

Script tự tìm thẻ theo vị trí của chính nó, chạy từ thư mục nào cũng được.

Script kiểm lá số (tên sao lạ, thứ tự 12 cung sai, Thân cư cung không hợp
lệ) và báo lỗi thì **sửa theo ảnh hoặc hỏi lại người dùng**, không ép cho
chạy. Khi hợp lệ, script in theo từng cung: sao tọa thủ, tam hợp, xung
chiếu, nhị hợp, giáp; rồi danh sách thẻ cần đọc; phần Hạn (đại hạn, tiểu
hạn, sao lưu); và danh mục quy tắc. **Chỉ đọc thẻ script liệt kê** (và thẻ
quy tắc chọn ở Bước 5); không tự dò tên file.

Mức khớp của thẻ cung:

| mức | nghĩa | cách dùng |
|---|---|---|
| đủ | mọi sao của thẻ tọa thủ tại cung | dùng, sau khi kiểm vị trí/miếu hãm |
| đủ, mượn xung chiếu | cung Vô Chính Diệu, chính tinh lấy từ cung xung chiếu | dùng, nói rõ là mượn |
| hội chiếu | sao của thẻ nằm rải trong cung + tam hợp + xung chiếu | đọc Điều kiện: thẻ viết "đồng cung" thì không dùng |
| một phần | thẻ gom nhiều sao/dị tượng, lá số chỉ có vài sao | chỉ dùng dòng mà mọi sao trong dòng đều có mặt |

Thẻ cung ghi cả Tuần lẫn Triệt (viết "Tuần, Triệt án ngữ") chỉ cần cung có
một trong hai là khớp; script đã tính theo cách này.

Phú và cách cục script đưa ra là **ứng viên**: đọc mục Điều kiện thành
cách/Phá cách (combo) hoặc Giải nghĩa (phú) rồi mới kết luận có thành cách.

Không chạy được Python: tra tay bằng [`00-index/lookup.md`](00-index/lookup.md),
[`00-index/lookup-palaces.md`](00-index/lookup-palaces.md),
[`00-index/lookup-phu.md`](00-index/lookup-phu.md) theo đúng các mức khớp
trên; cột "bộ sao" là danh sách sao thẻ **có nhắc tới**, không phải khoá
phải trùng khít.

## Bước 3 — Mệnh và Thân

Đọc thẻ script liệt kê cho cung Mệnh và cung Thân cư (thẻ `20-palaces/menh-than/`
áp dụng cho cả cung Thân cư). Thứ tự: thẻ cung mức đủ → thẻ sao tọa thủ
(mục Vị trí miếu hãm, Gặp sao khác, Nam nữ) → phú → cách cục. Sau đó xét
sao hội chiếu từ tam hợp, xung chiếu theo
`50-rules/xem-mot-cung-phai-xem-ca-tam-hop-xung-chieu-nhi-hop.md` và
`50-rules/chinh-khong-bang-chieu-chieu-khong-bang-giap.md`.

## Bước 4 — 11 cung còn lại

Cùng cách làm cho từng cung. Người dùng chỉ hỏi vài cung thì chỉ luận các
cung đó (vẫn phải có Mệnh, Thân làm nền).

## Bước 5 — Quy tắc toàn lá số

Từ danh mục `50-rules/` script in ra, chọn thẻ có mục **Điều kiện** khớp
lá số (âm dương thuận/nghịch lý, Bản Mệnh sinh/khắc Cục, Mệnh ở sinh/vượng/
bại/tuyệt địa, Tuần Triệt, Vô Chính Diệu, Thái Tuế, nhị hợp...). Đọc mục
**Khi nào không áp dụng** trước khi dùng.

## Bước 6 — Hạn

Dùng phần Hạn của script:

- Đọc các thẻ hạn chung trước (`phuong-phap-luan-doan-van-han.md`,
  `menh-than-han-lien-he.md`, `dai-han-tieu-han-lien-he.md`...).
- Thẻ theo sao tại cung đại hạn, cung tiểu hạn, cung Lưu Thái Tuế.
- Tiểu hạn script tính theo Tân Biên 10.3; nếu ảnh lá số ghi khác thì hỏi
  lại, không tự chọn. Lưu đại hạn script không tính.
- Hạn chết, đám tang: chỉ nêu khi người dùng hỏi thẳng, và nêu nguyên điều
  kiện của thẻ, không phán đoán ngày tháng.

## Bước 7 — Viết bài

Cấu trúc: (1) bảng lá số đã xác nhận; (2) Mệnh, Thân; (3) từng cung;
(4) cách cục thành/phá; (5) hạn năm xem; (6) mục "Nguồn đã dùng" liệt kê
đường dẫn thẻ. Mọi câu nhận định theo đúng 5 ràng buộc ở đầu. Khi người
dùng hỏi "sách viết nguyên văn thế nào", trích từ mục Nguyên văn của thẻ
(có id khúc), không trích từ trí nhớ.
