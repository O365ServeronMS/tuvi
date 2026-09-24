#!/usr/bin/env python3
"""Lấy mẫu gạch đầu dòng có nhãn sách trong bài luận giải, kèm thẻ ở dòng Nguồn của đơn vị chứa nó.

Dùng:
    python3 lay_mau_nguon.py <bai.md> [--so 25]
    python3 lay_mau_nguon.py --self-test

Chọn đều trên toàn bài (không ngẫu nhiên, chạy lại ra cùng mẫu), mỗi mục cấp
`##` được ít nhất một dòng nếu có. Sub-agent `kiem-nguon` đọc danh sách này thay
vì đọc cả bài.
"""
from __future__ import annotations

import sys
from pathlib import Path

from kb_the import CARD_PATH_RE
from kiem_bai import MIEN_TRU, NGUON_RE, NHAN_SACH_DAU_RE, _bullets, _doan


def lay_mau(text: str, so: int) -> list[dict]:
    lines = text.split("\n")
    doan = _doan(lines)
    nguon = {n: sorted({p for l in than if NGUON_RE.match(l.strip()) for p in CARD_PATH_RE.findall(l)})
             for n, _, than in doan}
    starts = [n for n, _, _ in doan]
    ung_vien = []
    for n, content, heads in _bullets(lines):
        if any(k in h for h in heads for k in MIEN_TRU) or not NHAN_SACH_DAU_RE.match(content):
            continue
        h = max(s for s in starts if s <= n)
        ung_vien.append({"dong": n, "muc": " > ".join(heads[-2:]), "cap2": heads[1] if len(heads) > 1 else "",
                         "y": content, "the": nguon.get(h, [])})
    if len(ung_vien) <= so:
        return ung_vien
    chon = {round(k * (len(ung_vien) - 1) / max(so - 1, 1)) for k in range(so)}
    cap2_co = {ung_vien[i]["cap2"] for i in chon}
    for i, u in enumerate(ung_vien):  # mục ## nào chưa có mẫu thì thêm dòng đầu của nó
        if u["cap2"] not in cap2_co:
            chon.add(i)
            cap2_co.add(u["cap2"])
    return [ung_vien[i] for i in sorted(chon)]


def run(bai: Path, so: int) -> int:
    mau = lay_mau(bai.read_text(encoding="utf-8"), so)
    for k, u in enumerate(mau, 1):
        print(f"{k}. dòng {u['dong']} — {u['muc']}")
        print(f"   {u['y']}")
        print("   thẻ: " + (", ".join(f"`{p}`" for p in u["the"]) or "(đơn vị không có dòng Nguồn)"))
    print(f"mẫu: {len(mau)}")
    return 0


def self_test() -> int:
    bad: list[str] = []
    bai = "\n".join(["# Bài", "## Cách đọc", "- [TB] miễn", "## 2. Mệnh", "#### Sao A",
                     "- [TB] ý một", "- [Claude] suy", "**[Claude] Tổng kết:** x", "Nguồn: `10-stars/a.md`",
                     "## 5. Cung", "#### Sao B"] +
                    [f"- [TL] ý {k}" for k in range(20)] + ["Nguồn: `10-stars/b.md`, `20-palaces/x/y.md`"])
    mau = lay_mau(bai, 5)
    if mau[0]["dong"] != 6 or mau[0]["the"] != ["10-stars/a.md"]:
        bad.append(f"mẫu đầu sai: {mau[0]}")
    if any("miễn" in u["y"] or "[Claude]" in u["y"] for u in mau):
        bad.append("lấy cả dòng miễn trừ hoặc dòng [Claude]")
    if mau[-1]["the"] != ["10-stars/b.md", "20-palaces/x/y.md"] or not (5 <= len(mau) <= 6):
        bad.append(f"mẫu cuối hoặc cỡ mẫu sai: {len(mau)} {mau[-1]}")
    if lay_mau(bai, 5) != mau:
        bad.append("chạy lại ra mẫu khác")
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
    so = 25
    if "--so" in argv:
        k = argv.index("--so")
        if k + 1 >= len(argv) or not argv[k + 1].isdigit():
            print(__doc__)
            return 2
        so = int(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    return run(Path(argv[0]), so)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
