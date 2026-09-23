#!/usr/bin/env python3
"""Kiểm bài luận giải: mã Q, trích nguyên văn, đường dẫn thẻ, mục nguồn, nhãn nguồn.

Dùng:
    python3 kiem_bai.py <bai.md> [--pack <pack-dir>] [--nhap]
    python3 kiem_bai.py --self-test

--nhap: kiểm một phần bài trước khi ghép (cho phép còn {Q:…}, không đòi mục Nguồn đã dùng).

| Mã | Loại | Kiểm |
| E1 | lỗi | Bài hoàn chỉnh còn `{Q:`; ở --nhap, mã Q không có trong trich.json (cần --pack). |
| E2 | lỗi | Blockquote `> "…" (id-khúc)` phải khớp nguyên văn khúc. |
| E3 | lỗi | Đường dẫn thẻ trong backtick phải có trong KB (trừ dòng nói "không có thẻ");
|    |     | có --pack thì phải có trong gói. |
| E4 | lỗi | Bài hoàn chỉnh phải có tiêu đề chứa "Nguồn đã dùng". |
| W1 | cảnh báo | Gạch đầu dòng ngoài mục miễn trừ không có nhãn nguồn/ghi chú suy luận. |
Exit 1 nếu có lỗi.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from kb_the import CARD_PATH_RE, KB, QUOTE_RE, Q_LINE_RE, doc_the, khop_nguyen_van

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+")
LABEL_ANY_RE = re.compile(r"\[(?:TB|TL|TĐ|NPL)\]")
Q_ANY_RE = re.compile(r"\{Q:([^{}\s]*)\}?")
BACKTICK_RE = re.compile(r"`([^`]+)`")
KHUC_TAIL_RE = re.compile(r"\(([a-z]+#[^()\s]+)\)\s*$")
MIEN_TRU = ("Bảng lá số", "Cách đọc", "Nguồn đã dùng")
MIEN_NHAN = ("suy luận của Claude", "không có đoạn riêng")


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
    """Gom các dòng '>' liền nhau thành khối; dòng '> — thẻ …' do chen_trich thêm thì cắt khối."""
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


def kiem(text: str, pack_dir: Path | None, nhap: bool) -> tuple[list[str], list[str]]:
    lines = text.split("\n")
    loi: list[str] = []
    canh_bao: list[str] = []
    trich = None
    if pack_dir is not None:
        trich = json.loads((pack_dir / "trich.json").read_text(encoding="utf-8"))

    # E1
    for n, line in enumerate(lines, 1):
        if "{Q:" not in line:
            continue
        if not nhap:
            loi.append(f"E1 dòng {n}: còn mã Q chưa chèn trích")
        elif trich is not None:
            for q in Q_ANY_RE.findall(line):
                if q not in trich:
                    loi.append(f"E1 dòng {n}: mã Q không có trong trich.json: {q}")
            if not Q_LINE_RE.match(line.strip()):
                loi.append(f"E1 dòng {n}: mã Q phải đứng riêng một dòng")

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

    # E4
    if not nhap and not any(HEADING_RE.match(l) and "Nguồn đã dùng" in l for l in lines):
        loi.append("E4: thiếu tiêu đề chứa \"Nguồn đã dùng\"")

    # W1
    for n, content, heads in _bullets(lines):
        if any(k in h for h in heads for k in MIEN_TRU):
            continue
        if LABEL_ANY_RE.search(content) or any(k in content for k in MIEN_NHAN):
            continue
        canh_bao.append(f"W1 dòng {n}: gạch đầu dòng không có nhãn nguồn: {content[:80]}")
    return loi, canh_bao


def run(bai: Path, pack_dir: Path | None, nhap: bool) -> int:
    loi, canh_bao = kiem(bai.read_text(encoding="utf-8"), pack_dir, nhap)
    for x in loi:
        print(x)
    for x in canh_bao:
        print(x)
    print(f"lỗi: {len(loi)}, cảnh báo: {len(canh_bao)}")
    return 1 if loi else 0


def self_test() -> int:
    bad: list[str] = []
    the_that = "20-palaces/menh-than/tham-lang.md"
    tr = doc_the(KB / the_that).trich[0]
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d) / "pack"
        pack.mkdir()
        (pack / "menh.md").write_text(f"### `{the_that}` — x [đủ]\n", encoding="utf-8")
        (pack / "trich.json").write_text(json.dumps({"20-palaces/menh-than/tham-lang#1": {
            "the": the_that, "khuc": tr.khuc, "van": tr.van}}, ensure_ascii=False), encoding="utf-8")

        hoan_chinh = "\n".join([
            "# Bài",
            "## Cách đọc bài này",
            "- chữ thường không nhãn, được miễn",
            "## 2. Mệnh",
            f"- `[TB]` Ý có nhãn trong backtick, dẫn `{the_that}`.",
            "- Ý không nhãn nhưng nối dòng",
            "  sang dòng sau vẫn không nhãn",
            "- Sách trong kho không có đoạn",
            "  riêng cho trường hợp này.",
            f'> "{tr.van}" ({tr.khuc})',
            f"> — thẻ `{the_that}`",
            f'> "Câu bịa không có trong sách." ({tr.khuc})',
            "- [TL] dẫn thẻ không có `20-palaces/menh-than/khong-co.md`",
            "- [TB] dẫn thẻ có trong KB nhưng ngoài gói `10-stars/tham-lang.md`",
            "Kho không có thẻ `20-palaces/menh-than/khong-co.md` — sách không có đoạn riêng.",
            "## 9. Nguồn đã dùng",
            f"- `{the_that}`",
        ])
        loi, cb = kiem(hoan_chinh, Path(pack), nhap=False)
        ma = sorted(x.split()[0] for x in loi)
        if ma != ["E2", "E3", "E3"]:
            bad.append(f"bài hoàn chỉnh: mong E2,E3,E3, được {loi}")
        if len(cb) != 1 or "dòng 6" not in cb[0]:
            bad.append(f"W1: mong đúng 1 cảnh báo ở dòng 6, được {cb}")

        loi, _ = kiem("# x\n- [TB] a\n{Q:20-palaces/menh-than/tham-lang#1}\n", None, nhap=False)
        if sorted(x.split()[0] for x in loi) != ["E1", "E4:"]:
            bad.append(f"thiếu E1/E4: {loi}")

        nhap = "- [TB] a\n{Q:20-palaces/menh-than/tham-lang#1}\n{Q:khong-co#1}\nxem {Q:20-palaces/menh-than/tham-lang#1} nhé\n"
        loi, _ = kiem(nhap, Path(pack), nhap=True)
        if len(loi) != 2 or not all(x.startswith("E1") for x in loi):
            bad.append(f"--nhap: mong 2 lỗi E1 (mã lạ, mã lẫn dòng), được {loi}")
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
    nhap = "--nhap" in argv
    argv = [a for a in argv if a != "--nhap"]
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
    return run(Path(argv[0]), pack, nhap)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
