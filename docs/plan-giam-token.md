# Plan: giảm token khi luận giải lá số (giao cho phiên thực hiện)

Tài liệu này là **đề bài đầy đủ** cho một phiên Claude Code khác thực hiện.
Phiên thực hiện không có ngữ cảnh của cuộc trao đổi đã sinh ra plan, nên mọi
quyết định, số liệu và quy cách đều ghi ở đây. Soạn ngày 2026-09-23.

---

## 0. Đọc trước khi làm

1. Đọc `CLAUDE.md`, `output/claude/tuvi-kb/_meta/schema.md`, và toàn bộ file này.
2. Làm theo đúng thứ tự giai đoạn G0 → G6. Mỗi giai đoạn có **điều kiện xong**;
   chưa đạt thì chưa sang giai đoạn sau.
3. Có ba **điểm dừng bắt buộc** (ghi `⛔ DỪNG`): báo người dùng và chờ trả lời.
4. Làm trên nhánh `giam-token-luan-giai` tách từ `main`. Commit sau mỗi giai
   đoạn, message tiếng Việt không dấu theo kiểu repo (`G2: tra_cuu.py --pack`).
   Không push, không mở PR nếu người dùng không yêu cầu.
5. Luôn đặt `PYTHONIOENCODING=utf-8`. Chỉ dùng Python 3 stdlib.
6. **Không đọc nguyên file lớn**: `output/luan-giai/thang-pham-2026-2027.md`
   (144 KB) và file `90-source/` chỉ được grep hoặc đọc theo đoạn.

## 1. Vì sao làm việc này (số liệu đã đo)

Đo từ transcript của sub-agent `xem-tu-vi` (lần luận bài "offer tháng 10/2026"):

| Chỉ số | Giá trị |
|---|---|
| Số lượt gọi model | 64 (58 lệnh Bash, 6 lần Read) |
| Token đọc từ cache | 5,97 triệu |
| Token ghi cache | 365 nghìn |
| Token output | 61 nghìn |
| Ngữ cảnh lớn nhất | 167 nghìn token |

Đo từ repo:

- `tra_cuu.py` liệt kê 258 thẻ cho lá số `thang-pham-2026.json`, tổng 773 KB.
  Trong đó 35% là mục **Nguyên văn**, 9,5% frontmatter, 8% Đối chứng.
- Tiếng Việt có dấu tốn khoảng **1,9 byte/token**. Số này đo từ độ tăng ngữ
  cảnh sau mỗi lần công cụ trả kết quả, với 17 mẫu nằm trong khoảng 1,64–2,03.
  773 KB tương đương khoảng 400 nghìn token, không một phiên nào chứa nổi.
- Bỏ Nguyên văn, frontmatter và các mục không dùng để suy luận thì còn khoảng
  390 KB. Lọc thêm các gạch đầu dòng chắc chắn không khớp lá số (G2) thì còn
  khoảng 355 KB, tức khoảng 190 nghìn token. Vẫn quá lớn cho một phiên, nên phải
  **chia 4 lượt**.
- Bài 12 cung cũ dài 144 KB, khoảng 75 nghìn token output.

Tiền đang đi vào ba chỗ. Thứ nhất, quá nhiều lượt: mỗi lượt đọc lại toàn bộ
ngữ cảnh. Thứ hai, đọc cả thẻ trong khi chỉ cần vài dòng. Thứ ba, kiểm trích
dẫn bằng cách grep tay vào `90-source/` (khoảng 15 lượt). Ngoài ra phiên chính
còn đọc lại cả bài rồi dán nguyên văn cho người dùng.

## 2. Quyết định đã chốt với người dùng (không mở lại)

| Quyết định | Nội dung |
|---|---|
| Không dùng DB | Không PostgreSQL, không SQLite. KB vẫn là file markdown. Lý do: token tính theo chữ vào ngữ cảnh, không theo cách lưu. |
| Giữ Opus-high | Mọi phần luận giải vẫn do `xem-tu-vi` (Opus, effort high) làm. Không chia cho Sonnet hay Haiku, không hạ effort. |
| Loại việc chính | Luận đủ 12 cung. |
| Chia 4 lượt | Lượt A: nền, Mệnh, Thân, quy tắc, cách cục. Xong A mới chạy **song song** B (nửa số cung còn lại), C (nửa kia), D (hạn). Script ghép thành một bài. **Thay bằng 6 lượt ở G7.** |
| Trích theo mã | Opus ghi `{Q:...}`, script chèn câu nguyên văn. Opus không tự chép câu trích. **Bỏ ở G7** (trích ý ngắn có nhãn thay trích nguyên văn). |
| Trả bài | Phiên chính **gửi file** kèm tóm tắt khoảng 15 dòng, không đọc rồi dán lại nguyên văn. |
| Độ dài | Không giới hạn độ dài bài. |

Các quyết định cũ ở mục 4 của `docs/tuvi-kb-guide.md` vẫn giữ nguyên: nguồn
chính TB/TL, không có module an sao, không sửa tầng nguyên văn.

## 3. Kiến trúc đích

```
lá số JSON (phiên chính, người dùng đã xác nhận)
   │
   ▼
tra_cuu.py --pack la-so.json <thư-mục-bài>/pack/        ← G3 (không tốn token model)
   │  00-nen.md, menh.md, than.md, cung-*.md, cach-cuc.md, quy-tac.md,
   │  han-<năm>.md, trich.json, phan-cong.json, loc-bo.md
   ▼
Lượt A (xem-tu-vi, Opus-high)  → phan-a.md, phan-a-cach-cuc.md, tom-tat-a.md
   │
   ├──► Lượt B (song song) → phan-b.md
   ├──► Lượt C (song song) → phan-c.md
   └──► Lượt D (song song) → phan-d.md
   ▼
ghep_bai.py → chen_trich.py → kiem_bai.py                  ← G4 (không tốn token model)
   ▼
output/luan-giai/<tên>-<năm>.md  → phiên chính gửi file + tóm tắt
```

Mỗi lượt chỉ đọc các file gói ngữ cảnh được phân cho nó, bằng 1–3 lần Read.
Không mở thẻ gốc, không grep `90-source/`.

