#!/usr/bin/env python3
"""Rút các dòng Tổng kết của bài luận giải làm đầu vào cho lượt tổng luận (Z).

Dùng:
    python3 trich_tong_ket.py <thư-mục-bài> [--tran 30000]
    python3 trich_tong_ket.py --self-test

Ghép các `phan-*.md` như `ghep_bai.py` (cùng thứ tự), bỏ mục "Cách đọc", "Bảng lá
số" và mục "Tổng luận" nếu đã có, rồi ghi `<thư-mục-bài>/pack/tong-luan-nguon.md`:

- mỗi mục đánh số (2., 4.3., 5.1., 7., 8.2.…) một tiêu đề, kèm `nhãn mục` = các
  sách có gạch đầu dòng trong mục;
- mỗi đơn vị (tiêu đề con có gạch đầu dòng nhãn hoặc dòng Tổng kết): tên, số gạch
  đầu dòng theo sách (`nhãn: TB 3, TL 2`), cờ `TB≠TL?` nếu có dấu hiệu hai sách
  nói khác, và nguyên dòng `[Claude] Tổng kết`;
- khối "Tổng kết cung/năm…" giữ cả gạch đầu dòng [Claude];
- dòng có "không có đoạn riêng" thành `Khoảng trống:`.

Không lấy gạch đầu dòng nhãn sách, dòng `Nguồn:`. Vượt trần (byte UTF-8) thì bỏ
Tổng kết từng đơn vị trong các mục 5.x có khối tổng kết cung, rồi cảnh báo.
"""
from __future__ import annotations

import io
import re
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

from ghep_bai import ghep
from kiem_bai import BULLET_RE, DAU_DONG, HEADING_RE, MIEN_TRU, NGUON_RE, TONG_KET

TRAN = 30_000
BYTE_TOKEN = 1.9
SACH = ("TB", "TL", "TĐ", "NPL")
MIEN = MIEN_TRU + ("Tổng luận",)
SO_MUC_RE = re.compile(r"^(\d+(?:\.\d+)*)\.\s")
NHAN_DAU_RE = re.compile(r"^" + DAU_DONG + r"\s+[`*]*((?:\[(?:TB|TL|TĐ|NPL|Claude)\][`*]*\s*)+)")
NHAN_RE = re.compile(r"\[(TB|TL|TĐ|NPL|Claude)\]")
TONG_KET_RE = re.compile(r"^\**" + re.escape(TONG_KET) + r":?\**:?\s*")
KHAC_RE = re.compile(
    r"khác (?:với )?(?:TB|TL|Tân Biên|Thiên Lương)\b"
    r"|(?:TB|TL|hai sách)(?: và (?:TB|TL))? (?:nói |ghi |viết )?khác nhau"
    r"|trái (?:với|lại|ngược)|ngược (?:với|lại)|còn (?:TB|TL)\b|(?:TB|TL) lại (?:nói|cho|ghi|viết)",
    re.I)
KHOANG_TRONG = "không có đoạn riêng"


@dataclass
class DonVi:
    ten: str
    nhan: dict[str, int] = field(default_factory=dict)
    tong_ket: str = ""
    claude: list[str] = field(default_factory=list)  # gạch đầu dòng [Claude], chỉ giữ ở khối tổng kết
    van: list[str] = field(default_factory=list)      # toàn văn đơn vị, để dò cờ TB≠TL

    @property
    def la_khoi_tong_ket(self) -> bool:
        return "Tổng kết" in self.ten

    @property
    def khac(self) -> bool:
        return bool(self.nhan.get("TB") and self.nhan.get("TL") and KHAC_RE.search(" ".join(self.van)))


@dataclass
class Muc:
    so: str
    ten: str
    don_vi: list[DonVi] = field(default_factory=list)
    khoang_trong: list[str] = field(default_factory=list)

    @property
    def nhan_muc(self) -> list[str]:
        return [s for s in SACH if any(d.nhan.get(s) for d in self.don_vi)]


def _sach_dong(dong: str) -> str:
    return re.sub(r"\s+", " ", dong.replace("**", "").replace("`", "")).strip()


