# CLAUDE.md

Dự án **luận giải Tử Vi Đẩu Số** bằng một knowledge base rút từ 4 bộ sách
tiếng Việt. Hai việc diễn ra trong repo này, đừng lẫn chúng:

1. **Luận giải lá số** cho người dùng (việc thường xuyên) — xem mục "Luồng
   luận giải" bên dưới. Việc này giao cho sub-agent `xem-tu-vi`.
2. **Xây và bảo trì knowledge base** `output/claude/tuvi-kb/` (việc thưa
   hơn) — quy trình nằm ở [docs/tuvi-kb-guide.md](docs/tuvi-kb-guide.md).

## Bố cục

| Đường dẫn | Nội dung |
|---|---|
| `input/*.clean.md` | 4 sách nguồn đã OCR: Tân Biên, Thiên Lương, Trần Đoàn, Nguyễn Phát Lộc. Không sửa tay. |
| `output/claude/tuvi-kb/` | **KB chính thức**, dùng cho mọi luận giải. 1596 file md. |
| `output/claude/tuvi-kb/90-source/` | 664 khúc nguyên văn, id ổn định (`tb#0039-...`). Nguồn sự thật cho mọi trích dẫn. **Không sửa.** |
| `output/claude/tuvi-kb/10-stars/` … `60-phu/` | 111 thẻ sao, 364 thẻ cung, 22 cách cục, 63 thẻ hạn, 39 quy tắc, 325 thẻ phú. |
| `output/claude/tuvi-kb/00-index/` | Sổ đăng ký `stars.md`, `palaces.md`; bảng tra `lookup*.md` (sinh tự động); `chart-reading.md` (cách đọc ảnh lá số). |
| `output/claude/tuvi-kb/SKILL.md` | Quy trình 7 bước luận giải. Sub-agent `xem-tu-vi` bám theo file này. |
| `output/claude/tuvi-kb/scripts/tra_cuu.py` | Nhận lá số JSON → in danh sách thẻ cần đọc, hoặc (`--pack`) dựng gói ngữ cảnh cho các lượt sub-agent (A, R, B, C, E, D…, T… nếu xem hạn tháng; Z tổng luận). Không luận giải. |
| `output/claude/tuvi-kb/scripts/` `ghep_bai.py`, `kiem_bai.py`, `lay_mau_nguon.py`, `trich_tong_ket.py` | Ghép các phần bài (có `phan-z.md` thì chèn mục 0 sau "Cách đọc"); kiểm bài (nhãn nguồn, tổng kết `[Claude]`, dòng `Nguồn:`, thẻ có thật; mục 0: trần 10.000 ký tự, chỉ nhãn TB/TL); lấy mẫu gạch đầu dòng cho `kiem-nguon`; rút các dòng Tổng kết thành đầu vào lượt Z. `kb_the.py` là thư viện chung. |
| `.claude/agents/` | `xem-tu-vi` (Sonnet high, luận giải), `kiem-nguon` (Sonnet, kiểm truy nguồn bài đã ghép), `tong-luan` (Sonnet, viết mục 0. Tổng luận), `tra-the` (Sonnet, câu hỏi lẻ không có lá số). |
| `scripts/` | Toolchain KB đang dùng: `tuvi_kb_common.py`, `chunk_sources.py`, `validate_kb.py`, `build_lookup.py`, `dump_chunks.py`. |

Lưu ý đường dẫn: KB nằm ở `output/claude/tuvi-kb/`, không phải `output/tuvi-kb/`
như bố cục cũ. `scripts/tuvi_kb_common.py:18` là nơi định nghĩa `KB_DIR` thật.

## Luồng luận giải (khi người dùng gửi ảnh lá số)

Chia đôi vì sub-agent không nhìn được ảnh người dùng tải lên và không hỏi
lại người dùng được. Phiên chính làm phần cần mắt và cần đối thoại; sub-agent
làm phần cần đọc nhiều thẻ và suy luận sâu.

### Bước A — phiên chính: đọc ảnh, xin xác nhận

1. Đọc ảnh theo `output/claude/tuvi-kb/00-index/chart-reading.md`.
2. In bảng chuẩn hoá: giới tính; năm sinh âm lịch (can chi); âm/dương nam/nữ;
   Cục; Bản Mệnh (nạp âm); Mệnh ở địa chi nào; Thân cư cung nào; bảng 12 dòng
   (địa chi | tên cung | số đại hạn | sao tọa thủ kèm miếu/hãm | Tuần/Triệt);
   năm muốn xem hạn.
