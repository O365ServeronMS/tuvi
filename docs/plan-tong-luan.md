# Plan: Bản tổng luận lá số (lượt Z, đợt 3)

Tài liệu này là **đề bài đầy đủ** cho phiên Claude Code thực hiện. Phiên đó
không có ngữ cảnh cuộc trao đổi sinh ra plan, nên mọi quyết định, số liệu và
quy cách đều ghi ở đây. Soạn ngày 2026-09-29.

---

## 0. Đọc trước khi làm

1. Đọc `CLAUDE.md`, `.claude/agents/xem-tu-vi.md`, `output/claude/tuvi-kb/SKILL.md`
   (mục "Chế độ gói ngữ cảnh"), `docs/bao-cao-giam-token.md` và toàn bộ file này.
2. Làm theo thứ tự Z1 → Z7. Mỗi giai đoạn có **điều kiện xong**; chưa đạt thì
   chưa sang giai đoạn sau. Có hai điểm `⛔ DỪNG`: báo người dùng, chờ trả lời.
3. Commit sau mỗi giai đoạn, message tiếng Việt không dấu (`Z1: trich_tong_ket.py`).
4. `PYTHONIOENCODING=utf-8`, chỉ Python 3 stdlib. Mọi script mới/sửa có `--self-test`.
5. Không đọc nguyên bài luận giải đã ghép (150–210 KB); chỉ grep hoặc đọc theo đoạn.

## 1. Vì sao

- Bài ghép hiện tại (mục Cách đọc, 1–8) dài 150–210 KB, khoảng 100 nghìn token
  trở lên. Người dùng cần một bản đọc nhanh; phiên chính hiện chỉ trả 15 dòng
  tóm tắt dựng từ `tom-tat-a.md`, `tom-tat-r.md`.
- Cho một agent đọc lại cả bài để tổng luận thì tốn gần bằng một lượt A
  (xem `docs/bao-cao-giam-token.md`: A đọc 4,68 triệu cache_read). Cần làm rẻ:
  **script rút sẵn các dòng Tổng kết**, agent chỉ đọc phần rút đó.

## 2. Quyết định đã chốt với người dùng (không mở lại)

| Quyết định | Nội dung |
|---|---|
| Vị trí | Mục `## 0. Tổng luận` chèn vào bài ghép **ngay sau "Cách đọc bài này", trước mục 1**. |
| Chat | Phiên chính dán nguyên mục 0 vào chat khi gửi bài, **thay** cho tóm tắt 15 dòng hiện nay (vẫn kèm dòng tổng của `kiem-nguon.md`). |
| Độ dài | Mục tiêu **9.000 ký tự**, trần cứng **10.000 ký tự** (đếm `len()` chuỗi Unicode của thân mục 0, không tính dòng tiêu đề `## 0.`). Khoảng 5–6,5 nghìn token output. |
| Nhãn | Mục 0 **không dùng nhãn `[Claude]`**, không dòng `[Claude] Tổng kết`, không dòng `Nguồn:`, không bắt buộc trỏ số mục. Mỗi ý gắn `[TB]`, `[TL]` hoặc `[TB][TL]` theo sách mà ý đó dựa vào. Người đọc tự kéo xuống các mục dưới để đối chiếu. Đây là **ngoại lệ riêng cho mục 0** của ràng buộc nguồn số 2 trong `CLAUDE.md`; mọi mục khác giữ nguyên luật cũ. |
| Agent | Sub-agent mới **`tong-luan`, model Sonnet**. Không dùng `xem-tu-vi` (Opus), phiên chính không tự viết. |

Hệ quả của quyết định nhãn, phải giữ trong agent và kiểm bài:

- Ý chỉ đứng trên `[Claude]`, `[TĐ]`, `[NPL]` (không có gạch đầu dòng `[TB]`/`[TL]`
  nào đỡ trong đơn vị gốc) thì **không đưa vào mục 0**.
- TB và TL nói khác nhau thì viết thành hai gạch đầu dòng, một `[TB]`, một
  `[TL]`, không gộp, không chọn.
- Không thêm ý nào không có trong các dòng Tổng kết/tóm tắt đầu vào.

## 3. Luồng mới