## 4. Ràng buộc kỹ thuật

- **Không sửa**: mọi thẻ trong `output/claude/tuvi-kb/10-stars/` … `60-phu/`,
  `90-source/`, `00-index/*`, `output/chatgpt/`, `output/claude/tan-bien/`,
  `scripts/legacy/`, và `input/`.
- `output/claude/tuvi-kb/` phải **tự chứa**, vì SKILL.md hứa "chép đi đâu cũng
  dùng được". Script mới trong `output/claude/tuvi-kb/scripts/` **không được
  import** từ `scripts/` ở gốc repo. Code cần dùng lại thì chép sang, kèm dòng
  chú thích ghi nguồn chép.
- `tra_cuu.py <json>` (chế độ cũ) phải in ra **y hệt** như trước, và
  `tra_cuu.py --self-test` vẫn phải đạt 7/7.
- `scripts/validate_kb.py` phải vẫn báo `lỗi: 0` (KB không đổi nên chỉ cần chạy lại cho chắc).
- Trước mỗi commit: `rm -rf scripts/__pycache__ output/claude/tuvi-kb/scripts/__pycache__`.

---

## G0. Công cụ đo token — `scripts/do_token.py` (mới)

**Mục đích:** đo trước và sau bằng cùng một thước.

**Dùng:**
```bash
python3 scripts/do_token.py <file.jsonl | thư-mục> [...]
```
Nếu truyền thư mục thì quét mọi `*.jsonl` bên dưới, kể cả `subagents/`.
Transcript nằm ở `~/.claude/projects/-home-ubuntu-tuvi/<session-id>.jsonl` và
`~/.claude/projects/-home-ubuntu-tuvi/<session-id>/subagents/agent-*.jsonl`.

**Cách tính:**
- Mỗi dòng là một JSON. Lấy dòng có `type == "assistant"` và
  `message.usage`. **Một `message.id` xuất hiện nhiều dòng** (stream), nên
  lấy `usage` của dòng **cuối cùng** theo mỗi id.
- Cộng các trường `input_tokens`, `cache_read_input_tokens`,
  `cache_creation_input_tokens`, `output_tokens`. Ngữ cảnh mỗi lượt =
  input + cache_read + cache_creation; lấy max.
- Đếm công cụ từ các khối `message.content[*].type == "tool_use"` theo `name`.
  Đếm riêng số lệnh Bash có chuỗi `90-source`.
- Tính byte kết quả công cụ: các khối `type == "tool_result"` ở dòng `type == "user"`.
  `content` có thể là chuỗi hoặc list; nếu là list thì nối các `text`.
- Cột "quy đổi" = input + 0,1·cache_read + 1,25·cache_write + 5·output. Đặt
  các hệ số này thành hằng số ở đầu file, chú thích "kiểm lại bảng giá khi đổi
  model". In cả số thô.

**Ra:** bảng markdown, mỗi transcript một dòng, thêm dòng tổng.

**Điều kiện xong:** chạy trên
`~/.claude/projects/-home-ubuntu-tuvi/6d12685c-73ac-54d0-97a4-8e38170ad6b3/subagents/`
ra đúng: 64 lượt, cache_read 5.973.480, cache_write 364.533, output 60.950.

---

## G1. Thư viện đọc thẻ — `output/claude/tuvi-kb/scripts/kb_the.py` (mới)

`tra_cuu.py`, `chen_trich.py` và `kiem_bai.py` đều import thư viện này.
Import được vì cùng thư mục: khi chạy script, `sys.path[0]` là thư mục chứa nó.

Cần có:

1. `KB = Path(__file__).resolve().parent.parent`.
2. `doc_the(path) -> The`, với `The` là dataclass gồm:
   - `path`: đường dẫn tương đối so với KB, ví dụ `20-palaces/menh-than/tham-lang.md`;
   - `meta`: dict frontmatter (chuyển `parse_card` từ `tra_cuu.py` sang đây, để
     `tra_cuu.py` import lại);
   - `title`;
   - `sections`: list các `(tên mục, list dòng)`. Tách mục theo dòng
     `## `, giống `split_sections` trong `scripts/validate_kb.py`;
   - `dong`: list `Dong(section, nhan, text, raw)`, lấy từ các dòng bắt đầu
     bằng `- `, `+ `, `* `. `nhan` là `TB`, `TL`, `TĐ`, `NPL` hoặc `None`;
     `text` là phần sau nhãn. Dòng tiếp nối (thụt lề, không có dấu gạch) thì
     nối vào gạch đầu dòng trước;
   - `trich`: list `Trich(n, van, khuc)`, lấy từ mục `Nguyên văn`. Gom các
     dòng `>` thành từng khối theo đúng logic `check_quotes` trong
     `scripts/validate_kb.py`, và tách bằng `QUOTE_RE` của file đó. `n` đánh
     số từ 1 theo thứ tự trong thẻ.
3. `NameDetector` và `star_detector()`: chép từ `scripts/tuvi_kb_common.py`
   (class `NameDetector`, hàm `fold`, `nfc`, `_split_list`). Đọc
   `00-index/stars.md` theo **vị trí cột**: `id | tên | aliases | viết tắt |
   nhóm | hành | âm dương | dò | ghi chú`. Chỉ lấy sao có cột `dò` là
   `x`, `yes`, `co` hoặc `có`.
4. `khop_nguyen_van(van, khuc) -> bool`: chép `norm_quote`, `ELLIPSIS_SPLIT_RE`
   và vòng so khớp từng đoạn từ `check_quotes`. Tìm file khúc theo id bằng cách
   quét dòng `id:` trong frontmatter của `90-source/*/*.md`, dựng chỉ mục một
   lần rồi cache.
5. `--self-test`, gồm:
   - `20-palaces/menh-than/tham-lang.md` có 2 dòng mục Kết luận, 13 dòng mục
     "Điều kiện và sắc thái", và ≥ 6 trích;
   - chạy qua **mọi thẻ** `10-` … `60-`: đọc được hết, và mọi trích đều
     `khop_nguyen_van == True`. Validator đang báo 0 lỗi nên số khớp phải bằng
     tổng số trích. Lệch thì thư viện sai, không phải KB sai.

