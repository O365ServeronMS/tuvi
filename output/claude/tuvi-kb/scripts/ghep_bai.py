#!/usr/bin/env python3
"""Ghép các phần bài do các lượt xem-tu-vi viết thành một bài.

Dùng:
    python3 ghep_bai.py <thư-mục-bài> <file-ra.md>
    python3 ghep_bai.py --chen-z <bài-đã-ghép.md> <phan-z.md> [<file-ra.md>]   # chèn/thay mục 0 vào bài có sẵn
    python3 ghep_bai.py --self-test

Thứ tự ghép (cách nhau bằng `---`): tiêu đề, phan-a.md (Cách đọc, 1, 2, 3),
phan-r.md (4), `## 5. Các cung còn lại`, phan-b.md, phan-c.md, phan-e.md,
phan-a-cach-cuc.md (6), phan-d.md (7, một năm) hoặc phan-d-<năm>.md theo năm tăng
dần (7.1, 7.2…, nhiều năm), rồi phan-t.md (8, hạn tháng một năm) hoặc phan-t-<năm>.md
(8.1, 8.2…) nếu có. Thiếu phần nào thì cảnh báo và ghép phần
còn lại. Không sinh mục Nguồn đã dùng: mỗi đơn vị trong bài đã có dòng `Nguồn:`.

Có `phan-z.md` (mục 0. Tổng luận, lượt Z viết sau lần ghép đầu) thì chèn ngay sau
"Cách đọc bài này", trước tiêu đề `##` kế tiếp của phan-a.md. Không có thì ghép như
cũ, không cảnh báo.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PHAN_Z = "phan-z.md"
PHAN = ("phan-a.md", "phan-r.md", "@5", "phan-b.md", "phan-c.md", "phan-e.md",
        "phan-a-cach-cuc.md", "@d", "@t")


def _tach_cach_doc(text: str) -> tuple[str, str] | None:
    """Tách phan-a.md tại tiêu đề `##` đầu tiên không phải "Cách đọc"; không có thì None."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("## ") and "Cách đọc" not in line:
            return "\n".join(lines[:i]).strip(), "\n".join(lines[i:]).strip()
    return None


def ghep(bai_dir: Path) -> tuple[str, list[str]]:
    canh_bao: list[str] = []
    khoi = [f"# Luận giải lá số Tử Vi — {bai_dir.resolve().name}"]
    fz = bai_dir / PHAN_Z
    z = fz.read_text(encoding="utf-8").strip() if fz.is_file() else None
    if z is not None and not (bai_dir / "phan-a.md").is_file():
        khoi.append(z)  # thiếu phan-a (đã cảnh báo bên dưới): tổng luận đứng ngay sau tiêu đề
        z = None
    for p in PHAN:
        if p == "@5":
            khoi.append("## 5. Các cung còn lại")
            continue
        if p in ("@d", "@t"):
            x = p[1]
            han = sorted(bai_dir.glob(f"phan-{x}-*.md")) or [bai_dir / f"phan-{x}.md"]
            if x == "t" and not any(f.is_file() for f in han):
                continue  # hạn tháng không bắt buộc: không xem tháng thì không có phần này
            for f in han:
                if f.is_file():
                    khoi.append(f.read_text(encoding="utf-8").strip())
                else:
                    canh_bao.append(f"thiếu {f.name} — bỏ qua phần này")
            continue
        f = bai_dir / p
        if not f.is_file():
            canh_bao.append(f"thiếu {p} — bỏ qua phần này")
            continue
        text = f.read_text(encoding="utf-8").strip()
        if p == "phan-a.md" and z is not None:
            tach = _tach_cach_doc(text)
            if tach is None:
                canh_bao.append("phan-a.md không có tiêu đề ## sau Cách đọc — tổng luận đặt sau phan-a.md")
                khoi.extend([text, z])
            else:
                khoi.extend([x for x in (tach[0], z, tach[1]) if x])
            continue
        khoi.append(text)
    return "\n\n---\n\n".join(khoi) + "\n", canh_bao


SEP = "\n\n---\n\n"