```
Đợt 1: A, R   →  Đợt 2: B, C, E, D…, T…  →  ghep_bai + kiem_bai  →  kiem-nguon (+ sửa)
  →  Đợt 3: trich_tong_ket.py  →  tong-luan (Sonnet) ghi phan-z.md  →  ghep_bai + kiem_bai lại
  →  gửi file + dán mục 0 vào chat
```

Tổng luận chạy **sau** `kiem-nguon` và các vòng sửa, để nó rút từ bản đã sửa.

## 4. Ngân sách

| Phần | Ước lượng |
|---|---|
| `tong-luan-nguon.md` (đầu vào lượt Z) | ≤ 30 KB, khoảng 16 nghìn token |
| Chỉ dẫn agent + đọc lại để kiểm | khoảng 6 nghìn token |
| Output `phan-z.md` | 9.000 ký tự, khoảng 5–6,5 nghìn token |
| Số lượt gọi model mục tiêu | ≤ 6 (Read 1 lần, Write 1 lần, kiem_bai 1–2 lần) |

Tỷ lệ tiếng Việt khoảng 1,9 byte/token (G6 cho thấy số này hơi lạc quan). Các
số trên là **ước tính**: repo không có bài mẫu (`output/luan-giai/` gitignore),
phải đo lại ở Z7.

Phân bổ 9.000 ký tự (hướng dẫn, không kiểm máy):

| Tiểu mục | Ký tự |
|---|---|
| Đúc kết | ~600 |
| Mệnh và Thân | ~1.000 |
| Nền chung và cách cục | ~600 |
| Các cung (11 cung × ~400) | ~4.400 |
| Hạn năm (và tháng) | ~1.500 |
| TB và TL khác nhau; sách chưa có đoạn riêng | ~900 |

## 5. Các giai đoạn

### Z1 — `trich_tong_ket.py` (không tốn token model) ✅ xong

Đã làm khác plan ở ba điểm: ghép bằng `ghep_bai.ghep()` rồi mới rút (cùng thứ
tự với bài, bỏ qua mục "Tổng luận" nếu đã có); `nhãn mục:` in trên tiêu đề mọi
mục thay cho `nhãn cung:` trên khối tổng kết; khối "Tổng kết …" có đánh số
(`### 5.1.9. Tổng kết cung…`) vẫn tính vào mục đang mở.

File mới `output/claude/tuvi-kb/scripts/trich_tong_ket.py`, dùng `kb_the.py` nếu
có hàm hợp.

```
python3 $S/trich_tong_ket.py <thư-mục-bài> [--tran 30000]
→ ghi <thư-mục-bài>/pack/tong-luan-nguon.md, in số byte và ước token
```

Đọc các `phan-*.md` theo đúng thứ tự `ghep_bai.PHAN` (import hằng số, không chép
lại), **bỏ** `phan-z.md` nếu đã có. Với mỗi **đơn vị** (một tiêu đề `###`/`####`
có gạch đầu dòng nhãn), in:

```markdown
## 5.3. Tài Bạch — cung Thìn · nhãn mục: TB, TL, TĐ   ← giữ số mục; hợp nhãn sách mọi đơn vị
- **Vũ Khúc tọa thủ (miếu)** · nhãn: TB 3, TL 2, TĐ 1
  Tổng kết: <nguyên dòng [Claude] Tổng kết, bỏ tiền tố>
- **Tổng kết cung Tài Bạch**
  - <các gạch đầu dòng [Claude] của khối>
  Tổng kết: <dòng Tổng kết của khối>
- Khoảng trống: <dòng có "không có đoạn riêng">
```

- `nhãn:` đếm theo nhãn mở đầu gạch đầu dòng của đơn vị (`[TB]`, `[TL]`, `[TĐ]`,
  `[NPL]`; không đếm `[Claude]`).
- Đơn vị có nhãn `TB` và `TL` mà Tổng kết chứa cụm "khác" / "trái" / "còn TL"
  / "còn TB" thì gắn thêm cờ `· TB≠TL?` (gợi ý cho agent, không phải kết luận).
- Bỏ hẳn: mục "Cách đọc", mục 1 (bảng lá số), dòng `Nguồn:`, gạch đầu dòng nhãn
  sách (chỉ lấy dòng Tổng kết, đã đủ ý).