3. Ô nào đọc không chắc thì đánh dấu `?` và hỏi riêng. **Dừng lại chờ người
   dùng xác nhận.** Đọc sai một sao làm hỏng toàn bộ phần sau, nên không được
   bỏ bước này để "đi cho nhanh".
4. Sau khi người dùng xác nhận, ghi lá số ra JSON theo mẫu ở mục "Bước 2" của
   `output/claude/tuvi-kb/SKILL.md`, đặt tại `output/luan-giai/<tên>-<năm>.json`
   (thư mục này đã gitignore vì chứa dữ liệu cá nhân). Ghi cả `thang_sinh`,
   `gio_sinh`, `cuc`, `ban_menh` lấy từ bảng; người dùng hỏi thời điểm theo
   tháng thì thêm `thang_xem` (tháng **âm lịch**; đổi từ dương lịch trước).

### Bước B — dựng gói ngữ cảnh, giao 6 lượt cho `xem-tu-vi`, lượt tổng luận cho `tong-luan`

Sub-agent `xem-tu-vi` đã cấu hình Sonnet, effort high tại
`.claude/agents/xem-tu-vi.md`; `tong-luan` là Sonnet (`.claude/agents/tong-luan.md`).
Đặt `S=output/claude/tuvi-kb/scripts`,
`D=output/luan-giai/<tên>-<năm>`.

1. Dựng gói: `python3 $S/tra_cuu.py --pack <file.json> $D/` (sinh `$D/pack/`).
   Nếu script in `CẢNH BÁO` ngân sách thì báo người dùng.
2. **Đợt 1:** gọi `xem-tu-vi` cho lượt **A** và **R** cùng lúc (hai lệnh Agent
   trong một message, chạy nền), **chờ cả hai xong**. Prompt gồm: tên lượt,
   đường dẫn `$D/pack/`, danh sách file đọc và file ghi lấy từ
   `$D/pack/phan-cong.json`.
3. **Đợt 2:** gọi **B, C, E, D**, hai lượt một lúc (để khỏi chạm hạn mức phiên),
   prompt như trên, B, C, E kèm `so_bat_dau`, lượt hạn kèm `nam` và `tieu_de`.
   Xem nhiều năm (`nam_xem` là danh sách) thì thay D bằng D1, D2… mỗi năm một
   lượt. Người dùng không hỏi hạn thì không có lượt D. Có `thang_xem` thì
   thêm lượt T (hoặc T1, T2… mỗi năm có tháng xem), prompt kèm `nam`, `tieu_de`.
   Lượt nào bị ngắt (HTTP 429, hết hạn mức) thì `SendMessage` cho đúng agent đó
   chạy tiếp, **không** gọi lại từ đầu.
4. Ghép, kiểm:
   ```bash
   python3 $S/ghep_bai.py $D output/luan-giai/<tên>-<năm>.md
   python3 $S/kiem_bai.py output/luan-giai/<tên>-<năm>.md --pack $D/pack
   ```
   `kiem_bai.py` báo lỗi thì `SendMessage` cho đúng agent của phần có lỗi để nó
   sửa rồi chạy lại hai lệnh. Không tự sửa nội dung luận giải.
5. Kiểm truy nguồn: `kiem_bai.py` ra `lỗi: 0` thì gọi `kiem-nguon` (Sonnet) với
   đường dẫn bài, `$D/pack/` và số mẫu (mặc định 25). Nó ghi `$D/kiem-nguon.md`
   và trả danh sách mẫu không khớp. Có mẫu `lệch ý`/`sai nhãn`/`sai điều
   kiện`/`không thấy` thì `SendMessage` cho lượt `xem-tu-vi` đã viết mục đó (xem
   số mục 2.x/4.x/5.x/6/7) để sửa, rồi ghép và kiểm lại. Agent đã hết phiên thì
   báo người dùng kèm danh sách, không tự sửa.
6. **Đợt 3 — tổng luận** (lượt Z, sau khi bước 5 đã sửa xong):
   ```bash
   python3 $S/trich_tong_ket.py $D          # sinh $D/pack/tong-luan-nguon.md
   ```
   Gọi `tong-luan` (không phải `xem-tu-vi`), prompt gồm đường dẫn `$D` và
   `$D/pack/`. Nó ghi `$D/phan-z.md` (mục `## 0. Tổng luận`, ≤ 10.000 ký tự, mỗi ý
   `[TB]`/`[TL]`). Rồi ghép và kiểm lại như bước 4; `ghep_bai.py` tự chèn mục 0 sau
   "Cách đọc". `kiem_bai.py` báo E7/E8 thì `SendMessage` cho `tong-luan` sửa. Nội
   dung các mục khác sau đó mà sửa thì chạy lại cả bước này. File nguồn quá 45 KB
   thì ghi sẵn trong prompt điểm chia khúc để agent đọc theo `offset`/`limit`.
   Người dùng chỉ đưa **bài đã ghép sẵn** (không có `phan-*.md`): chép vào
   `output/luan-giai/<tên>.md`, chạy `trich_tong_ket.py output/luan-giai/<tên>.md`
   (gói ra `output/luan-giai/<tên>/pack/`), gọi `tong-luan` với `D=output/luan-giai/<tên>`,
   rồi `ghep_bai.py --chen-z output/luan-giai/<tên>.md $D/phan-z.md`.