def chen_tong_luan(text: str, z: str) -> str:
    """Chèn mục 0 (nội dung phan-z.md) vào một bài đã ghép, như ghep() làm: sau "Cách đọc", trước tiêu đề
    `##` kế tiếp. Bài đã có mục 0 thì thay (bỏ cả dấu --- đi kèm)."""
    from kiem_bai import muc0  # kiem_bai không import ghep_bai, không vòng
    lines = text.split("\n")
    r = muc0(lines)
    if r is not None:
        dau, cuoi = r
        sau = cuoi
        while sau < len(lines) and lines[sau].strip() in ("", "---"):
            sau += 1
        lines = lines[:dau - 1] + lines[sau:]
    for i, line in enumerate(lines):
        if line.startswith("## ") and "Cách đọc" not in line:
            truoc, sau_ = "\n".join(lines[:i]).rstrip(), "\n".join(lines[i:])
            if truoc.endswith("---"):
                truoc = truoc[:-3].rstrip()
            return truoc + SEP + z.strip() + SEP + sau_
    return text.rstrip() + SEP + z.strip() + "\n"


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
        (d / "phan-d.md").unlink()
        (d / "phan-d-2027.md").write_text("## 7.2. Hạn năm 2027\n", encoding="utf-8")
        (d / "phan-d-2026.md").write_text("## 7.1. Hạn năm 2026\n", encoding="utf-8")
        text2, _ = ghep(d)
        if not (-1 < text2.find("## 7.1. Hạn năm 2026") < text2.find("## 7.2. Hạn năm 2027")):
            bad.append("ghép nhiều năm hạn sai thứ tự")
        if any("phan-t" in c for c in cb):
            bad.append("không xem tháng thì không được cảnh báo thiếu phan-t")
        (d / "phan-t-2026.md").write_text("## 8.1. Hạn tháng năm 2026\n", encoding="utf-8")
        text3, _ = ghep(d)
        if not (-1 < text3.find("## 7.2. Hạn năm 2027") < text3.find("## 8.1. Hạn tháng năm 2026")):
            bad.append("hạn tháng phải ghép sau hạn năm")
        (d / "phan-t-2026.md").unlink()

        # mục 0. Tổng luận
        (d / "phan-z.md").write_text("## 0. Tổng luận\n\n- [TB] ý\n", encoding="utf-8")
        text4, cb4 = ghep(d)
        thu_tu = ["## Cách đọc bài này", "## 0. Tổng luận", "## 2. Cung Mệnh", "## 4. Nền chung"]
        vi_tri = [text4.find(s) for s in thu_tu]
        if -1 in vi_tri or vi_tri != sorted(vi_tri):
            bad.append(f"tổng luận phải nằm giữa Cách đọc và mục đầu: {list(zip(thu_tu, vi_tri))}")
        if text4.count("\n---\n") != text2.count("\n---\n") + 2:
            bad.append("tổng luận phải có --- trước và sau")
        if cb4 != cb or text4.count("## 0. Tổng luận") != 1:
            bad.append(f"có phan-z.md không được thêm cảnh báo / lặp mục: {cb4}")
        a = (d / "phan-a.md").read_text(encoding="utf-8")
        (d / "phan-a.md").write_text("## 1. Bảng\n", encoding="utf-8")  # không có Cách đọc
        if not ghep(d)[0].split("\n---\n")[1].strip().startswith("## 0. Tổng luận"):
            bad.append("phan-a không có Cách đọc: tổng luận phải đứng trước phan-a")
        (d / "phan-a.md").write_text("## Cách đọc bài này\n", encoding="utf-8")
        t5, cb5 = ghep(d)
        if not any("tổng luận đặt sau" in c for c in cb5) or t5.find("## Cách đọc") > t5.find("## 0."):
            bad.append("phan-a chỉ có Cách đọc: tổng luận đặt sau và cảnh báo")
        (d / "phan-a.md").unlink()
        t6, _ = ghep(d)
        if not t6.split("\n---\n")[1].strip().startswith("## 0. Tổng luận"):
            bad.append("thiếu phan-a: tổng luận phải ngay sau tiêu đề bài")
        (d / "phan-a.md").write_text(a, encoding="utf-8")
        z = (d / "phan-z.md").read_text(encoding="utf-8")
        (d / "phan-z.md").unlink()
        khong_z = ghep(d)[0]
        if chen_tong_luan(khong_z, z) != text4:
            bad.append("--chen-z vào bài đã ghép phải ra y như ghép thư mục có phan-z.md")
        z2 = "## 0. Tổng luận\n\n- [TL] bản mới\n"
        if chen_tong_luan(text4, z2) != chen_tong_luan(khong_z, z2) or text4.count("---") != chen_tong_luan(text4, z2).count("---"):
            bad.append("--chen-z vào bài đã có mục 0 phải thay mục cũ, không thêm ---")
        text = text2
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
    if argv[:1] == ["--chen-z"] and len(argv) in (3, 4):
        bai, z = Path(argv[1]), Path(argv[2])
        out = Path(argv[3]) if len(argv) == 4 else bai
        text = chen_tong_luan(bai.read_text(encoding="utf-8"), z.read_text(encoding="utf-8"))
        out.write_text(text, encoding="utf-8")
        print(f"đã ghi {out} ({len(text.encode('utf-8'))} byte)")
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    return run(Path(argv[0]), Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