- Vượt `--tran` (mặc định 30.000 byte): bỏ dần Tổng kết từng sao **trong mục 5**
  (giữ khối "Tổng kết cung" và nhãn mục), in `CẢNH BÁO` kèm số byte trước/sau.
  Vẫn vượt thì in `CẢNH BÁO` và ghi nguyên, không cắt thêm.

Self-test: bài giả 3 mục (Mệnh, một cung có khối Tổng kết cung, một năm hạn),
kiểm đếm nhãn, cờ `TB≠TL?`, bỏ `Nguồn:`, thứ tự mục, nhánh cắt khi vượt trần.

**Điều kiện xong:** self-test đạt.

### Z2 — sub-agent `tong-luan` ✅ xong

Đã làm khác plan ở năm điểm (Z3 phải theo):
- `tools: Read, Write, Edit, Bash`: sửa lỗi kiểm bằng Edit, không Write lại cả file.
- Chỗ TB và TL vênh chỉ viết một lần, ở tiểu mục "TB và TL nói khác nhau" (cặp dòng
  `[TB]`/`[TL]`); dòng của cung ở "Các cung" chỉ giữ phần hai sách không vênh.
- Dòng ở tiểu mục "Sách chưa có đoạn riêng" **không mang nhãn**, bắt buộc chứa cụm
  "không có đoạn riêng" → E8 phải miễn các dòng này (như `MIEN_NHAN` của E5).
- Agent đọc số ký tự từ `kiem_bai.py` → Z3 phải in `mục 0: <n> ký tự` mỗi lần
  kiểm một bài/phần có mục 0. Trước khi xong Z3, đừng gọi agent (E5/E6 cũ sẽ báo
  lỗi mọi dòng của mục 0).
- Gộp nhiều đơn vị trong một câu thì nhãn là sách có ở **mọi** đơn vị bị gộp.

File mới `.claude/agents/tong-luan.md`: `model: sonnet`, `tools: Read, Write, Bash`.
Nội dung chính (viết thành chỉ dẫn, ngắn):

- Đọc **một** file: `pack/tong-luan-nguon.md`. Không đọc thẻ, không đọc bài
  ghép, không đọc `00-nen.md`, không đọc mã script.
- Ghi `phan-z.md` bằng **một** lần Write, khuôn:

```markdown
## 0. Tổng luận

Phần này gom các kết luận của bài bên dưới. Mỗi ý gắn nhãn sách mà nó dựa vào;
chi tiết và đường dẫn thẻ nằm ở các mục cùng tên phía dưới.

### Đúc kết
- [TB][TL] …
### Mệnh và Thân
### Nền chung và cách cục
### Các cung
- [TB] **Phụ Mẫu:** …
- [TL] **Phụ Mẫu:** … (khi TL khác TB)
### Hạn năm <năm>          ← nhiều năm thì mỗi năm một dòng tiêu đề; có tháng thì thêm "### Hạn tháng"
### TB và TL nói khác nhau
### Sách chưa có đoạn riêng
```

- Luật: như mục 2 "Hệ quả của quyết định nhãn". Nhãn một ý lấy từ `nhãn:` của đơn vị hoặc
  `nhãn mục:` của mục gốc, chỉ chọn trong `TB`, `TL`. Không có TB/TL thì bỏ ý.
- Mục tiêu 9.000 ký tự, **không vượt 10.000**. Thiếu chỗ thì gộp cung bình
  thường vào một dòng, giữ cung có kết luận mạnh/xấu rõ, giữ đủ mục TB≠TL.
- Giọng người đọc thường, như `xem-tu-vi.md`. Nhận định xấu nêu kèm điều kiện
  hóa giải nếu dòng Tổng kết có ghi.
- Trước khi trả: chạy `kiem_bai.py phan-z.md --pack <pack>` một lần, sửa đúng
  dòng bị báo. Trả đường dẫn và số ký tự, không dán nội dung.

**Điều kiện xong:** file agent có frontmatter hợp lệ; nội dung khớp mục 2.

### Z3 — `kiem_bai.py`: luật cho mục 0 ✅ xong

