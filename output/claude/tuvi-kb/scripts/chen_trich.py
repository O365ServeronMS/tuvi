#!/usr/bin/env python3
"""Thay mỗi dòng {Q:<mã>} trong bài bằng câu trích nguyên văn lấy từ pack/trich.json.

Dùng:
    python3 chen_trich.py <bai.md> <pack-dir> [-o out.md]   # không có -o thì ghi đè bai.md
    python3 chen_trich.py --self-test

Dòng chỉ gồm `{Q:…}` thành:
    > "<van>" (<khuc>)
    > — thẻ `<the>`
Mã không có trong trich.json, hoặc `{Q:` lẫn trong dòng có chữ khác → lỗi, exit 1,
không ghi file. Chạy lại trên kết quả thì không đổi gì.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from kb_the import Q_LINE_RE


def chen(text: str, trich: dict) -> tuple[str, list[str]]:
    out: list[str] = []
    loi: list[str] = []
    for n, line in enumerate(text.split("\n"), 1):
        m = Q_LINE_RE.match(line.strip())
        if m:
            q = trich.get(m.group(1))
            if q is None:
                loi.append(f"dòng {n}: mã không có trong trich.json: {m.group(1)}")
                out.append(line)
                continue
            out.append(f'> "{q["van"]}" ({q["khuc"]})')
            out.append(f"> — thẻ `{q['the']}`")
        else:
            if "{Q:" in line:
                loi.append(f"dòng {n}: `{{Q:` nằm lẫn trong dòng có chữ khác — mã Q phải đứng riêng một dòng")
            out.append(line)
    return "\n".join(out), loi


def run(bai: Path, pack_dir: Path, out: Path | None) -> int:
    trich = json.loads((pack_dir / "trich.json").read_text(encoding="utf-8"))
    text, loi = chen(bai.read_text(encoding="utf-8"), trich)
    for l in loi:
        print("LỖI", l, file=sys.stderr)
    if loi:
        print(f"lỗi: {len(loi)} — chưa ghi file", file=sys.stderr)
        return 1
    (out or bai).write_text(text, encoding="utf-8")
    return 0


def self_test() -> int:
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "pack").mkdir()
        trich = {"20-palaces/x/y#1": {"the": "20-palaces/x/y.md", "khuc": "tb#0001-abc", "van": "Câu trích một."}}
        (d / "pack" / "trich.json").write_text(json.dumps(trich, ensure_ascii=False), encoding="utf-8")
        src = "# Bài\n\n- [TB] Ý chính.\n  {Q:20-palaces/x/y#1}  \nhết\n"
        (d / "bai.md").write_text(src, encoding="utf-8")
        if run(d / "bai.md", d / "pack", d / "ra.md") != 0:
            bad.append("ca đúng bị báo lỗi")
        got = (d / "ra.md").read_text(encoding="utf-8")
        want = '# Bài\n\n- [TB] Ý chính.\n> "Câu trích một." (tb#0001-abc)\n> — thẻ `20-palaces/x/y.md`\nhết\n'
        if got != want:
            bad.append(f"kết quả sai:\n{got!r}")
        if run(d / "ra.md", d / "pack", d / "ra2.md") != 0 or (d / "ra2.md").read_text(encoding="utf-8") != got:
            bad.append("chạy lần hai làm đổi nội dung")

        (d / "sai1.md").write_text("a\n{Q:khong-co#9}\n", encoding="utf-8")
        _, loi = chen((d / "sai1.md").read_text(encoding="utf-8"), trich)
        if len(loi) != 1 or "dòng 2" not in loi[0]:
            bad.append(f"mã lạ không báo đúng: {loi}")
        _, loi = chen("xem {Q:20-palaces/x/y#1} nhé\n", trich)
        if len(loi) != 1 or "dòng 1" not in loi[0]:
            bad.append(f"mã lẫn trong dòng không báo đúng: {loi}")
        if run(d / "sai1.md", d / "pack", d / "khong-ghi.md") != 1 or (d / "khong-ghi.md").exists():
            bad.append("có lỗi mà vẫn ghi file hoặc exit khác 1")
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
    out = None
    if "-o" in argv:
        k = argv.index("-o")
        if k + 1 >= len(argv):
            print(__doc__)
            return 2
        out = Path(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    if len(argv) != 2:
        print(__doc__)
        return 2
    return run(Path(argv[0]), Path(argv[1]), out)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