def rut(text: str) -> list[Muc]:
    """Chia bài thành mục đánh số → đơn vị. Bỏ khối code và các mục miễn."""
    muc: list[Muc] = []
    dv: DonVi | None = None
    bo_cap: int | None = None       # đang trong mục miễn ở cấp này
    in_code = False
    cho: list | None = None         # đoạn đang nối dòng: [loại, list chữ]

    def dong_cho() -> None:
        nonlocal cho
        if cho and dv is not None:
            loai, chu = cho
            t = _sach_dong(" ".join(chu))
            if KHOANG_TRONG in t and loai != "tk":  # câu "không có đoạn riêng" có thể vắt dòng
                loai = "kt"
            if loai == "tk":
                dv.tong_ket = TONG_KET_RE.sub("", t) if not dv.tong_ket else dv.tong_ket + " " + TONG_KET_RE.sub("", t)
            elif loai == "claude":
                dv.claude.append(t)
            elif loai == "kt" and muc:
                muc[-1].khoang_trong.append(t.lstrip("-*+ "))
            dv.van.append(t)
        cho = None

    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            dong_cho()
            continue
        if in_code:
            continue
        h = HEADING_RE.match(line)
        if h:
            dong_cho()
            cap, ten = len(h.group(1)), h.group(2).strip()
            if bo_cap is not None and cap <= bo_cap:
                bo_cap = None
            if bo_cap is not None or cap == 1:
                continue
            if any(k in ten for k in MIEN):
                bo_cap, dv = cap, None
                continue
            m = SO_MUC_RE.match(ten)
            if m and ten[m.end():].lstrip().startswith("Tổng kết") and muc:
                ten, m = ten[m.end():].strip(), None  # "### 5.1.9. Tổng kết cung…" vẫn thuộc mục đang mở
            if m:
                muc.append(Muc(m.group(1), ten[m.end():].strip()))
                dv = DonVi("(thân mục)")
            elif muc:
                dv = DonVi(ten)
            else:
                dv = None
            if dv is not None:
                muc[-1].don_vi.append(dv)
            continue
        if bo_cap is not None or dv is None:
            continue
        if not s or BULLET_RE.match(line) or NGUON_RE.match(s) or TONG_KET_RE.match(s) or s.startswith((">", "|")):
            dong_cho()
        if not s or NGUON_RE.match(s) or s.startswith(("|",)):
            continue
        if TONG_KET_RE.match(s):
            cho = ["tk", [s]]
            continue
        nd = NHAN_DAU_RE.match(s)
        if nd:
            nhan = NHAN_RE.findall(nd.group(1))
            for x in dict.fromkeys(nhan):
                if x != "Claude":
                    dv.nhan[x] = dv.nhan.get(x, 0) + 1
            if nhan[0] == "Claude" and dv.la_khoi_tong_ket:
                cho = ["claude", [s]]
            else:
                cho = ["van", [s]]
            continue
        if BULLET_RE.match(line) or cho is None:
            cho = ["van", [s]]
            continue
        cho[1].append(s)
    dong_cho()
    for m in muc:
        m.don_vi = [d for d in m.don_vi if d.nhan or d.tong_ket or d.claude]
    return [m for m in muc if m.don_vi or m.khoang_trong]


def _in_nhan(nhan: dict[str, int]) -> str:
    return ", ".join(f"{s} {nhan[s]}" for s in SACH if nhan.get(s))


def viet(muc: list[Muc], ten_bai: str, gon: bool = False) -> str:
    """gon=True: bỏ đơn vị lẻ trong mục 5.x có khối tổng kết cung."""
    out = [f"# Nguồn tổng luận — {ten_bai}", "",
           "Rút tự động từ bài ghép (`trich_tong_ket.py`). `nhãn mục`: sách có gạch đầu dòng "
           "trong mục. `nhãn`: số gạch đầu dòng theo sách trong đơn vị. `TB≠TL?`: có dấu hiệu "
           "hai sách nói khác, phải đọc Tổng kết để biết.", ""]
    for m in muc:
        nm = ", ".join(m.nhan_muc) or "không có nhãn sách"
        out.append(f"## {m.so}. {m.ten} · nhãn mục: {nm}")
        co_khoi = any(d.la_khoi_tong_ket for d in m.don_vi)
        for d in m.don_vi:
            if gon and co_khoi and m.so.startswith("5.") and not d.la_khoi_tong_ket:
                continue
            dau = f"- **{d.ten}**"
            if d.nhan:
                dau += f" · nhãn: {_in_nhan(d.nhan)}"
            if d.khac:
                dau += " · TB≠TL?"
            out.append(dau)
            out.extend(f"  - {c.lstrip('-*+ ')}" for c in d.claude)
            if d.tong_ket:
                out.append(f"  Tổng kết: {d.tong_ket}")
        out.extend(f"- Khoảng trống: {k}" for k in m.khoang_trong)
        out.append("")
    return "\n".join(out)


