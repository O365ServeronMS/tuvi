#!/usr/bin/env python3
"""Kiểm bài luận giải (khuôn G7): nhãn nguồn, tổng kết [Claude], dòng Nguồn, đường dẫn thẻ.

Dùng:
    python3 kiem_bai.py <bai.md> [--pack <pack-dir>]
    python3 kiem_bai.py --self-test

| Mã | Kiểm |
| E2 | Nếu có blockquote `> "…" (id-khúc)` thì phải khớp nguyên văn khúc. |
| E3 | Đường dẫn thẻ trong backtick phải có trong KB (trừ dòng nói "không có thẻ");
|    | có --pack thì phải có trong gói. |
| E5 | Gạch đầu dòng ngoài mục "Bảng lá số"/"Cách đọc" phải mở bằng nhãn [TB]/[TL]/[TĐ]/[NPL]/[BĐ]/[Claude]
|    | (được bọc backtick hoặc in đậm), trừ dòng nói "không có đoạn riêng". |
| E6 | Đoạn dưới một tiêu đề có gạch đầu dòng mang nhãn sách phải có dòng "[Claude] Tổng kết"
|    | và dòng "Nguồn:" có đường dẫn thẻ. |

Mục `## 0. Tổng luận` (lượt Z, sub-agent tong-luan: bài luận của "thầy", văn xuôi) miễn E5, E6 và kiểm riêng:
| E7 | Thân mục 0 quá 20.000 ký tự. Dưới 12.000 là cảnh báo W7 (mỏng). In `mục 0: <n> ký tự`. |
| E8 | Mỗi đoạn/gạch đầu dòng phải có ít nhất một nhãn [TB], [TL] hoặc [Claude]; cấm [TĐ]/[NPL]/[BĐ];
|    | miễn đoạn nói "không có đoạn riêng" và dòng chú thích in nghiêng cả dòng. |
| E9 | Đoạn có [Claude] (ghép/suy luận) phải kèm chú dẫn `(← 2.1, 5.3)` về các mục của bài. |
| E10 | Chú dẫn `(← …)` trỏ tới số mục không có trong bài. |
| W8 | Cảnh báo: khối `[..] **<Tên>:**` gắn sách không có trong `nhãn mục` của mục
|    | cùng tên trong `<pack>/tong-luan-nguon.md` (chỉ kiểm khi có file đó). |
Mã E là lỗi, exit 1 nếu có lỗi. Mã W chỉ cảnh báo.
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
NHAN_SACH = r"\[(?:TB|TL|TĐ|NPL|BĐ)\]"
NHAN_DAU_RE = re.compile(r"^" + DAU_DONG + r"\s+[`*]*(?:\[(?:TB|TL|TĐ|NPL|BĐ|Claude)\])")
NHAN_SACH_DAU_RE = re.compile(r"^" + DAU_DONG + r"\s+[`*]*" + NHAN_SACH)
TONG_KET = "[Claude] Tổng kết"
NGUON_RE = re.compile(r"^\**Nguồn:?\**:?\s")
BACKTICK_RE = re.compile(r"`([^`]+)`")
KHUC_TAIL_RE = re.compile(r"\(([a-z]+#[^()\s]+)\)\s*$")
MIEN_TRU = ("Bảng lá số", "Cách đọc")
MIEN_NHAN = ("không có đoạn riêng",)
MUC0_RE = re.compile(r"^0\.\s+Tổng luận")
MUC0_MUC_TIEU, MUC0_TRAN = 12_000, 20_000  # mục tiêu là cận dưới: ngắn hơn thì cảnh báo mỏng
NHAN_Z_CO = re.compile(r"\[(?:TB|TL|Claude)\]")
NHAN_Z_CAM = re.compile(r"\[(?:TĐ|NPL|BĐ)\]")
CHU_DAN_RE = re.compile(r"\(←\s*([^()]*)\)")
MUC_SO_RE = re.compile(r"\d+(?:\.\d+)*")
_NHAN_Z = r"[`*]*\[(?:TB|TL)\][`*]*"
NHAN_Z_RE = re.compile(r"^" + DAU_DONG + r"\s+" + _NHAN_Z + r"(?:\s*" + _NHAN_Z + r")?(?!\s*[`*]*\[)")
NHAN_Z_TEN_RE = re.compile(r"^" + DAU_DONG + r"\s+((?:" + _NHAN_Z + r"\s*)+)\*\*([^*:()]+?)\s*(?:\([^)]*\))?:\*\*")
NGUON_Z_RE = re.compile(r"^##\s+(\d+(?:\.\d+)*)\.\s+(.*?)\s+·\s+nhãn mục:\s*(.*)$")


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


def muc0(lines: list[str]) -> tuple[int, int] | None:
    """(dòng tiêu đề, dòng cuối) của mục `## 0. Tổng luận`, tính từ 1; không có thì None."""
    in_code, dau = False, None
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        h = None if in_code else HEADING_RE.match(line)
        if not h:
            continue
        if dau is None:
            if len(h.group(1)) == 2 and MUC0_RE.match(h.group(2).strip()):
                dau = n
        elif len(h.group(1)) <= 2:
            return dau, n - 1
    return (dau, len(lines)) if dau is not None else None


def nhan_muc_nguon(pack_dir: Path | None) -> list[tuple[str, set[str]]]:
    """(tên mục, nhãn mục) đọc từ tong-luan-nguon.md của gói; không có file thì rỗng."""
    f = pack_dir / "tong-luan-nguon.md" if pack_dir is not None else None
    if f is None or not f.is_file():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").split("\n"):
        m = NGUON_Z_RE.match(line)
        if m:
            out.append((m.group(2), set(re.findall(r"TB|TL|TĐ|NPL|BĐ", m.group(3)))))
    return out


def _khop_ten(ten: str, ten_muc: str) -> bool:
    for goc in (ten, "Cung " + ten):
        if ten_muc.startswith(goc) and (len(ten_muc) == len(goc) or ten_muc[len(goc)] in " —-(,"):
            return True
    return False


def _khoi_muc0(lines: list[str], dau: int, cuoi: int) -> list[tuple[int, str]]:
    """Các khối (đoạn văn hoặc gạch đầu dòng) trong thân mục 0: (dòng đầu, nội dung). Bỏ tiêu đề, `---`."""
    out: list[tuple[int, str]] = []
    cur: list[str] = []
    start = 0
    for n in range(dau + 1, cuoi + 1):
        line = lines[n - 1]
        moi = (not line.strip()) or HEADING_RE.match(line) or line.strip() == "---" or BULLET_RE.match(line)
        if moi and cur:
            out.append((start, " ".join(cur)))
            cur = []
        if not line.strip() or HEADING_RE.match(line) or line.strip() == "---":
            continue
        if not cur:
            start = n
        cur.append(line.strip())
    if cur:
        out.append((start, " ".join(cur)))
    return out


def nhan_muc_so(pack_dir: Path | None) -> set[str]:
    f = pack_dir / "tong-luan-nguon.md" if pack_dir is not None else None
    if f is None or not f.is_file():
        return set()
    return {m.group(1) for line in f.read_text(encoding="utf-8").split("\n") for m in [NGUON_Z_RE.match(line)] if m}


def kiem_muc0(lines: list[str], pack_dir: Path | None) -> tuple[list[str], list[str], int | None]:
    """(lỗi, cảnh báo, số ký tự thân mục 0). Không có mục 0 thì ([], [], None)."""
    r = muc0(lines)
    if r is None:
        return [], [], None
    dau, cuoi = r
    than = lines[dau:cuoi]
    while than and than[-1].strip() in ("", "---"):
        than.pop()
    n_ky_tu = len("\n".join(than).strip())
    loi: list[str] = []
    cb: list[str] = []
    if n_ky_tu > MUC0_TRAN:
        loi.append(f"E7 dòng {dau}: mục 0 dài {n_ky_tu} ký tự, quá trần {MUC0_TRAN}")
    elif n_ky_tu < MUC0_MUC_TIEU:
        cb.append(f"W7 dòng {dau}: mục 0 chỉ {n_ky_tu} ký tự, dưới mục tiêu {MUC0_MUC_TIEU} (bài luận còn mỏng?)")
    nguon = nhan_muc_nguon(pack_dir)
    co_so = {m.group(1) for line in lines[cuoi:] + lines[:dau - 1]
             for m in [re.match(r"^#{2,4}\s+(\d+(?:\.\d+)*)\.\s", line)] if m} | nhan_muc_so(pack_dir)
    for n, block in _khoi_muc0(lines, dau, cuoi):
        if any(k in block for k in MIEN_NHAN):
            continue
        if block.startswith("*") and block.endswith("*"):  # dòng chú thích in nghiêng
            continue
        if NHAN_Z_CAM.search(block):
            loi.append(f"E8 dòng {n}: mục 0 không dùng [TĐ]/[NPL]/[BĐ]: {block[:80]}")
            continue
        if not NHAN_Z_CO.search(block):
            loi.append(f"E8 dòng {n}: đoạn mục 0 phải có ít nhất một nhãn [TB], [TL] hoặc [Claude]: {block[:80]}")
            continue
        if "[Claude]" in block:
            cd = CHU_DAN_RE.findall(block)
            if not cd:
                loi.append(f"E9 dòng {n}: đoạn có [Claude] phải kèm chú dẫn `(← 2.1, 5.3)` về mục trong bài: {block[:80]}")
            for so in (x for c in cd for x in MUC_SO_RE.findall(c)):
                if co_so and so not in co_so:
                    loi.append(f"E10 dòng {n}: chú dẫn trỏ tới mục {so} không có trong bài")
        m = NHAN_Z_TEN_RE.match(block)
        if not (m and nguon):
            continue
        khop = [nh for ten_muc, nh in nguon if _khop_ten(m.group(2).strip(), ten_muc)]
        if not khop:
            continue
        co = set().union(*khop)
        thieu = [x for x in re.findall(r"TB|TL", m.group(1)) if x not in co]
        if thieu:
            cb.append(f"W8 dòng {n}: \"{m.group(2).strip()}\" gắn [{', '.join(thieu)}] "
                      f"nhưng nhãn mục trong nguồn chỉ có {', '.join(sorted(co)) or 'không sách nào'}")
    return loi, cb, n_ky_tu


def kiem(text: str, pack_dir: Path | None) -> list[str]:
    return _kiem(text, pack_dir)[0]


def _kiem(text: str, pack_dir: Path | None) -> tuple[list[str], list[str], int | None]:
    lines = text.split("\n")
    loi: list[str] = []
    r0 = muc0(lines)
    trong_muc0 = (lambda n: r0[0] <= n <= r0[1]) if r0 else (lambda n: False)

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
        if any(k in h for h in heads for k in MIEN_TRU) or trong_muc0(n):
            continue
        if NHAN_DAU_RE.match(content) or any(k in content for k in MIEN_NHAN):
            continue
        loi.append(f"E5 dòng {n}: gạch đầu dòng không mở bằng nhãn nguồn/[Claude]: {content[:80]}")

    # E6
    for n, tieu_de, than in _doan(lines):
        if any(k in tieu_de for k in MIEN_TRU) or trong_muc0(n):
            continue
        if not any(NHAN_SACH_DAU_RE.match(l.strip()) for l in than):
            continue
        if not any(TONG_KET in l for l in than):
            loi.append(f"E6 dòng {n}: mục \"{tieu_de[:60]}\" thiếu dòng **{TONG_KET}:**")
        if not any(NGUON_RE.match(l.strip()) and CARD_PATH_RE.search(l) for l in than):
            loi.append(f"E6 dòng {n}: mục \"{tieu_de[:60]}\" thiếu dòng Nguồn: có đường dẫn thẻ")

    # E7, E8, W7, W8
    loi0, cb, n_ky_tu = kiem_muc0(lines, pack_dir)
    return loi + loi0, cb, n_ky_tu


def run(bai: Path, pack_dir: Path | None) -> int:
    loi, cb, n_ky_tu = _kiem(bai.read_text(encoding="utf-8"), pack_dir)
    for x in loi + cb:
        print(x)
    if n_ky_tu is not None:
        print(f"mục 0: {n_ky_tu} ký tự (mục tiêu {MUC0_MUC_TIEU}, trần {MUC0_TRAN})")
        print(f"cảnh báo: {len(cb)}")
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

        # mục 0. Tổng luận
        tl = "\n".join([
            "# Bài",                                                                  # 1
            "## Cách đọc bài này",                                                    # 2
            "- chữ thường",                                                           # 3
            "---",                                                                    # 4
            "## 0. Tổng luận",                                                        # 5
            "*Đoạn mở in nghiêng, không nhãn.*",                                                    # 6
            "### Đúc kết",                                                            # 7
            "- [TB][TL] Ý chung hai sách.",                                           # 8
            "- **[TL]** Ý in đậm nhãn.",                                              # 9
            "### Các cung",                                                           # 10
            "- [TB] **Phụ Mẫu (Thái Âm):** đúng nhãn mục.",                           # 11
            "- [TL] **Phụ Mẫu:** TL không có trong nhãn mục → W8.",                   # 12
            "- [TB] **Mệnh:** khớp mục \"Cung Mệnh\".",                               # 13
            "### Sách chưa có đoạn riêng",                                            # 14
            "- **Tử Tức:** sách trong kho không có đoạn riêng cho trường hợp này.",   # 15
            "",
            "---",
            "## 5. Các cung còn lại",                                                 # 18
            "### 5.1. Phụ Mẫu",                                                       # 19
            "- [TB] thiếu tổng kết vẫn bị E6",                                        # 20
        ])
        (pack / "tong-luan-nguon.md").write_text(
            "# Nguồn\n\n## 2. Cung Mệnh — cung Dần · nhãn mục: TB, TL\n"
            "## 5.1. Phụ Mẫu — cung Mão · nhãn mục: TB, NPL\n", encoding="utf-8")
        loi, cb, n0 = _kiem(tl, pack)
        if muc0(tl.split("\n")) != (5, 17):
            bad.append(f"phạm vi mục 0 sai: {muc0(tl.split(chr(10)))}")
        if sorted(" ".join(x.split()[:3]) for x in loi) != ["E6 dòng 19:", "E6 dòng 19:"]:
            bad.append(f"mục 0 đúng khuôn bị báo lỗi / mục 5 phải còn E6: {loi}")
        if [" ".join(x.split()[:3]) for x in cb] != ["W7 dòng 5:", "W8 dòng 12:"]:
            bad.append(f"W8 sai: {cb}")
        than = "\n".join(tl.split("\n")[5:15]).strip()
        if n0 != len(than):
            bad.append(f"đếm ký tự mục 0 sai: {n0} ≠ {len(than)}")

        sai0 = "\n".join([
            "## 0. Tổng luận",                                                        # 1
            "- [TĐ] Đối chứng không được ở mục 0.",                                   # 2
            "- Ý không nhãn.",                                                        # 3
            "- [Claude] Ghép mà không chú dẫn.",                                      # 4
            "- [Claude] Chú dẫn trỏ mục không có (← 9.9).",                           # 5
            "- [TB] `20-palaces/menh-than/khong-co.md` vẫn kiểm E3.",                 # 6
            "- [Claude] Ghép có chú dẫn đúng (← 2).",                                 # 7
            "Đoạn văn xuôi có [TL] ở giữa câu vẫn được.",                             # 8
            "- [BĐ] Blog Bửu Đình không được ở mục 0.",                              # 9
            "## 2. Cung Mệnh",                                                        # 10
        ])
        got = sorted(" ".join(x.split()[:3]) for x in kiem(sai0, None))
        want = sorted(["E8 dòng 2:", "E8 dòng 3:", "E9 dòng 4:", "E10 dòng 5:", "E3 dòng 6:", "E8 dòng 9:"])
        if got != want:
            bad.append(f"mục 0 sai khuôn: mong {want}, được {got}")

        if not NHAN_DAU_RE.match("- [BĐ] ý đối chứng") or not NHAN_SACH_DAU_RE.match("- `[BĐ]` ý"):
            bad.append("E5 phải nhận nhãn [BĐ] ở đầu gạch đầu dòng")

        rieng = "## 0. Tổng luận\n\nĐoạn nối [Claude] (← 2, 5.1.).\n\nĐoạn sai [Claude] (← 0, 7).\n"
        got = [" ".join(x.split()[:3]) for x in _kiem(rieng, pack)[0]]
        if got != ["E10 dòng 5:", "E10 dòng 5:"]:
            bad.append(f"kiểm riêng phan-z.md: chú dẫn hợp lệ lấy từ pack, mục 0/7 không có: {got}")

        dai = "## 0. Tổng luận\n- [TB] " + "x" * (MUC0_TRAN - 6)  # "- [TB] " dài 7
        loi, cb, n0 = _kiem(dai, None)
        if not any(x.startswith("E7") for x in loi) or n0 != MUC0_TRAN + 1:
            bad.append(f"quá trần phải báo E7: {loi} ({n0})")
        du = "## 0. Tổng luận\n- [TB] " + "x" * (MUC0_MUC_TIEU + 100)
        loi, cb, _ = _kiem(du, None)
        if loi or cb:
            bad.append(f"đủ dài không được lỗi/cảnh báo: {loi} {cb}")
        ngan = "## 0. Tổng luận\n- [TB] ngắn"
        loi, cb, _ = _kiem(ngan, None)
        if loi or not any(x.startswith("W7") for x in cb):
            bad.append(f"quá ngắn chỉ cảnh báo W7: {loi} {cb}")
        if _kiem(dung, pack)[1:] != ([], None):
            bad.append("bài không có mục 0 không được có cảnh báo/số ký tự")
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