**Điều kiện xong:** `python3 output/claude/tuvi-kb/scripts/kb_the.py --self-test`
đạt; `tra_cuu.py --self-test` vẫn đạt 7/7; output chế độ cũ không đổi. Kiểm bằng
`diff` với bản chạy trước khi sửa, lưu ở `/tmp`.

---

## G2. Bộ lọc gạch đầu dòng (thêm vào `kb_the.py`)

**Nguyên tắc: chỉ bỏ dòng chắc chắn không khớp; nghi ngờ thì giữ.** Việc cân
nhắc theo ràng buộc số 4 vẫn do Opus làm. Bộ lọc chỉ bớt những dòng mà máy
chứng minh được là sai điều kiện. Mọi dòng bị bỏ phải ghi vào `loc-bo.md`
kèm lý do.

Hàm: `loc_dong(the, dong, ctx) -> str | None`, trả mã lý do hoặc `None` (giữ).
`ctx` gồm:
- `gioi`: `nam` hoặc `nu`;
- `chi`: index địa chi của cung đang xét;
- `mieu`: dict `star_id → mã` (M/V/Đ/B/H) lấy từ JSON lá số, phần sau dấu `:`,
  tại chính cung đó;
- `quanh`: tập sao ở cung + 2 cung tam hợp + xung chiếu + nhị hợp + 2 cung giáp,
  cộng chính tinh mượn nếu cung Vô Chính Diệu;
- `muc_khop`: mức khớp của thẻ (`đủ`, `hội chiếu`, …).

**Phạm vi áp dụng:**

| Loại thẻ | Mục được lọc | Không bao giờ lọc |
|---|---|---|
| star-card | Gặp sao khác, Nam nữ, Đối chứng | Bản chất, Vị trí miếu hãm |
| palace-card | Kết luận, Điều kiện và sắc thái, Đối chứng | — |
| phu-card | lọc **cả thẻ** theo luật P1, P2 | — |
| combo, han, rule | không lọc | toàn bộ |

**Luật cho gạch đầu dòng.** Đặt `t` là `text` đã bỏ backtick hoặc `**` ở đầu.
Đặt `dau` là phần của `t` trước dấu `:` đầu tiên, nếu dấu `:` nằm trong 120 ký
tự đầu; không thì `dau = ""`.

- **R1 giới tính.** `t` bắt đầu bằng `Nữ mệnh`, `Nữ Mệnh`, `Nữ:` hoặc
  `Đàn bà` (không phân biệt hoa thường) trong khi lá số là nam → bỏ, lý do
  `gioi`. Ngược lại, `Nam mệnh`, `Nam Mệnh` hoặc `Đàn ông` trong khi lá số là
  nữ → bỏ.
- **R2 miếu/hãm.**
  - Chỉ áp dụng khi thẻ có **đúng một** sao trong `meta.stars`, sao đó có mã
    trong `ctx.mieu`, và `muc_khop == "đủ"` (star-card luôn coi là `đủ`).
  - Bỏ tên sao ở đầu `t` nếu có, ví dụ "Tham Lang ". Sau đó so khớp **ở đầu
    chuỗi** với
    `^((miếu|vượng|đắc|bình hòa|bình|hãm)( địa)?)(\s*(,|và|hay|hoặc)\s*(miếu|vượng|đắc|bình hòa|bình|hãm)( địa)?)*`,
    không phân biệt hoa thường.
  - Gom các từ miếu/hãm tìm được. Mã quy đổi: M→miếu, V→vượng, Đ→đắc,
    B→bình, H→hãm.
  - Tập khác rỗng mà từ của lá số không nằm trong tập → bỏ, lý do `mieu-ham`.
  - **Chỉ xét ở đầu chuỗi.** Chữ "đắc địa" trong "…hay Hỏa, Linh đắc địa:" là
    nói về Hỏa, Linh, không phải về sao của thẻ.
- **R4 sao đi kèm.**
  - Chỉ áp dụng khi `dau` khác rỗng **và** bắt đầu bằng `Gặp`, `Hội`, `Có`,
    `Thêm`, `Được`, `Đi với` hoặc `Đồng cung với`.
  - Gọi `S` là tập sao mà `NameDetector` tìm thấy trong `dau`, trừ các sao của
    chính thẻ, trừ `tuan` và `triet`.
  - `S` khác rỗng và **không sao nào** trong `S` thuộc `ctx.quanh` → bỏ, lý do
    `sao-kem`.
  - Chỉ cần một sao trong `S` có mặt là giữ.
  - **Không** xét phần sau dấu `:`. Nhiều dòng có nhiều vế, ví dụ dòng Đối chứng
    "Tham Lang ở tứ mộ địa … rất hay, gặp Hỏa Tinh thì…": vế đầu vẫn đúng dù
    lá số không có Hỏa Tinh.
- Không làm luật lọc theo địa chi. Luật này dễ nhầm "Thân" (địa chi) với
  "Mệnh Thân", mà các dòng "Hãm địa tại …" đã bị R2 bỏ rồi.

**Luật cho thẻ phú.** Đọc dòng đầu mục `Sao và cung liên quan`, dạng
`Sao: Tham Lang (miếu địa). Cung: Mệnh.`:

- **P1.** Có `(nữ mệnh)` trong khi lá số là nam → bỏ cả thẻ. Có `(nam mệnh)`
  trong khi lá số là nữ → bỏ cả thẻ. Câu phú bắt đầu bằng "Nữ Mệnh" hoặc
  "Nữ mệnh" với lá số nam cũng bỏ.
- **P2.** Với mỗi `Tên sao (…)` có ngoặc chứa từ miếu/hãm (kể cả dạng
  `miếu/vượng địa`): nếu sao đó tọa thủ tại cung đang xét, có mã trong
  `ctx.mieu`, và từ của lá số không nằm trong ngoặc → bỏ cả thẻ.