Đã làm: `muc0()` tìm phạm vi mục (từ `## 0. Tổng luận` đến tiêu đề `##` kế tiếp);
`kiem_muc0()` trả (lỗi, cảnh báo, số ký tự); `kiem()` giữ chữ ký cũ (chỉ trả lỗi).
Khi có mục 0, `run()` in thêm `mục 0: <n> ký tự …` và `cảnh báo: <m>` trước dòng
`lỗi:`. E8 miễn dòng "không có đoạn riêng" (theo Z2). W8 so tên in đậm với mục
nguồn theo tiền tố (`Mệnh` khớp cả `Cung Mệnh — …`), nhiều mục cùng tên thì lấy
hợp nhãn. Hồi quy: bài không có mục 0 cho output và exit code y như bản cũ. Bảng
mã đã chép vào `.claude/agents/tong-luan.md` (agent không đọc mã script).

Nhận diện mục 0 bằng tiêu đề `## 0. Tổng luận`. Trong mục 0:

| Mã | Lỗi khi |
|---|---|
| E7 | Thân mục 0 > 10.000 ký tự. (> 9.000 là cảnh báo **W7**.) |
| E8 | Gạch đầu dòng không mở bằng `[TB]`, `[TL]` hoặc `[TB][TL]`; có `[Claude]`, `[TĐ]`, `[NPL]` ở đầu dòng. |
| E3 | Giữ: đường dẫn thẻ nếu có vẫn phải có thật. |

- Mục 0 **miễn E5 và E6** (E8 thay E5; không cần Tổng kết/Nguồn).
- Cảnh báo **W8** (không chặn): dòng dạng `**<Tên cung>:**` gắn nhãn không có
  trong `nhãn mục:` của mục cung đó trong `pack/tong-luan-nguon.md` (có file thì mới kiểm).
- Mục khác: luật cũ không đổi. Self-test thêm ca mục 0 đạt, vượt trần, nhãn
  `[Claude]` trong mục 0, và ca mục 5 vẫn bị E6 như cũ.

**Điều kiện xong:** self-test đạt; chạy trên một bài cũ không có mục 0 cho kết
quả y như trước khi sửa.

### Z4 — `ghep_bai.py`: chèn mục 0 ✅ xong

Đã làm khác plan một điểm: tách `phan-a.md` tại tiêu đề `##` đầu tiên **không phải
"Cách đọc"** (thay vì đúng dòng `## 1.`), nên phan-a không có mục 1 vẫn chèn đúng.
Các nhánh: phan-a không có Cách đọc → mục 0 đứng trước phan-a; phan-a chỉ có Cách
đọc → mục 0 sau phan-a, cảnh báo; thiếu phan-a → mục 0 ngay sau tiêu đề bài.
Hồi quy: không có `phan-z.md` thì `ghep()` ra y hệt bản cũ. Ghép lại có mục 0 rồi
chạy `trich_tong_ket.py` thì mục 0 không bị rút ngược vào nguồn.

- Có `phan-z.md` thì chèn sau khối "## Cách đọc bài này" của `phan-a.md`, trước
  dòng `## 1.` đầu tiên (tách `phan-a.md` tại dòng đó; không có dòng `## 1.` thì
  chèn ngay sau tiêu đề bài và cảnh báo). Không có `phan-z.md` thì ghép như cũ,
  **không** cảnh báo (tổng luận chạy sau lần ghép đầu).
- Self-test: thứ tự Cách đọc → 0 → 1; thiếu `phan-z.md` không cảnh báo; số `---`.

**Điều kiện xong:** self-test đạt.

### Z5 — `tra_cuu.py --pack`: lượt Z trong `phan-cong.json` ✅ xong

Đã làm khác plan một điểm: `"ghi": ["phan-z.md"]` (không có `../`), theo quy ước
sẵn có của `phan-cong.json`: file `ghi` nằm ở thư mục cha của `pack/`. Lượt Z luôn
đứng cuối, `dot: 3`, `agent: tong-luan`, `truoc: trich_tong_ket.py`. Báo cáo gói
in một dòng riêng cho Z (trần `TRAN_TONG_LUAN` = 30.000 byte), không tính vào cảnh
báo 70k. `--kiem-pack` bỏ qua file trong `SINH_SAU` (`tong-luan-nguon.md`) khi
chưa có. Self-test 17/17, gồm kiểm `TRAN_TONG_LUAN == trich_tong_ket.TRAN`. Chạy
`--pack` và `--kiem-pack` trên lá số giả: `lỗi: 0`, trước và sau khi có
`tong-luan-nguon.md`.

