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
| `output/claude/tuvi-kb/scripts/tra_cuu.py` | Nhận lá số JSON → in danh sách thẻ cần đọc. Không luận giải. |
| `output/chatgpt/`, `output/claude/tan-bien/` | Bản xuất cho công cụ khác. **Không dùng để luận giải, không sửa.** |
| `scripts/` | Toolchain KB đang dùng: `tuvi_kb_common.py`, `chunk_sources.py`, `validate_kb.py`, `build_lookup.py`, `dump_chunks.py`. |
| `scripts/legacy/` | Pipeline đời đầu đã ngưng, sinh ra `output/chatgpt/` và `output/claude/tan-bien/`. Giữ để tái tạo được, **không chạy trong công việc thường ngày**. Xem README trong đó. |

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
   (thư mục này đã gitignore vì chứa dữ liệu cá nhân).

### Bước B — giao cho sub-agent `xem-tu-vi`

Gọi Agent với `subagent_type: "xem-tu-vi"` (đã cấu hình Opus, effort high tại
`.claude/agents/xem-tu-vi.md`), prompt gồm: đường dẫn file JSON, năm xem hạn,
người dùng muốn luận cung nào (mặc định: đủ 12 cung), và đường dẫn file kết quả
mong muốn.

Sub-agent ghi bài luận ra `output/luan-giai/<tên>-<năm>.md` rồi báo lại đường
dẫn. **Phiên chính đọc file đó và trả nguyên văn cho người dùng** — báo cáo của
sub-agent không tự hiện ra với người dùng.

Không tự luận giải trong phiên chính. Sub-agent chạy Opus effort high và chỉ
mang theo phần ngữ cảnh cần thiết, nên phần đọc vài chục thẻ và cân nhắc mâu
thuẫn giữa hai sách thuộc về nó.

Người dùng chỉ hỏi một cung, một câu phú, hay "sao X ở cung Y nghĩa là gì" mà
không có lá số thì trả lời thẳng trong phiên chính bằng cách đọc thẻ tương ứng
(tra qua `00-index/lookup.md`), vẫn giữ nguyên các ràng buộc nguồn bên dưới.

## Ràng buộc nguồn (áp dụng cho mọi câu nói về Tử Vi trong repo này)

Đây là điểm sống còn của dự án: giá trị nằm ở chỗ mỗi nhận định truy được về
một câu trong sách, chứ không phải ở chỗ bài luận nghe hay.

1. **Chỉ dùng kiến thức trong thẻ** `10-stars/` … `60-phu/`. Không dùng hiểu
   biết Tử Vi ngoài thẻ, dù có vẻ đúng.
2. **Mỗi nhận định mang nhãn nguồn**: `[TB]` Tân Biên, `[TL]` Thiên Lương là
   nguồn chính; `[TĐ]` Trần Đoàn, `[NPL]` Nguyễn Phát Lộc chỉ đối chứng, lấy từ
   mục **Đối chứng** của thẻ. Ghép hai thẻ hoặc suy ra điều thẻ không viết thì
   ghi rõ `(suy luận của Claude, không phải nguyên văn sách)`.
3. **TB và TL khác nhau thì nêu cả hai**, không chọn thay người dùng. `[TĐ]`,
   `[NPL]` không được dùng để bác TB/TL.
4. **Chỉ dùng gạch đầu dòng thật sự thỏa lá số**: đúng địa chi, đúng miếu/hãm,
   đúng nam/nữ, đúng sao đồng cung hay hội chiếu như thẻ ghi.
5. Không có thẻ cho một bộ sao thì nói thẳng "sách trong kho không có đoạn riêng
   cho trường hợp này". Không bịa, không lấp bằng kiến thức chung.
6. Trích nguyên văn thì lấy từ mục **Nguyên văn** của thẻ (có id khúc), không
   trích từ trí nhớ.

## Lệnh hay dùng

Luôn đặt `PYTHONIOENCODING=utf-8`. Chỉ cần Python 3, không thư viện ngoài.

```bash
# Tra thẻ cho một lá số đã xác nhận
PYTHONIOENCODING=utf-8 python3 output/claude/tuvi-kb/scripts/tra_cuu.py output/luan-giai/la-so.json
PYTHONIOENCODING=utf-8 python3 output/claude/tuvi-kb/scripts/tra_cuu.py --self-test

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