**Ca kiểm thử bắt buộc** (thêm vào `--self-test`). Lá số dùng
`output/luan-giai/thang-pham-2026.json`: nam; Tham Lang **V** tại Thìn; Mệnh ở
Thìn; giáp Mão có Hóa Khoa, giáp Tỵ có Hóa Quyền. Nếu file này không có (nó
nằm trong thư mục gitignore), dựng lại trong `/tmp` từ bảng lá số ở đầu
`thang-pham-2026-2027.md`.

Thẻ `20-palaces/menh-than/tham-lang.md` tại Thìn:

| Mục | Đầu dòng | Kết quả |
|---|---|---|
| Kết luận | `[TB] Tham Lang miếu, vượng, đắc địa là người…` | giữ |
| Kết luận | `[TB] Hãm địa là người gian hiểm…` | bỏ `mieu-ham` |
| Điều kiện | `[TB] Miếu, vượng, đắc địa: thân hình cao lớn…` | giữ |
| Điều kiện | `[TB] Miếu địa: thời trẻ vất vả…` | bỏ `mieu-ham` |
| Điều kiện | `[TB] Gặp nhiều sao sáng (Tả, Hữu, Khoa, Quyền, Lộc) hay Hỏa, Linh đắc địa:…` | **giữ** (Khoa, Quyền ở cung giáp) |
| Điều kiện | `[TB] Vượng địa gặp Kỵ…` | giữ |
| Điều kiện | `[TB] Hãm địa: thân hình cao vừa tầm…` | bỏ `mieu-ham` |
| Điều kiện | `[TB] Hãm địa tại Tý, Ngọ, Tỵ, Hợi:…` | bỏ `mieu-ham` |
| Điều kiện | `[TB] Hãm địa tại Tý, Ngọ:…` | bỏ `mieu-ham` |
| Điều kiện | `[TB] Hãm địa tại Mão, Dậu:…` | bỏ `mieu-ham` |
| Điều kiện | `[TB] Hãm địa gặp nhiều sao mờ ám…` | bỏ `mieu-ham` |
| Điều kiện | `[TB] Dù miếu, vượng, đắc hay hãm gặp Kỵ hoặc Riêu…` | giữ |
| Điều kiện | `[TB] Nam mệnh:…` | giữ |
| Điều kiện | `[TB] Nữ mệnh:…` | bỏ `gioi` |
| Điều kiện | `[TB] Cách Tham Vũ (Sửu, Mùi) xem…` | giữ |
| Đối chứng | `[TĐ] Tham Lang ở tứ mộ địa (Thìn, Tuất, Sửu, Mùi) rất hay…` | **giữ** |

Thẻ phú tại Mệnh (Thìn):

| Thẻ | Kết quả |
|---|---|
| `60-phu/tham-lang-nhap-mieu-tho-nguyen-thoi.md` | bỏ (P2: miếu ≠ vượng) |
| `60-phu/tham-lang-ham-dia-tac-tru-nhan.md` | bỏ (P2) |
| `60-phu/nu-menh-tham-lang-da-tat-do.md` | bỏ (P1) |
| `60-phu/hoa-ky-van-nhan-bat-nai.md` | giữ |
| `60-phu/tham-xuong-cu-menh-phan-cot-tuy-si.md` | giữ |

**Điều kiện xong:**
- Toàn bộ ca kiểm thử trên đạt.
- Chạy bộ lọc cho cả lá số `thang-pham-2026.json` rồi **tự đọc hết**
  `loc-bo.md`. Dòng nào bị bỏ mà thật ra khớp lá số thì sửa luật cho chặt hơn
  (thà giữ thừa còn hơn bỏ nhầm) và thêm dòng đó vào ca kiểm thử.
- Ghi số dòng bị bỏ theo từng lý do vào báo cáo cuối.

---

## G3. Gói ngữ cảnh — `tra_cuu.py --pack` (sửa `tra_cuu.py`)

**Dùng:**
```bash
python3 output/claude/tuvi-kb/scripts/tra_cuu.py --pack <la-so.json> <thư-mục-bài>
```
Tạo `<thư-mục-bài>/pack/`. Tái dùng nguyên logic chọn thẻ hiện có trong
`report()`: tam hợp, xung chiếu, mức khớp, phú ứng viên, cách cục, hạn. Tách
phần chọn thẻ thành hàm trả về dữ liệu có cấu trúc, rồi cho `report()` (in như
cũ) và `pack()` cùng gọi. **Không** viết lại logic chọn thẻ theo cách khác.

**Quy cách in một thẻ trong gói:**
```
### `20-palaces/menh-than/tham-lang.md` — Tham Lang tại Mệnh Thân [đủ]
#### Kết luận
- [TB] ...
#### Điều kiện và sắc thái
- [TB] ...
#### Đối chứng
- [TĐ] ...
Trích: {Q:20-palaces/menh-than/tham-lang#1} tb#0039
       {Q:20-palaces/menh-than/tham-lang#2} tb#0039
```
- Không in frontmatter. Không in mục `Nguyên văn`; thay bằng dòng `Trích:`
  với mã Q và id khúc rút gọn.
- *Sửa 2026-09-23 (người dùng duyệt):* bản đầu in thêm khoảng 80 ký tự đầu
  của câu trích; phần xem trước đó chiếm ~35% gói và đẩy lượt A lên ~124k token
  ước tính. Đã bỏ vì nó chỉ lặp lại chữ đã có trong `trich.json`; không bỏ gạch
  đầu dòng nào của thẻ, bài luận vẫn không giới hạn độ chi tiết.
- Mục bị bỏ theo loại thẻ:

  | Loại | Mục bỏ |
  |---|---|
  | palace | Nguyên văn, Phú liên quan (phú đã có danh sách riêng) |
  | star | Nguyên văn |
  | phu | Nguyên văn, Nguồn giải |
  | combo | Nguyên văn (giữ Thành phần và Cung áp dụng, vì đó là điều kiện) |
  | han | Nguyên văn |
  | rule | Nguyên văn, Ví dụ trong sách |

- Mục nào còn trống sau khi lọc thì in `(các dòng của mục này không khớp lá số — xem loc-bo.md)`.
- Trong một file, mỗi thẻ chỉ in một lần. Giữa các file được in lặp,
  vì mỗi lượt chỉ đọc file của nó.