def _nbyte(text: str) -> int:
    return len(text.encode("utf-8"))


def run(bai_dir: Path, tran: int) -> int:
    text, canh_bao = ghep(bai_dir)
    for c in canh_bao:
        print("CẢNH BÁO", c, file=sys.stderr)
    muc = rut(text)
    if not muc:
        print(f"LỖI: không rút được mục nào từ {bai_dir}", file=sys.stderr)
        return 1
    ra = viet(muc, bai_dir.resolve().name)
    if _nbyte(ra) > tran:
        truoc = _nbyte(ra)
        ra = viet(muc, bai_dir.resolve().name, gon=True)
        print(f"CẢNH BÁO vượt trần {tran} byte ({truoc}): đã bỏ Tổng kết từng sao ở mục 5.x, "
              f"còn {_nbyte(ra)} byte", file=sys.stderr)
        if _nbyte(ra) > tran:
            print(f"CẢNH BÁO vẫn vượt trần {tran} byte, ghi nguyên không cắt thêm", file=sys.stderr)
    pack = bai_dir / "pack"
    pack.mkdir(exist_ok=True)
    out = pack / "tong-luan-nguon.md"
    out.write_text(ra, encoding="utf-8")
    n = _nbyte(ra)
    print(f"đã ghi {out} ({n} byte, ~{round(n / BYTE_TOKEN / 1000, 1)} nghìn token; "
          f"{len(muc)} mục, {sum(len(m.don_vi) for m in muc)} đơn vị)")
    return 0


BAI_MAU = {
    "phan-a.md": """## Cách đọc bài này

- [TB] giải thích nhãn, không được rút

## 1. Bảng lá số đã xác nhận

- Mệnh: Dần

## 2. Cung Mệnh — cung Dần

#### Tử Vi tọa thủ (vượng)

- [TB] Ý một.
- [TB] Ý hai, nối dòng
  sang dòng sau.
- [TL] Ý ba.
- [TĐ] Đối chứng.

**[Claude] Tổng kết:** Mệnh Tử Vi vượng, TB và TL cùng khen.

Nguồn: `10-stars/tu-vi.md`

#### Tổng kết cung Mệnh

- [Claude] Mệnh vững.

**[Claude] Tổng kết:** Mệnh tốt,
nối sang dòng hai.
""",
    "phan-r.md": """## 4. Nền chung toàn lá số

### 4.1. Âm dương thuận lý

- [TL] Thuận lý thì tốt.
- Sách trong kho không có đoạn
  riêng cho Mệnh Vô Chính Diệu ở Dần.

**[Claude] Tổng kết:** Lá số thuận lý.

Nguồn: `50-rules/x.md`
""",
    "phan-b.md": """### 5.1. Phụ Mẫu — cung Mão

#### Thái Âm tọa thủ (hãm)

- [TB] Cha mẹ vất vả.
- [TL] Khác TB, TL cho là cha mẹ khá.

**[Claude] Tổng kết:** Hai sách nói khác về cha mẹ.

Nguồn: `20-palaces/phu-mau/thai-am.md`

#### Kình Dương

- [NPL] Có hình khắc.

**[Claude] Tổng kết:** Kình Dương làm xấu thêm.

Nguồn: `10-stars/kinh-duong.md`

#### Tổng kết cung Phụ Mẫu

- [Claude] Cung Phụ Mẫu trung bình.

**[Claude] Tổng kết:** Phụ Mẫu có vất vả.
""",
    "phan-d.md": """## 7. Hạn năm 2026

Tiểu hạn do script tính theo TB 10.3.

### Đại hạn Thìn

- [TB] Đại hạn gặp Hóa Kỵ thì trắc trở.

**[Claude] Tổng kết:** Đại hạn có trắc trở.

Nguồn: `40-han/x.md`
""",
}


