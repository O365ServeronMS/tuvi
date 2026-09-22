# Pipeline cũ — đã ngưng, giữ để tái tạo được

Năm script ở đây thuộc giai đoạn đầu của dự án (sửa lần cuối 06/2026), trước khi
có `tuvi-kb`. Chúng sinh ra các bản xuất trong `output/chatgpt/` và
`output/claude/tan-bien/` — những thư mục mà **CLAUDE.md đã ghi rõ là không dùng
để luận giải**.

Tách ra đây để không lẫn với toolchain đang sống ở `scripts/`
(`tuvi_kb_common.py`, `validate_kb.py`, `build_lookup.py`, `dump_chunks.py`,
`chunk_sources.py`). Không xóa hẳn vì nếu không có chúng thì `input/` và
`output/chatgpt/` thành dữ liệu không tái tạo được.

| script | sinh ra | ghi chú |
|---|---|---|
| `extract_vni_pdf_to_md.py` | `input/*.clean.md` từ PDF font VNI | **Đường duy nhất từ PDF về `input/`.** PDF gốc không có trong repo, nên muốn chạy lại phải có lại PDF. |
| `split_tuvi_markdown.py` | `output/*/tan-bien/` | Chỉ tách sách Tân Biên. |
| `build_gpt_knowledge_md.py` | gói knowledge từ **1** sách | Bị `merge_four_*` thay thế. |
| `merge_tuvi_books_for_gpt_knowledge.py` | gói knowledge từ **2** sách | Bị `merge_four_*` thay thế. |
| `merge_four_tuvi_books_for_gpt_knowledge.py` | `output/chatgpt/gpt_knowledge_merged/` từ **4** sách | Bản cuối của nhánh này. |

Ba script cuối chồng lên nhau theo số sách xử lý; chỉ `merge_four_*` còn khớp
với `output/chatgpt/` hiện tại.

Muốn chạy lại thì chạy từ gốc repo, ví dụ
`python3 scripts/legacy/merge_four_tuvi_books_for_gpt_knowledge.py --help`.
Chúng không import `tuvi_kb_common.py` nên việc chuyển thư mục không làm hỏng gì;
nhưng đường dẫn output mặc định bên trong có thể còn trỏ vào bố cục `output/` cũ
(trước khi tách `output/claude/` và `output/chatgpt/`) — kiểm trước khi chạy.
