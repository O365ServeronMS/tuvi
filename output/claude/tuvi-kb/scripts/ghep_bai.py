#!/usr/bin/env python3
"""Ghép các phần bài do các lượt xem-tu-vi viết thành một bài.

Dùng:
    python3 ghep_bai.py <thư-mục-bài> <file-ra.md>
    python3 ghep_bai.py --self-test

Thứ tự ghép (cách nhau bằng `---`): tiêu đề, phan-a.md (Cách đọc, 1, 2, 3),
phan-r.md (4), `## 5. Các cung còn lại`, phan-b.md, phan-c.md, phan-e.md,
phan-a-cach-cuc.md (6), phan-d.md (7). Thiếu phần nào thì cảnh báo và ghép phần
còn lại. Không sinh mục Nguồn đã dùng: mỗi đơn vị trong bài đã có dòng `Nguồn:`.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PHAN = ("phan-a.md", "phan-r.md", "@5", "phan-b.md", "phan-c.md", "phan-e.md",
        "phan-a-cach-cuc.md", "phan-d.md")


def ghep(bai_dir: Path) -> tuple[str, list[str]]:
    canh_bao: list[str] = []
    khoi = [f"# Luận giải lá số Tử Vi — {bai_dir.resolve().name}"]
    for p in PHAN:
        if p == "@5":
            khoi.append("## 5. Các cung còn lại")
            continue
        f = bai_dir / p
        if not f.is_file():
            canh_bao.append(f"thiếu {p} — bỏ qua phần này")
            continue
        khoi.append(f.read_text(encoding="utf-8").strip())
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
        (d / "phan-a.md").write_text("## Cách đọc bài này\n\n- x\n\n## 2. Cung Mệnh\n", encoding="utf-8")
        (d / "phan-r.md").write_text("## 4. Nền chung toàn lá số\n", encoding="utf-8")
        (d / "phan-b.md").write_text("### 5.1. Phụ Mẫu — cung Ngọ\n", encoding="utf-8")
        (d / "phan-e.md").write_text("### 5.8. Tử Tức — cung Tý\n", encoding="utf-8")
        (d / "phan-d.md").write_text("## 7. Hạn năm 2026\n", encoding="utf-8")
        text, cb = ghep(d)
        if sorted(cb) != ["thiếu phan-a-cach-cuc.md — bỏ qua phần này", "thiếu phan-c.md — bỏ qua phần này"]:
            bad.append(f"cảnh báo thiếu phần sai: {cb}")
        thu_tu = ["# Luận giải lá số Tử Vi — an-2026", "## Cách đọc bài này", "## 4. Nền chung",
                  "## 5. Các cung còn lại", "### 5.1. Phụ Mẫu", "### 5.8. Tử Tức", "## 7. Hạn năm 2026"]
        vi_tri = [text.find(s) for s in thu_tu]
        if -1 in vi_tri or vi_tri != sorted(vi_tri):
            bad.append(f"thứ tự ghép sai: {list(zip(thu_tu, vi_tri))}")
        if text.count("\n---\n") != 6:
            bad.append(f"số dấu --- sai: {text.count(chr(10) + '---' + chr(10))}")
        if "Nguồn đã dùng" in text:
            bad.append("còn sinh mục Nguồn đã dùng")
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