7. Gửi file kết quả cho người dùng (`SendUserFile` nếu có, không thì ghi đường
   dẫn), kèm **nguyên mục 0** (đọc `$D/phan-z.md`, dán vào chat không thêm bớt) và
   dòng tổng của `$D/kiem-nguon.md`. **Không** đọc cả bài rồi dán lại vào chat — bài
   nằm trong file .md, độ dài không giới hạn. Không có `phan-z.md` (lượt Z hỏng)
   thì thay bằng tóm tắt khoảng 15 dòng dựng từ `$D/tom-tat-a.md`, `$D/tom-tat-r.md`
   và báo cáo của các lượt, nói rõ là thiếu tổng luận.
8. Người dùng chỉ hỏi vài cung: chạy A và R, cộng một lượt B gồm đúng các cung
   được hỏi (sửa `phan-cong.json` bằng tay: B nhận các file `cung-*.md` đó, bỏ
   C, E), cộng D (hoặc D1, D2…) nếu có hỏi hạn, cộng T nếu có hỏi tháng. Vẫn chạy
   Z; mục 0 chỉ gồm các mục có trong bài.

Không tự luận giải trong phiên chính. Sub-agent chạy Sonnet effort high và chỉ
mang theo phần ngữ cảnh cần thiết, nên phần đọc vài chục thẻ và cân nhắc mâu
thuẫn giữa hai sách thuộc về nó.

Người dùng chỉ hỏi một cung, một câu phú, hay "sao X ở cung Y nghĩa là gì" mà
không có lá số thì giao cho sub-agent `tra-the` (Sonnet): prompt là nguyên câu
hỏi, kèm giới tính/miếu hãm nếu người dùng đã nói. Nó tra `00-index/lookup*.md`,
đọc thẻ và trả lời có nhãn nguồn; phiên chính chuyển lại câu trả lời, không
thêm ý ngoài thẻ. Câu hỏi nối tiếp rất ngắn về chính thẻ vừa tra thì phiên
chính được trả lời thẳng từ câu trả lời đó, vẫn giữ các ràng buộc nguồn bên dưới.

## Ràng buộc nguồn (áp dụng cho mọi câu nói về Tử Vi trong repo này)

Đây là điểm sống còn của dự án: giá trị nằm ở chỗ mỗi nhận định truy được về
một câu trong sách, chứ không phải ở chỗ bài luận nghe hay.

1. **Chỉ dùng kiến thức trong thẻ** `10-stars/` … `60-phu/`. Không dùng hiểu
   biết Tử Vi ngoài thẻ, dù có vẻ đúng.
2. **Mỗi nhận định mang nhãn nguồn**: `[TB]` Tân Biên, `[TL]` Thiên Lương là
   nguồn chính; `[TĐ]` Trần Đoàn, `[NPL]` Nguyễn Phát Lộc chỉ đối chứng, lấy từ
   mục **Đối chứng** của thẻ. Ghép hai thẻ hoặc suy ra điều thẻ không viết thì
   mang nhãn `[Claude]`. Mỗi sao/cách cục/quy tắc/cung/điểm hạn kết thúc bằng
   `**[Claude] Tổng kết:**` và dòng `Nguồn:` liệt kê đường dẫn thẻ.
   **Ngoại lệ duy nhất: mục `## 0. Tổng luận`** (người dùng đã chốt). Mục này chỉ
   gom các dòng Tổng kết của bài bên dưới, không thêm ý; mỗi ý gắn `[TB]`, `[TL]`
   hoặc `[TB][TL]` theo sách đỡ ý đó trong đơn vị gốc, không `[Claude]`, không
   dòng Tổng kết/`Nguồn:`; ý chỉ có `[TĐ]`/`[NPL]`/`[Claude]` đỡ thì bỏ. Người đọc
   đối chiếu ở mục cùng tên bên dưới.