**Các file trong `pack/`:**

| File | Nội dung |
|---|---|
| `00-nen.md` | Đầu trang: tên file lá số, giới tính, năm sinh (can chi), năm xem, tuổi âm. Bảng 12 cung (địa chi, tên cung, đại hạn, sao kèm miếu/hãm, Tuần/Triệt). Với **cả 12 cung**: dòng tọa thủ, tam hợp, xung chiếu, nhị hợp, giáp, Vô Chính Diệu như `report()` đang in. Chú giải mức khớp. Cách dùng mã Q (xem G4). |
| `menh.md` | Cung Mệnh: thẻ cung (theo mức khớp), thẻ sao tọa thủ, phú ứng viên (sau lọc P1, P2). Nếu Thân cư Mệnh thì ghi rõ ở đầu file. |
| `than.md` | Cung Thân cư, cùng cấu trúc. Không tạo file này nếu Thân cư Mệnh. |
| `cung-<palace-id>.md` | Mỗi cung còn lại một file, cùng cấu trúc, ví dụ `cung-quan-loc.md`. |
| `cach-cuc.md` | Hợp các cách cục ứng viên của Mệnh và Thân (bỏ trùng), kèm dòng "sao có mặt". |
| `quy-tac.md` | Cả 39 thẻ `50-rules/`. |
| `han-<nam_xem>.md` | Dòng hạn (đại hạn, tiểu hạn, sao lưu) như `report()`. Với mỗi điểm (Đại hạn, Tiểu hạn, Lưu Thái Tuế): sao tọa thủ kèm miếu/hãm và thẻ hạn theo sao. Thẻ hạn chung. Bỏ trùng trong file. |
| `trich.json` | `{"20-palaces/menh-than/tham-lang#1": {"the": "...md", "khuc": "tb#0039-...", "van": "..."}}` cho **mọi thẻ có mặt trong gói**. |
| `phan-cong.json` | Xem bên dưới. |
| `loc-bo.md` | Bảng: file gói, thẻ, mục, lý do, nội dung dòng bị bỏ. Chỉ để kiểm, **không** giao cho lượt nào đọc. |

**Phân công (`phan-cong.json`):**
- Gọi `con_lai` là các cung theo thứ tự `PALACE_ORDER` tính từ Mệnh, trừ Mệnh
  và cung Thân cư.
- `B` = đoạn đầu của `con_lai`, `C` = phần còn lại; điểm cắt chọn theo dung
  lượng file `cung-*.md` sao cho lượt lớn hơn là nhỏ nhất (hoà thì lấy điểm gần
  giữa nhất). *Sửa 2026-09-23 (người dùng duyệt):* bản đầu cắt ở `ceil(len/2)`
  làm C ~117k còn B ~80k.
- Thêm `so_bat_dau` cho C = `len(B) + 1`, dùng để đánh số mục 5.x.

```json
{
  "A": {"doc": ["00-nen.md", "menh.md", "than.md", "quy-tac.md", "cach-cuc.md"],
        "ghi": ["phan-a.md", "phan-a-cach-cuc.md", "tom-tat-a.md"]},
  "B": {"doc": ["00-nen.md", "../tom-tat-a.md", "cung-phu-mau.md", "..."], "ghi": ["phan-b.md"], "so_bat_dau": 1},
  "C": {"doc": ["00-nen.md", "../tom-tat-a.md", "..."], "ghi": ["phan-c.md"], "so_bat_dau": 6},
  "D": {"doc": ["00-nen.md", "../tom-tat-a.md", "han-2026.md"], "ghi": ["phan-d.md"]}
}
```

**Stdout của `--pack`:** bảng dung lượng từng file (byte và token ước tính =
byte/1,9), rồi tổng theo từng lượt (A, B, C, D). In `CẢNH BÁO` nếu tổng một
lượt vượt 110 nghìn token ước tính.

**Điều kiện xong:**
- Chạy `--pack` cho `thang-pham-2026.json` ra đủ các file trên.
- Mọi đường dẫn thẻ mà `report()` liệt kê đều có trong gói, trừ phú bị lọc (đã
  ghi trong `loc-bo.md`). Viết một đoạn kiểm tự động so tập thẻ của hai chế độ.
- Mọi mã Q in trong gói đều có trong `trich.json`.
- Không lượt nào có cảnh báo vượt ngân sách. Nếu lượt A vượt, báo lại, **không**
  tự cắt nội dung.
- Ghi dung lượng từng lượt vào báo cáo.

---

## G4. Ghép bài, chèn trích, kiểm bài (3 script mới trong `output/claude/tuvi-kb/scripts/`)

### Quy ước mã Q (ghi vào `00-nen.md` và agent md)

- Muốn trích nguyên văn thì viết **một dòng riêng** chỉ gồm `{Q:<mã>}`, ví dụ
  `{Q:20-palaces/menh-than/tham-lang#2}`.
- Không được tự gõ câu trích trong ngoặc kép kèm id khúc.
- Được nhắc lại ý của câu trích bằng lời mình, nhưng vẫn phải gắn nhãn nguồn.

### `chen_trich.py <bai.md> <pack-dir> [-o out.md]`

- Thay mỗi dòng chỉ gồm `{Q:…}` (bỏ khoảng trắng hai đầu) bằng
  `> "<van>" (<khuc>)`, ngay dưới thêm `> — thẻ \`<the>\``.
- Mã không có trong `trich.json` → lỗi, exit 1, in số dòng.
- `{Q:` nằm lẫn trong dòng có chữ khác → lỗi, in số dòng.
- Chạy lại lần hai trên kết quả thì không đổi gì.

### `kiem_bai.py <bai.md> [--pack <pack-dir>] [--nhap]`

`--nhap` dùng để kiểm một phần bài trước khi ghép. Không có cờ này là kiểm bài hoàn chỉnh.

