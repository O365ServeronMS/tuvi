#!/usr/bin/env python3
"""Dựng "bản đồ quan hệ" của lá số: cung nào nối với cung nào, sao nào dồn về đâu.

Dùng:
    python3 ban_do_quan_he.py <la-so.json>            # in ra stdout
    python3 ban_do_quan_he.py --self-test

Chỉ là dữ kiện vị trí (tam hợp, xung chiếu, nhị hợp, giáp, tứ hóa, Tuần/Triệt, cát/sát
trong tam phương tứ chính) tính từ JSON, không có nhận định. Đầu vào cho lượt tổng luận
(`tong-luan`): giúp nối các cung thành mạch mà không phải đoán lại vị trí. Không nạp
sao lưu: chỉ sao trên địa bàn gốc.
"""
from __future__ import annotations

import sys
from pathlib import Path

from tra_cuu import (BRANCH_NAMES, build_context, giap, nhi_hop, tam_hop, xung)

MIEU_TEN = {"M": "miếu", "V": "vượng", "Đ": "đắc", "B": "bình", "H": "hãm"}
TU_HOA = ("hoa-loc", "hoa-quyen", "hoa-khoa", "hoa-ky")


def _fmt_chinh(ctx: dict, i: int) -> str:
    out = []
    for s in ctx["chart"][i]["stars"]:
        if ctx["star_group"].get(s) == "chinh-tinh":
            ma = ctx["mieu"].get(i, {}).get(s)
            out.append(f"{ctx['stars'][s]}" + (f" ({MIEU_TEN.get(ma, ma)})" if ma else ""))
    return ", ".join(out)


def _ten_cung(ctx: dict, i: int) -> str:
    return ctx["palaces"][ctx["chart"][i]["palace"]]


def _nhom(ctx: dict, i: int, *nhom: str) -> str:
    out = []
    for s in ctx["chart"][i]["stars"]:
        if ctx["star_group"].get(s) in nhom:
            ma = ctx["mieu"].get(i, {}).get(s)
            out.append(ctx["stars"][s] + (f" ({MIEU_TEN.get(ma, ma)})" if ma else ""))
    return ", ".join(out)


def _chinh_hoac_muon(ctx: dict, i: int) -> str:
    c = _fmt_chinh(ctx, i)
    return c if c else f"vô chính diệu, mượn {_fmt_chinh(ctx, xung(i)) or 'không có chính tinh'} từ {_ten_cung(ctx, xung(i))}"


def _cung_nhan(ctx: dict, i: int) -> str:
    return f"{_ten_cung(ctx, i)} ({BRANCH_NAMES[i]}: {_chinh_hoac_muon(ctx, i)})"


def dung(path: Path) -> str:
    ctx = build_context(path)
    chart, menh, than = ctx["chart"], ctx["menh"], ctx["than"]
    L = [f"# Bản đồ quan hệ — {path.name}", "",
         "Dữ kiện vị trí tính từ lá số, không có nhận định. Tam phương tứ chính của một cung = "
         "chính nó + hai cung tam hợp + cung xung chiếu.", ""]
    L.append(f"- Mệnh tại {BRANCH_NAMES[menh]}; Thân tại {BRANCH_NAMES[than]} (cung {_ten_cung(ctx, than)})"
             + (" — Thân cư Mệnh" if than == menh else ""))
    for k, nhan in (("cuc", "Cục"), ("ban_menh", "Bản Mệnh")):
        if ctx["data"].get(k):
            L.append(f"- {nhan}: {ctx['data'][k]}")
    L.append("")

    L.append("## Tứ hóa và Tuần/Triệt trên địa bàn")
    L.append("")
    for s in TU_HOA:
        for i in range(12):
            if s in chart[i]["stars"]:
                tp = [i, *tam_hop(i), xung(i)]
                L.append(f"- {ctx['stars'][s]} nằm cung {_ten_cung(ctx, i)} ({BRANCH_NAMES[i]}): "
                         f"chiếu/hội về {', '.join(_ten_cung(ctx, j) for j in tp[1:])}")
    for s in ("tuan", "triet"):
        for i in range(12):
            if s in chart[i]["stars"]:
                L.append(f"- {ctx['stars'][s]} án ngữ cung {_ten_cung(ctx, i)} ({BRANCH_NAMES[i]})")
    L.append("")

    L.append("## Từng cung và các cung nối với nó")
    L.append("")
    for k in range(12):
        i = (menh + k) % 12
        cell = chart[i]
        dh = cell["dai_han"]
        L.append(f"### {_ten_cung(ctx, i)} — {BRANCH_NAMES[i]}" + (f", đại hạn {dh}" if dh is not None else "")
                 + (" · có Thân" if i == than else ""))
        L.append(f"- Tọa thủ: {_chinh_hoac_muon(ctx, i)}")
        for nhan, nhom in (("Lục cát", ("luc-cat",)), ("Lục sát", ("luc-sat",)), ("Tứ hóa", ("tu-hoa",)),
                           ("Tuần/Triệt", ("tuan-triet",))):
            v = _nhom(ctx, i, *nhom)
            if v:
                L.append(f"- {nhan} đồng cung: {v}")
        th, x = tam_hop(i), xung(i)
        L.append(f"- Tam hợp: {_cung_nhan(ctx, th[0])}; {_cung_nhan(ctx, th[1])}")
        L.append(f"- Xung chiếu: {_cung_nhan(ctx, x)}")
        n, g = nhi_hop(i), giap(i)
        L.append(f"- Nhị hợp: {_ten_cung(ctx, n)} ({BRANCH_NAMES[n]}); "
                 f"giáp: {_ten_cung(ctx, g[0])} ({BRANCH_NAMES[g[0]]}) và {_ten_cung(ctx, g[1])} ({BRANCH_NAMES[g[1]]})")
        tp = [i, *th, x]
        cat = [t for j in tp for t in [_nhom(ctx, j, "luc-cat")] if t]
        sat = [t for j in tp for t in [_nhom(ctx, j, "luc-sat")] if t]
        hoa = [t for j in tp for t in [_nhom(ctx, j, "tu-hoa")] if t]
        tt = [f"{ctx['stars'][s]} ở {_ten_cung(ctx, j)}" for j in tp for s in chart[j]["stars"]
              if ctx["star_group"].get(s) == "tuan-triet"]
        L.append("- Trong tam phương tứ chính: "
                 f"cát [{'; '.join(cat) or 'không'}], sát [{'; '.join(sat) or 'không'}], "
                 f"hóa [{'; '.join(hoa) or 'không'}]" + (f", {'; '.join(tt)}" if tt else ""))
        L.append("")
    return "\n".join(L).rstrip() + "\n"


def self_test() -> int:
    import tempfile
    bad: list[str] = []
    mau = Path(__file__).resolve().parents[3] / "luan-giai"
    cand = sorted(mau.glob("*.json")) if mau.is_dir() else []
    if not cand:
        print("self-test: bỏ qua (không có lá số JSON mẫu trong output/luan-giai)")
        return 0
    text = dung(cand[0])
    for co in ("## Tứ hóa và Tuần/Triệt trên địa bàn", "### Mệnh —", "- Tam hợp:", "- Xung chiếu:"):
        if co not in text:
            bad.append(f"thiếu {co!r}")
    if text.count("\n### ") != 12:
        bad.append(f"phải có đúng 12 cung, được {text.count(chr(10) + '### ')}")
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
    if len(argv) != 1:
        print(__doc__)
        return 2
    sys.stdout.write(dung(Path(argv[0])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