3. **TB và TL khác nhau thì nêu cả hai**, không chọn thay người dùng. `[TĐ]`,
   `[NPL]` không được dùng để bác TB/TL.
4. **Chỉ dùng gạch đầu dòng thật sự thỏa lá số**: đúng địa chi, đúng miếu/hãm,
   đúng nam/nữ, đúng sao đồng cung hay hội chiếu như thẻ ghi.
5. Không có thẻ cho một bộ sao thì nói thẳng "sách trong kho không có đoạn riêng
   cho trường hợp này". Không bịa, không lấp bằng kiến thức chung.
6. Bài luận giải không trích nguyên văn: ghi ý rút gọn có nhãn, truy nguồn qua
   dòng `Nguồn:` về thẻ, rồi mục **Nguyên văn** của thẻ (có id khúc). Trả lời
   thẳng trong phiên chính mà cần trích nguyên văn thì lấy từ mục đó, không
   trích từ trí nhớ.

## Lệnh hay dùng

Luôn đặt `PYTHONIOENCODING=utf-8`. Chỉ cần Python 3, không thư viện ngoài.

```bash
# Tra thẻ cho một lá số đã xác nhận
PYTHONIOENCODING=utf-8 python3 output/claude/tuvi-kb/scripts/tra_cuu.py output/luan-giai/la-so.json
PYTHONIOENCODING=utf-8 python3 output/claude/tuvi-kb/scripts/tra_cuu.py --self-test

# Luận giải theo gói ngữ cảnh (xem Bước B)
S=output/claude/tuvi-kb/scripts; D=output/luan-giai/la-so-2026
PYTHONIOENCODING=utf-8 python3 $S/tra_cuu.py --pack output/luan-giai/la-so.json $D/      # dựng gói
PYTHONIOENCODING=utf-8 python3 $S/tra_cuu.py --kiem-pack output/luan-giai/la-so.json $D/ # gói đủ thẻ chưa
PYTHONIOENCODING=utf-8 python3 $S/kiem_bai.py $D/phan-a.md --pack $D/pack               # kiểm một phần
PYTHONIOENCODING=utf-8 python3 $S/ghep_bai.py $D output/luan-giai/la-so-2026.md
PYTHONIOENCODING=utf-8 python3 $S/kiem_bai.py output/luan-giai/la-so-2026.md --pack $D/pack
PYTHONIOENCODING=utf-8 python3 $S/lay_mau_nguon.py output/luan-giai/la-so-2026.md --so 25  # mẫu cho kiem-nguon
PYTHONIOENCODING=utf-8 python3 $S/trich_tong_ket.py $D                    # đầu vào lượt Z (tổng luận), sau kiem-nguon
PYTHONIOENCODING=utf-8 python3 $S/ghep_bai.py --chen-z output/luan-giai/la-so-2026.md $D/phan-z.md  # chèn mục 0 vào bài có sẵn
# Mỗi script trên đều có --self-test

# Bảo trì KB
PYTHONIOENCODING=utf-8 python3 scripts/validate_kb.py                 # kiểm toàn bộ, exit 1 nếu lỗi
PYTHONIOENCODING=utf-8 python3 scripts/validate_kb.py output/claude/tuvi-kb/20-palaces --no-coverage
PYTHONIOENCODING=utf-8 python3 scripts/build_lookup.py                # sinh lại 00-index/lookup*.md
PYTHONIOENCODING=utf-8 python3 scripts/dump_chunks.py --list tb       # id + tiêu đề khúc một sách
PYTHONIOENCODING=utf-8 python3 scripts/dump_chunks.py --grep "Tử Tức" # tìm khúc chứa cụm từ
```

## Khi sửa knowledge base

- Đọc `output/claude/tuvi-kb/_meta/schema.md` (quy tắc hình thức validator kiểm)
  và `docs/tuvi-kb-guide.md` (quy trình, bẫy trích dẫn OCR) trước khi viết thẻ.
  Validator từ chối thẻ sai nhãn, sai id sao/cung, trích dẫn không khớp nguyên
  văn, thẻ trùng cặp cung+sao.
- Thêm hoặc sửa thẻ xong: chạy `validate_kb.py` đến khi `lỗi: 0`, rồi
  `build_lookup.py` nếu frontmatter đổi, rồi `rm -rf scripts/__pycache__` trước
  khi commit.
- Các quyết định đã chốt (nguồn chính là TB/TL; không viết module an sao; không
  sửa tầng nguyên văn; quy ước slug, địa chi, sao trùng tên) nằm ở mục 4 của
  `docs/tuvi-kb-guide.md`. Không mở lại.