| Mã | Loại | Kiểm |
|---|---|---|
| E1 | lỗi | Còn `{Q:` trong bài hoàn chỉnh; hoặc, ở chế độ `--nhap`, mã không có trong `trich.json`. |
| E2 | lỗi | Mỗi blockquote dạng `> "…" (id-khúc)` phải qua `khop_nguyen_van`. |
| E3 | lỗi | Mỗi đường dẫn trong backtick khớp `(10-stars\|20-palaces\|30-combos\|40-han\|50-rules\|60-phu)/[^` ]+\.md` phải tồn tại trong KB. Có `--pack` thì phải là thẻ có mặt trong gói. Đường dẫn tương đối kiểu `menh-than/x.md` thì bỏ qua. |
| E4 | lỗi | Bài hoàn chỉnh phải có tiêu đề chứa "Nguồn đã dùng". |
| W1 | cảnh báo | Gạch đầu dòng nằm ngoài các mục miễn trừ (tiêu đề chứa "Bảng lá số", "Cách đọc", "Nguồn đã dùng") mà không có nhãn `[TB]`, `[TL]`, `[TĐ]`, `[NPL]` (có hay không có backtick), không có "suy luận của Claude", và không có "không có đoạn riêng". |

In từng lỗi kèm số dòng. Cuối cùng in `lỗi: N, cảnh báo: M`. Exit 1 nếu N > 0.

**Kiểm thử:** chạy trên `output/luan-giai/thang-pham-2026-2027.md` (bài cũ,
không có `--pack`). Bài có 4 blockquote; E2 phải cho kết quả hợp lý. Nếu có
lỗi E2 thì đối chiếu tay xem là lỗi thật của bài cũ hay lỗi của script, và
ghi kết luận vào báo cáo. Nhãn trong bài cũ có dạng `` `[TB]` ``.

### `ghep_bai.py <thư-mục-bài> <file-ra.md>`

- Ghép theo thứ tự, mỗi phần cách nhau bằng `---`:
  1. `# Luận giải lá số Tử Vi — <tên lấy từ tên thư mục>`;
  2. `phan-a.md` (lượt A đã viết mục 1–4);
  3. `## 5. Các cung còn lại`;
  4. `phan-b.md`, rồi `phan-c.md`;
  5. `phan-a-cach-cuc.md` (mục 6);
  6. `phan-d.md` (mục 7);
  7. mục **`## 8. Nguồn đã dùng`** do script **tự sinh**.
- Mục 8 gom mọi đường dẫn thẻ trong backtick ở các phần, nhóm theo thư mục
  (`10-stars`, `20-palaces`, …). Mỗi thẻ ghi các mục `##`/`###` có dẫn nó
  ("dùng ở mục 2.1, 5.3").
- Thiếu file phần nào thì in cảnh báo và ghép phần còn lại. Ví dụ người dùng
  không hỏi hạn thì không có `phan-d.md`.

**Chuỗi lệnh cuối** (phiên chính chạy):
```bash
S=output/claude/tuvi-kb/scripts; D=output/luan-giai/<tên>-<năm>
python3 $S/ghep_bai.py $D $D/nhap.md
python3 $S/chen_trich.py $D/nhap.md $D/pack -o output/luan-giai/<tên>-<năm>.md
python3 $S/kiem_bai.py output/luan-giai/<tên>-<năm>.md --pack $D/pack
```

**Điều kiện xong:** cả ba script có `--self-test` dùng dữ liệu nhỏ dựng trong
`/tmp`, và đều đạt.

---

## G5. Cập nhật hướng dẫn

### `.claude/agents/xem-tu-vi.md`

Giữ nguyên frontmatter (`model: opus`, `effort: high`), giữ 6 ràng buộc nguồn,
và giữ các mục Hạn, Giọng văn, Không làm. Viết lại:

- **"Bạn nhận gì, trả gì":**
  - Agent nhận: tên lượt (`A`/`B`/`C`/`D`), đường dẫn `pack/`, danh sách file
    phải đọc (lấy từ `phan-cong.json`), file phải ghi, và với B, C thì số bắt
    đầu của mục 5.x.
  - Agent trả: đường dẫn file đã ghi và 3–5 dòng tóm tắt.
- **Thay mục "1. Chạy script tra cứu" bằng "1. Đọc gói ngữ cảnh":**
  - Đọc đúng các file được giao, gộp trong 1–3 lần Read.
  - **Không** mở thẻ gốc trong `10-stars/` … `60-phu/`. **Không** grep
    `90-source/`. **Không** chạy lại `tra_cuu.py`.
  - Gói đã bỏ những dòng chắc chắn không khớp, nhưng mọi dòng còn lại vẫn phải
    kiểm điều kiện như cũ (ràng buộc 4).
- **Việc riêng từng lượt:**
  - **A** viết `phan-a.md` với các mục `## 1. Bảng lá số đã xác nhận`,
    `## 2. Cung Mệnh …`, `## 3. Thân cư …` (hoặc "Thân cư Mệnh"),
    `## 4. Nền chung toàn lá số`. Mở đầu bằng mục "Cách đọc bài này" không
    đánh số. A viết thêm `phan-a-cach-cuc.md` (`## 6. Cách cục`) và
    `tom-tat-a.md`.
  - `tom-tat-a.md` ≤ 6 KB, gồm: kết luận chính về Mệnh, Thân có nhãn nguồn;
    danh sách quy tắc `50-rules/` áp dụng cho lá số, mỗi quy tắc một dòng;
    danh sách cách cục thành và phá. B, C, D đọc file này để luận các cung khác
    theo Mệnh Thân.
  - **B, C** viết `### 5.<k>. <Tên cung> — cung <Chi> (…)`, đánh số từ `so_bat_dau`.
    Không viết tiêu đề `## 5.`, vì script ghép sẽ thêm.
  - **D** viết `## 7. Hạn năm <năm>`.
- **Quy tắc viết:**
  - Trích nguyên văn chỉ bằng dòng `{Q:…}`.
  - Dẫn thẻ bằng đường dẫn đầy đủ trong backtick ít nhất một lần ở mục dùng thẻ đó.
  - **Không** viết mục "Nguồn đã dùng", vì script tự sinh.
  - Ghi file bằng ít lần Write nhất có thể.
