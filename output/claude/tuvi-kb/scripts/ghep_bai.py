#!/usr/bin/env python3
"""Ghép các phần bài do các lượt xem-tu-vi viết thành một bài, tự sinh mục Nguồn đã dùng.

Dùng:
    python3 ghep_bai.py <thư-mục-bài> <file-ra.md>
    python3 ghep_bai.py --self-test

Thứ tự ghép (cách nhau bằng `---`): tiêu đề, phan-a.md, `## 5. Các cung còn lại`,
phan-b.md, phan-c.md, phan-a-cach-cuc.md, phan-d.md, `## 8. Nguồn đã dùng`.
Thiếu phần nào thì cảnh báo và ghép phần còn lại. Mục 8 gom mọi đường dẫn thẻ
trong backtick và mọi thẻ dẫn qua mã {Q:…}, nhóm theo thư mục, ghi mục đã dùng.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from kb_the import CARD_DIRS, CARD_PATH_RE

HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$")
SO_MUC_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s")
BACKTICK_RE = re.compile(r"`([^`]+)`")
Q_CARD_RE = re.compile(r"\{Q:([^{}\s#]+)#\d+\}")

PHAN = ("phan-a.md", "@5", "phan-b.md", "phan-c.md", "phan-a-cach-cuc.md", "phan-d.md")


def _ten_muc(heading: str) -> str:
    m = SO_MUC_RE.match(heading)
    return m.group(1) if m else heading.strip()


def gom_the(text: str, dung: dict[str, list[str]]) -> None:
    """Thêm vào `dung` {đường dẫn thẻ: [mục đã dùng]} theo thứ tự xuất hiện."""
    muc = "(đầu bài)"
    in_code = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        h = None if in_code else HEADING_RE.match(line)
        if h:
            muc = _ten_muc(h.group(2))
        paths = [p for span in BACKTICK_RE.findall(line) for p in CARD_PATH_RE.findall(span)]
        paths += [q + ".md" for q in Q_CARD_RE.findall(line)]
        for p in paths:
            ds = dung.setdefault(p, [])
            if muc not in ds:
                ds.append(muc)


def muc_nguon(dung: dict[str, list[str]]) -> str:
    out = ["## 8. Nguồn đã dùng", ""]
    if not dung:
        out.append("(bài không dẫn thẻ nào)")
    for d in CARD_DIRS:
        the = sorted(p for p in dung if p.startswith(d + "/"))
        if not the:
            continue
        out += [f"### `{d}/` ({len(the)} thẻ)", ""]
        out += [f"- `{p}` — dùng ở mục {', '.join(dung[p])}" for p in the]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def ghep(bai_dir: Path) -> tuple[str, list[str]]:
    canh_bao: list[str] = []
    khoi = [f"# Luận giải lá số Tử Vi — {bai_dir.resolve().name}"]
    dung: dict[str, list[str]] = {}
    for p in PHAN:
        if p == "@5":
            khoi.append("## 5. Các cung còn lại")
            continue
        f = bai_dir / p
        if not f.is_file():
            canh_bao.append(f"thiếu {p} — bỏ qua phần này")
            continue
        text = f.read_text(encoding="utf-8").strip()
        gom_the(text, dung)
        khoi.append(text)
    khoi.append(muc_nguon(dung).rstrip())
    return "\n\n---\n\n".join(khoi) + "\n", canh_bao


def run(bai_dir: Path, out: Path) -> int:
    text, canh_bao = ghep(bai_dir)
    for c in canh_bao:
        print("CẢNH BÁO", c, file=sys.stderr)
    out.write_text(text, encoding="utf-8")
    print(f"đã ghi {out} ({len(text.encode('utf-8'))} byte)")
    return 0


def self_test() -> int:
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        d = Path(d) / "an-2026"
        d.mkdir()
        (d / "phan-a.md").write_text(
            "## Cách đọc bài này\n\n- x\n\n## 2. Cung Mệnh\n\n### 2.1. Sao\n\n"
            "- [TB] a `20-palaces/menh-than/tham-lang.md`\n{Q:10-stars/tham-lang#1}\n", encoding="utf-8")
        (d / "phan-b.md").write_text(
            "### 5.1. Phụ Mẫu — cung Ngọ\n\n- [TB] b `20-palaces/menh-than/tham-lang.md` "
            "`50-rules/x.md` và `menh-than/tuong-doi.md`\n", encoding="utf-8")
        (d / "phan-d.md").write_text("## 7. Hạn năm 2026\n\n- [TL] c\n", encoding="utf-8")
        text, cb = ghep(d)
        if sorted(cb) != ["thiếu phan-a-cach-cuc.md — bỏ qua phần này", "thiếu phan-c.md — bỏ qua phần này"]:
            bad.append(f"cảnh báo thiếu phần sai: {cb}")
        thu_tu = ["# Luận giải lá số Tử Vi — an-2026", "## Cách đọc bài này", "## 5. Các cung còn lại",
                  "### 5.1. Phụ Mẫu", "## 7. Hạn năm 2026", "## 8. Nguồn đã dùng"]
        vi_tri = [text.find(s) for s in thu_tu]
        if -1 in vi_tri or vi_tri != sorted(vi_tri):
            bad.append(f"thứ tự ghép sai: {list(zip(thu_tu, vi_tri))}")
        if text.count("\n---\n") != 5:
            bad.append(f"số dấu --- sai: {text.count(chr(10) + '---' + chr(10))}")
        muc8 = text[text.find("## 8."):]
        for want in ("### `10-stars/` (1 thẻ)", "- `10-stars/tham-lang.md` — dùng ở mục 2.1",
                     "### `20-palaces/` (1 thẻ)", "- `20-palaces/menh-than/tham-lang.md` — dùng ở mục 2.1, 5.1",
                     "- `50-rules/x.md` — dùng ở mục 5.1"):
            if want not in muc8:
                bad.append(f"mục 8 thiếu: {want}")
        if "tuong-doi" in muc8:
            bad.append("mục 8 lấy cả đường dẫn tương đối")
        out = d / "ra.md"
        if run(d, out) != 0 or out.read_text(encoding="utf-8") != text:
            bad.append("run() ghi file khác ghep()")
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
    if len(argv) != 2:
        print(__doc__)
        return 2
    return run(Path(argv[0]), Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