def self_test() -> int:
    bad: list[str] = []
    muc = rut(ghep_mau := "\n\n".join(BAI_MAU.values()))
    so = [m.so for m in muc]
    if so != ["2", "4.1", "5.1", "7"]:
        bad.append(f"thứ tự/số mục sai: {so}")
    ra = viet(muc, "an-2026")
    for khong in ("giải thích nhãn", "Mệnh: Dần", "Nguồn:", "Ý một", "Cha mẹ vất vả", "10-stars/"):
        if khong in ra:
            bad.append(f"không được rút: {khong!r}")
    for co in ("## 2. Cung Mệnh — cung Dần · nhãn mục: TB, TL, TĐ",
               "- **Tử Vi tọa thủ (vượng)** · nhãn: TB 2, TL 1, TĐ 1\n  Tổng kết: Mệnh Tử Vi vượng",
               "- **Tổng kết cung Mệnh**\n  - [Claude] Mệnh vững.\n  Tổng kết: Mệnh tốt, nối sang dòng hai.",
               "## 4.1. Âm dương thuận lý · nhãn mục: TL",
               "- Khoảng trống: Sách trong kho không có đoạn riêng cho Mệnh Vô Chính Diệu ở Dần.",
               "## 5.1. Phụ Mẫu — cung Mão · nhãn mục: TB, TL, NPL",
               "- **Thái Âm tọa thủ (hãm)** · nhãn: TB 1, TL 1 · TB≠TL?",
               "## 7. Hạn năm 2026 · nhãn mục: TB",
               "- **Đại hạn Thìn** · nhãn: TB 1\n  Tổng kết: Đại hạn có trắc trở."):
        if co not in ra:
            bad.append(f"thiếu trong bản rút: {co!r}")
    n_co = sum(l.endswith("TB≠TL?") for l in ra.split("\n"))
    if n_co != 1:
        bad.append(f"cờ TB≠TL? phải đúng 1 đơn vị, được {n_co}")
    if "Tiểu hạn do script" in ra:
        bad.append("đoạn văn phương pháp không phải đơn vị, không được rút")
    if "(thân mục)" in ra.split("## 4.1.")[0].split("## 2.")[1]:
        bad.append("thân mục 2 rỗng không được in")

    # mục Tổng luận đã có (sau khi ghép lại) phải bị bỏ
    co_z = "## 0. Tổng luận\n\n### Đúc kết\n\n- [TB] Ý tổng luận.\n\n" + ghep_mau
    if [m.so for m in rut(co_z)] != so or "Ý tổng luận" in viet(rut(co_z), "x"):
        bad.append("mục 0. Tổng luận phải bị bỏ")

    so_khoi = rut("### 5.2. Tài Bạch\n\n#### Vũ Khúc\n\n- [TB] x\n\n### 5.2.1. Tổng kết cung Tài Bạch\n\n"
                  "- [Claude] y\n\n**[Claude] Tổng kết:** z\n")
    if [m.so for m in so_khoi] != ["5.2"] or not so_khoi[0].don_vi[-1].la_khoi_tong_ket:
        bad.append("khối Tổng kết có đánh số phải thuộc mục đang mở")

    gon = viet(muc, "an-2026", gon=True)
    if "Thái Âm tọa thủ" in gon or "Kình Dương" in gon or "Tổng kết cung Phụ Mẫu" not in gon:
        bad.append("bản gọn phải bỏ đơn vị lẻ mục 5.x, giữ khối tổng kết cung")
    if "Tử Vi tọa thủ" not in gon:
        bad.append("bản gọn không được bỏ đơn vị ngoài mục 5.x")

    with tempfile.TemporaryDirectory() as d:
        bai = Path(d) / "an-2026"
        bai.mkdir()
        for ten, nd in BAI_MAU.items():
            (bai / ten).write_text(nd, encoding="utf-8")
        im = io.StringIO()
        with redirect_stdout(im), redirect_stderr(im):
            kq = run(bai, TRAN)
        if kq != 0 or (bai / "pack" / "tong-luan-nguon.md").read_text(encoding="utf-8") != ra:
            bad.append("run() ghi khác viet()")
        with redirect_stdout(im), redirect_stderr(im):
            run(bai, 100)
        if "vẫn vượt trần" not in im.getvalue():
            bad.append("vượt trần sau khi gọn phải cảnh báo")
        if (bai / "pack" / "tong-luan-nguon.md").read_text(encoding="utf-8") != gon:
            bad.append("vượt trần phải ghi bản gọn")
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
    tran = TRAN
    if "--tran" in argv:
        k = argv.index("--tran")
        try:
            tran = int(argv[k + 1])
        except (IndexError, ValueError):
            print(__doc__)
            return 2
        argv = argv[:k] + argv[k + 2:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    return run(Path(argv[0]), tran)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