- **Trước khi trả:** chạy
  `kiem_bai.py <file> --pack <pack> --nhap`, sửa hết lỗi, rồi mới báo xong.

### `CLAUDE.md`, mục "Bước B"

Thay bằng luồng mới:

1. Chạy `tra_cuu.py --pack <json> output/luan-giai/<tên>-<năm>/`. Nếu có
   `CẢNH BÁO` ngân sách thì báo người dùng.
2. Gọi `xem-tu-vi` cho lượt A và **chờ xong**.
3. Gọi B, C, D **cùng một lúc** (nhiều lệnh Agent trong cùng một message, chạy
   nền). Người dùng không hỏi hạn thì bỏ D.
4. Ghép, chèn trích, kiểm bằng chuỗi lệnh ở G4. Nếu `kiem_bai.py` báo lỗi thì
   `SendMessage` cho đúng agent của phần có lỗi để nó sửa. Không tự sửa nội dung
   luận giải.
5. Gửi file kết quả cho người dùng (`SendUserFile` nếu có, không thì ghi đường
   dẫn), kèm tóm tắt khoảng 15 dòng dựng từ `tom-tat-a.md` và báo cáo của các
   lượt. **Không** đọc cả bài rồi dán lại vào chat. Thay câu "Phiên chính đọc
   file đó và trả nguyên văn cho người dùng".
6. Người dùng chỉ hỏi vài cung: chạy A, cộng một lượt B gồm đúng các cung
   được hỏi (sửa `phan-cong.json` bằng tay hoặc thêm cờ `--cung` cho
   `--pack`), cộng D nếu có hỏi hạn.

Cập nhật bảng "Lệnh hay dùng" trong `CLAUDE.md` với các lệnh mới, và bảng
"Bố cục" nếu cần.

### `output/claude/tuvi-kb/SKILL.md`

- **Giữ nguyên** 7 bước hiện có, vì file này còn dùng cho trường hợp một phiên làm hết.
- Thêm mục "Chế độ gói ngữ cảnh (khuyên dùng)" mô tả `--pack`, mã Q,
  `kiem_bai.py`, `chen_trich.py` và `ghep_bai.py`. Viết đường dẫn tương đối
  so với thư mục skill, như phần còn lại của file.

### `docs/tuvi-kb-guide.md`

Chỉ cần thêm dòng giới thiệu script mới nếu file có chỗ liệt kê script.
Không sửa mục 4.

**Điều kiện xong:** ba file nói cùng một luồng. Đọc chéo và grep các cụm
`--pack`, `{Q:`, `kiem_bai`, `nguyên văn cho người dùng` để kiểm; cụm cuối
không được còn sót.

---

## G6. Chạy thật và đo

⛔ **DỪNG trước G6.** Báo người dùng các việc sau rồi chờ đồng ý:
- G0–G5 đã xong, kèm số commit;
- dung lượng gói từng lượt;
- số dòng bị lọc theo từng lý do;
- G6 sẽ gọi Opus-high 4 lần.

Khi được đồng ý:

1. Làm đúng như phiên chính theo `CLAUDE.md` mới, với
   `output/luan-giai/thang-pham-2026.json`, thư mục
   `output/luan-giai/thang-pham-2026-v2/`, luận đủ 12 cung và hạn 2026.
2. Đo bằng `scripts/do_token.py` trên transcript của 4 sub-agent. Transcript
   nằm dưới `~/.claude/projects/-home-ubuntu-tuvi/<session-id-hiện-tại>/subagents/`.
3. So với mục tiêu:

| Chỉ số | Mục tiêu |
|---|---|
| Số lượt mỗi sub-agent | ≤ 15 |
| Ngữ cảnh lớn nhất mỗi sub-agent | ≤ 120 nghìn token |
| Lệnh Bash có `90-source` | 0 |
| Đọc thẻ gốc `10-` … `60-` bằng Read hoặc cat | 0 |
| `kiem_bai.py` trên bài hoàn chỉnh | `lỗi: 0` |
| Độ phủ | Đủ 12 cung, cách cục, hạn 2026 (so danh sách mục với bài cũ `thang-pham-2026-2027.md`, phần năm 2026) |
| Truy nguồn | Chọn ngẫu nhiên 20 gạch đầu dòng có nhãn; mỗi dòng phải tìm thấy nội dung tương ứng trong gói. Ghi kết quả từng dòng. |

4. Viết báo cáo `docs/bao-cao-giam-token.md`:
   - bảng số trước và sau (mốc là 64 lượt, 5,97 triệu cache_read và các số khác ở mục 1);
   - kết quả từng mục tiêu, đạt hay không;
   - các dòng lọc đáng ngờ đã sửa ở G2;
   - những gì còn chưa đạt.

⛔ **DỪNG sau G6.** Gửi báo cáo cho người dùng. Không tự tối ưu thêm ngoài
phạm vi plan.

---

## G7. Trích ý có nhãn thay trích nguyên văn, chia 6 lượt (người dùng duyệt 2026-09-24)

Lý do: G6 chưa rẻ hơn cách cũ (xem `docs/bao-cao-giam-token.md`). Hai nguồn
tốn chính là gói lượt A quá lớn (quy-tac.md 95 KB, ngữ cảnh 173 nghìn, nén 4
lần) và việc agent tra `trich.json` để biết mã Q nói gì. Điều kiện người dùng
đặt: **không giảm chi tiết bài**; được bỏ trích nguyên văn.

### Quyết định mới (thay dòng "Chia 4 lượt" và "Trích theo mã" ở mục 2)

