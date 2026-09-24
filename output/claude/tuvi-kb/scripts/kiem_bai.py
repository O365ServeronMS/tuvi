#!/usr/bin/env python3
"""Kiểm bài luận giải (khuôn G7): nhãn nguồn, tổng kết [Claude], dòng Nguồn, đường dẫn thẻ.

Dùng:
    python3 kiem_bai.py <bai.md> [--pack <pack-dir>]
    python3 kiem_bai.py --self-test

| Mã | Kiểm |
| E2 | Nếu có blockquote `> "…" (id-khúc)` thì phải khớp nguyên văn khúc. |
| E3 | Đường dẫn thẻ trong backtick phải có trong KB (trừ dòng nói "không có thẻ");
|    | có --pack thì phải có trong gói. |
| E5 | Gạch đầu dòng ngoài mục "Bảng lá số"/"Cách đọc" phải mở bằng nhãn [TB]/[TL]/[TĐ]/[NPL]/[Claude]
|    | (được bọc backtick hoặc in đậm), trừ dòng nói "không có đoạn riêng". |
| E6 | Đoạn dưới một tiêu đề có gạch đầu dòng mang nhãn sách phải có dòng "[Claude] Tổng kết"
|    | và dòng "Nguồn:" có đường dẫn thẻ. |
Mọi mã đều là lỗi. Exit 1 nếu có lỗi.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from kb_the import CARD_PATH_RE, KB, QUOTE_RE, doc_the, khop_nguyen_van

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
DAU_DONG = r"(?:[-*+]|\d+[.)])"  # gạch đầu dòng hoặc mục đánh số
BULLET_RE = re.compile(r"^(\s*)" + DAU_DONG + r"\s+")
NHAN_SACH = r"\[(?:TB|TL|TĐ|NPL)\]"
NHAN_DAU_RE = re.compile(r"^" + DAU_DONG + r"\s+[`*]*(?:\[(?:TB|TL|TĐ|NPL|Claude)\])")
NHAN_SACH_DAU_RE = re.compile(r"^" + DAU_DONG + r"\s+[`*]*" + NHAN_SACH)
TONG_KET = "[Claude] Tổng kết"
NGUON_RE = re.compile(r"^\**Nguồn:?\**:?\s")
BACKTICK_RE = re.compile(r"`([^`]+)`")
KHUC_TAIL_RE = re.compile(r"\(([a-z]+#[^()\s]+)\)\s*$")
MIEN_TRU = ("Bảng lá số", "Cách đọc")
MIEN_NHAN = ("không có đoạn riêng",)


def the_trong_goi(pack_dir: Path) -> set[str]:
    out: set[str] = set()
    for p in pack_dir.glob("*.md"):
        if p.name == "loc-bo.md":
            continue
        for line in p.read_text(encoding="utf-8").split("\n"):
            if line.startswith("### `"):
                out.update(CARD_PATH_RE.findall(line))
    return out


def _blockquotes(lines: list[str]) -> list[tuple[int, str]]:
    """Gom các dòng '>' liền nhau thành khối; dòng '> — thẻ …' hay '>' trống thì cắt khối."""
    groups: list[tuple[int, str]] = []
    start, cur = 0, []
    for n, line in enumerate(lines, 1):
        s = line.lstrip()
        if s.startswith(">"):
            text = s[1:].strip()
            if text.startswith("— thẻ") or text == "":
                if cur:
                    groups.append((start, " ".join(cur)))
                cur = []
                continue
            if not cur:
                start = n
            cur.append(text)
        elif cur:
            groups.append((start, " ".join(cur)))
            cur = []
    if cur:
        groups.append((start, " ".join(cur)))
    return groups


def _bullets(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    """(số dòng, nội dung gạch đầu dòng kể cả dòng nối, chồng tiêu đề đang mở). Bỏ qua khối code."""
    out: list[tuple[int, str, list[str]]] = []
    stack: list[tuple[int, str]] = []
    in_code = False
    cur: list | None = None
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            if cur:
                out.append(cur)
                cur = None
            continue
        if in_code:
            continue
        h = HEADING_RE.match(line)
        b = BULLET_RE.match(line)
        if h or b or not line.strip() or line.lstrip().startswith((">", "|")):
            if cur:
                out.append(cur)
                cur = None
        if h:
            lvl = len(h.group(1))
            stack = [x for x in stack if x[0] < lvl] + [(lvl, h.group(2))]
        elif b:
            cur = [n, line.strip(), [t for _, t in stack]]
        elif cur and line.strip():
            cur[1] += " " + line.strip()
    if cur:
        out.append(cur)
    return [tuple(x) for x in out]


def _doan(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    """Chia bài theo tiêu đề: (dòng tiêu đề, tiêu đề, các dòng thân). Bỏ qua khối code."""
    out: list[tuple[int, str, list[str]]] = [(0, "(đầu bài)", [])]
    in_code = False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        h = None if in_code else HEADING_RE.match(line)
        if h:
            out.append((n, h.group(2), []))
        elif not in_code:
            out[-1][2].append(line)
    return out


def kiem(text: str, pack_dir: Path | None) -> list[str]:
    lines = text.split("\n")
    loi: list[str] = []

    # E2
    for n, joined in _blockquotes(lines):
        if not joined.startswith(('"', "“")):
            continue
        m = QUOTE_RE.match(joined)
        if not m:
            if KHUC_TAIL_RE.search(joined):
                loi.append(f"E2 dòng {n}: trích sai dạng `> \"…\" (id-khúc)`")
            continue
        if not khop_nguyen_van(m.group(1), m.group(2)):
            loi.append(f"E2 dòng {n}: câu trích không khớp nguyên văn khúc {m.group(2)}")

    # E3
    goi = the_trong_goi(pack_dir) if pack_dir is not None else None
    for n, line in enumerate(lines, 1):
        for span in BACKTICK_RE.findall(line):
            for p in CARD_PATH_RE.findall(span):
                if not (KB / p).is_file():
                    if "không có thẻ" in line:  # câu nói rõ kho thiếu thẻ này
                        continue
                    loi.append(f"E3 dòng {n}: thẻ không có trong KB: {p}")
                elif goi is not None and p not in goi:
                    loi.append(f"E3 dòng {n}: thẻ không có trong gói: {p}")

    # E5
    for n, content, heads in _bullets(lines):
        if any(k in h for h in heads for k in MIEN_TRU):
            continue
        if NHAN_DAU_RE.match(content) or any(k in content for k in MIEN_NHAN):
            continue
        loi.append(f"E5 dòng {n}: gạch đầu dòng không mở bằng nhãn nguồn/[Claude]: {content[:80]}")

    # E6
    for n, tieu_de, than in _doan(lines):
        if any(k in tieu_de for k in MIEN_TRU):
            continue
        if not any(NHAN_SACH_DAU_RE.match(l.strip()) for l in than):
            continue
        if not any(TONG_KET in l for l in than):
            loi.append(f"E6 dòng {n}: mục \"{tieu_de[:60]}\" thiếu dòng **{TONG_KET}:**")
        if not any(NGUON_RE.match(l.strip()) and CARD_PATH_RE.search(l) for l in than):
            loi.append(f"E6 dòng {n}: mục \"{tieu_de[:60]}\" thiếu dòng Nguồn: có đường dẫn thẻ")
    return loi


def run(bai: Path, pack_dir: Path | None) -> int:
    loi = kiem(bai.read_text(encoding="utf-8"), pack_dir)
    for x in loi:
        print(x)
    print(f"lỗi: {len(loi)}")
    return 1 if loi else 0


def self_test() -> int:
    bad: list[str] = []
    the_that = "20-palaces/menh-than/tham-lang.md"
    tr = doc_the(KB / the_that).trich[0]
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d) / "pack"
        pack.mkdir()
        (pack / "menh.md").write_text(f"### `{the_that}` — x [đủ]\n", encoding="utf-8")

        dung = "\n".join([
            "# Bài",
            "## Cách đọc bài này",
            "- chữ thường không nhãn, được miễn",
            "## 2. Cung Mệnh",
            "### 2.1. Tham Lang",
            "- `[TB]` Ý có nhãn trong backtick.",
            "- **[TL]** Ý có nhãn in đậm, nối dòng",
            "  sang dòng sau.",
            "- [Claude] Ghép hai ý trên.",
            "- Sách trong kho không có đoạn",
            "  riêng cho trường hợp này.",
            f'> "{tr.van}" ({tr.khuc})',
            "",
            "**[Claude] Tổng kết:** gom ý.",
            "",
            f"Nguồn: `{the_that}`",
            "### 2.2. Tổng kết cung",
            "- [Claude] Chỉ có suy luận thì không đòi Nguồn.",
        ])
        loi = kiem(dung, pack)
        if loi:
            bad.append(f"bài đúng khuôn bị báo lỗi: {loi}")

        sai = "\n".join([
            "# Bài",                                                                  # 1
            "## 2. Cung Mệnh",                                                        # 2
            "- Ý không nhãn",                                                         # 3
            "- Ý có nhãn ở giữa dòng [TB] vẫn sai",                                   # 4
            f'> "Câu bịa không có trong sách." ({tr.khuc})',                          # 5
            "- [TL] dẫn thẻ không có `20-palaces/menh-than/khong-co.md`",             # 6
            "- [TB] dẫn thẻ có trong KB nhưng ngoài gói `10-stars/tham-lang.md`",     # 7
            "Kho không có thẻ `20-palaces/menh-than/khong-co.md` — sách không có đoạn riêng.",
            "### 2.1. Thiếu cả tổng kết lẫn nguồn",                                   # 9
            "- [TB] ý",
            "### 2.2. Có tổng kết, dòng Nguồn không có đường dẫn thẻ",                # 11
            "- [NPL] ý",
            "**[Claude] Tổng kết:** x",
            "Nguồn: sách",
        ])
        loi = kiem(sai, pack)
        got = sorted(" ".join(x.split()[:3]) for x in loi)
        want = sorted(["E5 dòng 3:", "E5 dòng 4:", "E2 dòng 5:", "E3 dòng 6:", "E3 dòng 7:",
                       "E6 dòng 2:", "E6 dòng 2:", "E6 dòng 9:", "E6 dòng 9:", "E6 dòng 11:"])
        if got != want:
            bad.append(f"bài sai khuôn: mong {want}, được {got}")
    for b in bad:
        print("SAI:", b)
    print("self-test:", "đạt" if not bad else f"{len(bad)} lỗi")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if argv == ["--self-test"]:
        return self_test()
    pack = None
    if "--pack" in argv:
        k = argv.index("--pack")
        if k + 1 >= len(argv):
            print(__doc__)
            return 2
        pack = Path(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    return run(Path(argv[0]), pack)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