Thêm `"Z": {"dot": 3, "agent": "tong-luan", "doc": ["tong-luan-nguon.md"],
"ghi": ["../phan-z.md"], "truoc": "trich_tong_ket.py"}`. Không tính Z vào cảnh báo
ngân sách 70k (file đầu vào chưa có lúc dựng gói; Z1 tự cảnh báo). Cập nhật
self-test của `tra_cuu.py` nếu nó so khoá `phan-cong.json`.

**Điều kiện xong:** `tra_cuu.py --self-test` đạt.

### Z6 — Tài liệu ✅ xong

Đã làm: `CLAUDE.md` (bảng bố cục; Bước B thêm bước 6 "Đợt 3 — tổng luận", bước 7
gửi bài kèm nguyên mục 0, dự phòng tóm tắt 15 dòng khi lượt Z hỏng, bước 8 vài cung
vẫn chạy Z; ngoại lệ nhãn mục 0 ở ràng buộc nguồn 2; lệnh `trich_tong_ket.py`),
`SKILL.md` (chế độ gói: đợt 3, E7/E8, bước 6 tổng luận), `xem-tu-vi.md` (lượt Z
không phải của nó; thứ tự bài có mục 0). Thêm ngoài plan: `lay_mau_nguon.py` bỏ
qua mục 0 khi lấy mẫu cho `kiem-nguon` (mục 0 không có dòng `Nguồn:`), có self-test.
Self-test: `lay_mau_nguon`, `kiem_bai`, `ghep_bai`, `trich_tong_ket` đạt; `tra_cuu`
17/17; `kb_the` không đạt **từ trước** vì thiếu `output/luan-giai/thang-pham-2026.json`
(gitignore, không có trong container). `validate_kb.py`: `lỗi: 0`.

- `CLAUDE.md`, Bước B: thêm bước "Đợt 3 — tổng luận" sau bước 5 (kiem-nguon):
  chạy `trich_tong_ket.py $D`, gọi `tong-luan` với đường dẫn `$D/pack/`, rồi ghép
  và kiểm lại. Bước 6: dán mục 0 (đọc `$D/phan-z.md`, ≤ 10.000 ký tự) thay tóm
  tắt 15 dòng. Bước 7 (chỉ hỏi vài cung): vẫn chạy Z, mục 0 chỉ gồm các mục có
  trong bài. Bảng bố cục: thêm `trich_tong_ket.py` và agent `tong-luan`.
- `CLAUDE.md`, "Ràng buộc nguồn" mục 2: thêm một câu ngoại lệ cho mục 0 như
  mục 2 của plan này.
- `SKILL.md` (chế độ gói) và `xem-tu-vi.md` mục 7: thứ tự bài thêm "0. Tổng
  luận" sau Cách đọc; ghi rõ `xem-tu-vi` **không** viết mục 0.
- `rm -rf scripts/__pycache__ output/claude/tuvi-kb/scripts/__pycache__` trước commit.

**Điều kiện xong:** mọi `--self-test` đạt; `validate_kb.py` vẫn `lỗi: 0`.

### Z7 — Chạy thử và đo ⛔ DỪNG

⛔ **DỪNG trước khi chạy**: cần một bài đã ghép có thật (người dùng chỉ định thư
mục trong `output/luan-giai/`, hoặc đồng ý chạy lượt mới). Không tự gọi đợt 1–2.

Khi có bài:
1. `trich_tong_ket.py` → ghi số byte `tong-luan-nguon.md`. Vượt 30 KB sau khi cắt
   thì ⛔ **DỪNG**, báo người dùng số đo, đề xuất trần mới.
2. Gọi `tong-luan`, ghép, kiểm. Đo: số ký tự mục 0, số lượt gọi model, cache_read,
   output của lượt Z (dùng cách đo như `bao-cao-giam-token.md`).
3. Tự đối chiếu 10 gạch đầu dòng mục 0 với mục cùng tên bên dưới: nhãn có đúng
   sách không, có ý nào không có trong bài không.
4. Ghi `docs/bao-cao-tong-luan.md`: bảng số đo so với mục 4, kết quả đối chiếu,
   việc còn lại.

**Điều kiện xong:** `kiem_bai.py` bài có mục 0 ra `lỗi: 0`; mục 0 ≤ 10.000 ký tự;
báo cáo đã ghi.