| Quyết định | Nội dung |
|---|---|
| Bỏ trích nguyên văn | Bỏ mã `{Q:…}`, `trich.json`, dòng `Trích:` trong gói, `chen_trich.py`. Truy nguồn đi bài → thẻ (đường dẫn trong dòng `Nguồn:`) → mục Nguyên văn của thẻ (id khúc). |
| Khuôn một đơn vị | Mỗi sao / cách cục / quy tắc / cung / điểm hạn: các gạch đầu dòng ý ngắn, mỗi dòng mở bằng nhãn `[TB]`/`[TL]`/`[TĐ]`/`[NPL]`/`[Claude]`; rồi dòng `**[Claude] Tổng kết:** …` chỉ gom các ý bên trên; rồi dòng `Nguồn:` liệt kê đường dẫn thẻ trong backtick. "Ngắn" là ngắn lời, **không** bớt ý: mọi gạch đầu dòng thẻ khớp lá số vẫn có mặt. |
| `[Claude]` | Thay cụm "(suy luận của Claude, không phải nguyên văn sách)". |
| Bỏ "Nguồn đã dùng" | Bài không còn mục 8; dòng `Nguồn:` cuối mỗi đơn vị đã làm việc đó. |
| Chia 6 lượt | Đợt 1 song song: **A** (Mệnh, Thân, cách cục) và **R** (quy tắc toàn lá số). Đợt 2, chạy hai lượt một lúc: **B**, **C**, **E** (các cung còn lại chia ba theo kích thước), **D** (hạn). |

### Ngân sách gói (`tra_cuu.py --pack`)

- Ước tính token = byte / 1,755 (số đo thật ở G6) cộng 15 nghìn nền của sub-agent.
- Gói của một lượt ≤ 60 nghìn token (không tính nền); vượt thì in `CẢNH BÁO`.
- Mỗi file gói ≤ 45 KB (Read cắt file lớn hơn). File dài hơn được chia tại ranh
  giới thẻ thành `<tên>-1.md`, `<tên>-2.md`…
- Các cung còn lại chia thành 3 nhóm liên tục (B, C, E) sao cho nhóm lớn nhất
  nhỏ nhất.
- `phan-cong.json` thêm khoá `dot` (1 hoặc 2). B, C, E, D đọc cả
  `../tom-tat-a.md` và `../tom-tat-r.md`.

### Bài ghép (`ghep_bai.py`)

Thứ tự: tiêu đề, `phan-a.md` (Cách đọc, 1, 2, 3), `phan-r.md` (`## 4. Nền
chung toàn lá số`), `## 5. Các cung còn lại`, `phan-b.md`, `phan-c.md`,
`phan-e.md`, `phan-a-cach-cuc.md` (`## 6.`), `phan-d.md` (`## 7.`). Không sinh
mục Nguồn đã dùng.

### Kiểm bài (`kiem_bai.py <bai.md> [--pack <dir>]`)

| Mã | Loại | Kiểm |
|---|---|---|
| E2 | lỗi | Giữ làm lưới an toàn: nếu có blockquote `> "…" (id-khúc)` thì phải khớp nguyên văn. |
| E3 | lỗi | Giữ nguyên: đường dẫn thẻ có trong KB, có `--pack` thì có trong gói. |
| E5 | lỗi | Gạch đầu dòng ngoài mục "Bảng lá số"/"Cách đọc" không mở bằng nhãn nguồn hay `[Claude]` (trừ dòng nói "không có đoạn riêng"). Thay W1. |
| E6 | lỗi | Đoạn dưới một tiêu đề có gạch đầu dòng mang nhãn sách mà thiếu dòng `[Claude] Tổng kết`, hoặc thiếu dòng `Nguồn:` có đường dẫn thẻ. |

Bỏ E1 (mã Q), E4 (mục Nguồn đã dùng), cờ `--nhap`.

### Hướng dẫn agent

- Luật kiểm ghi thẳng vào `xem-tu-vi.md` để agent khỏi đọc mã `kiem_bai.py`.
- Đọc hết file được giao trong lượt gọi đầu; chạy `kiem_bai.py` một lần, chỉ sửa lỗi.
- `tom-tat-a.md`, `tom-tat-r.md`: mỗi kết luận một dòng, nêu cả nội dung
  (quy tắc nói gì), không chỉ tên thẻ, để lượt sau khỏi mở `quy-tac-*.md`.
- Phiên chính: lượt bị 429 thì `SendMessage` cho chạy tiếp, không gọi lại từ đầu.

Kỳ vọng mỗi lượt: 5–8 lượt gọi model, ngữ cảnh lớn nhất 90–110 nghìn.
Kiểm thử G7 **chỉ bằng script** (self-test, dựng gói lá số mẫu, kiểm bài giả);
không gọi sub-agent cho đến khi người dùng duyệt chạy thật.

---

## Bẫy đã biết

- **Tý và Tỵ:** `fold()` biến cả hai thành `ty`. KB dùng `ty` cho Tý và `ti`
  cho Tỵ. Dùng `branch_index()` của `tra_cuu.py`, đừng tự fold.
- **Quan Phù và Quan Phủ:** `quan-phu` (vòng Thái Tuế) và `quan-phu-loc-ton`
  (vòng Lộc Tồn) là hai sao khác nhau. Lá số mẫu có cả hai ở cung Tý (Sửu).
- **Tuần/Triệt:** thẻ ghi cả hai sao chỉ cần cung có một trong hai
  (`gop_tuan_triet`). Giữ nguyên hành vi này.
- **Dòng nhiều vế:** đừng lọc theo sao hay miếu/hãm xuất hiện ở giữa hay cuối
  dòng (xem R2, R4).
- **Nhãn trong bài có thể nằm trong backtick** (`` `[TB]` ``).
- Mục Đối chứng chỉ dùng `[TĐ]` và `[NPL]`. Ngoài mục đó chỉ dùng `[TB]` và `[TL]`.
- Không đọc hết `thang-pham-2026-2027.md` (144 KB, khoảng 75 nghìn token): chỉ grep.
- Thư mục `output/luan-giai/` đã gitignore. Không `git add -f` gì trong đó.

## Khi nào dừng và hỏi (ngoài hai điểm ⛔ ở G6)

- Một ca kiểm thử trong bảng G2 không thể đạt mà không làm hỏng ca khác.
- Lượt A vượt ngân sách 110 nghìn token (từ G7: gói một lượt vượt 60 nghìn).
- Thấy cần sửa thẻ trong KB, dù chỉ để "sửa lỗi". Không được sửa; báo lại.
- Thấy cần đổi một quyết định ở mục 2.
