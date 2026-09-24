#!/usr/bin/env python3
"""Thư viện đọc thẻ tuvi-kb: parse thẻ thành dữ liệu có cấu trúc, lọc gạch đầu
dòng chắc chắn không khớp lá số (G2), và kiểm trích nguyên văn.

`tra_cuu.py`, `kiem_bai.py` đều import module này (cùng thư
mục, `sys.path[0]` là thư mục chứa script khi chạy trực tiếp). Không import gì
từ `scripts/` ở gốc repo, để `output/claude/tuvi-kb/` tự chứa — một số hàm bên
dưới là bản chép từ `scripts/tuvi_kb_common.py` và `scripts/validate_kb.py`,
ghi rõ nguồn chép ở mỗi hàm.

Dùng:
    python3 output/claude/tuvi-kb/scripts/kb_the.py --self-test
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

KB = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------- text
# Chép từ scripts/tuvi_kb_common.py (nfc, strip_accents, fold, squash_ws, _split_list)
# và scripts/validate_kb.py (norm_quote).

def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def fold(text: str) -> str:
    return strip_accents(text).replace("Đ", "D").replace("đ", "d")


def squash_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def norm_quote(text: str) -> str:
    return squash_ws(nfc(text)).casefold()


def _split_list(cell: str) -> list[str]:
    return [x.strip() for x in cell.split(";") if x.strip()]


# --------------------------------------------------------------- frontmatter
# Chép từ output/claude/tuvi-kb/scripts/tra_cuu.py:parse_card (bản gốc trước G1).
# tra_cuu.py import lại hàm này để giữ hành vi y hệt.

def parse_card(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    _, fm, body = text.split("---", 2)
    meta, key = {}, None
    for line in fm.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("["):
                meta[key] = [v.strip().strip('"') for v in val[1:-1].split(",") if v.strip()]
            elif val:
                meta[key] = val.strip('"')
            else:
                meta[key] = []
        elif key and line.strip().startswith("- "):
            meta[key].append(line.strip()[2:].strip().strip('"'))
    title = next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), path.stem)
    meta["title"] = title
    meta["path"] = path.relative_to(KB).as_posix()
    return meta


# ------------------------------------------------------------------ The/Dong/Trich

H2_RE = re.compile(r"^##\s+(.+?)\s*$")
BULLET_START_RE = re.compile(r"^[-+*]\s+(.*)$")
LABEL_RE = re.compile(r"^\[(TB|TL|TĐ|NPL)\]\s*(.*)$")
QUOTE_RE = re.compile(r'^["“](.+)["”]\s*\(([^()\s]+)\)\s*$', re.S)
ELLIPSIS_SPLIT_RE = re.compile(r"\s*(?:\[\.\.\.\]|\[…\]|\.\.\.|…)\s*")
CARD_PATH_RE = re.compile(r"(?:10-stars|20-palaces|30-combos|40-han|50-rules|60-phu)/[^` ]+\.md")


@dataclass
class Dong:
    section: str
    nhan: str | None
    text: str
    raw: str


@dataclass
class Trich:
    n: int
    van: str
    khuc: str


@dataclass
class The:
    path: str
    meta: dict
    title: str
    sections: list[tuple[str, list[str]]]
    dong: list[Dong]
    trich: list[Trich]


def split_sections(body: str) -> tuple[str, list[tuple[str, list[str]]]]:
    """Chép từ scripts/validate_kb.py:split_sections."""
    title = ""
    sections: list[tuple[str, list[str]]] = []
    cur_name, cur_lines = "(trước mục đầu)", []
    for line in body.split("\n"):
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        m = H2_RE.match(line)
        if m:
            sections.append((cur_name, cur_lines))
            cur_name, cur_lines = m.group(1), []
            continue
        cur_lines.append(line)
    sections.append((cur_name, cur_lines))
    return title, sections


def _make_dong(section: str, raw_parts: list[str]) -> Dong:
    raw = " ".join(p.strip() for p in raw_parts).strip()
    m = LABEL_RE.match(raw)
    if m:
        return Dong(section, m.group(1), m.group(2), raw)
    return Dong(section, None, raw, raw)


def _parse_dong(section: str, lines: list[str]) -> list[Dong]:
    out: list[Dong] = []
    cur: list[str] | None = None
    for line in lines:
        m = BULLET_START_RE.match(line)
        if m:
            if cur is not None:
                out.append(_make_dong(section, cur))
            cur = [m.group(1)]
        elif line.strip() and cur is not None:
            cur.append(line.strip())
    if cur is not None:
        out.append(_make_dong(section, cur))
    return out


def _parse_trich(lines: list[str]) -> list[Trich]:
    """Gom khối '> ...' và tách bằng QUOTE_RE, cùng logic scripts/validate_kb.py:check_quotes."""
    groups: list[list[str]] = []
    cur: list[str] = []
    for line in lines:
        if line.startswith(">"):
            text = line[1:].lstrip()
            if text == "" and cur:
                groups.append(cur)
                cur = []
            elif text:
                cur.append(text)
        elif cur:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    out: list[Trich] = []
    n = 0
    for group in groups:
        joined = " ".join(group).strip()
        m = QUOTE_RE.match(joined)
        if not m:
            continue
        n += 1
        out.append(Trich(n, m.group(1), m.group(2)))
    return out


def doc_the(path: Path) -> The:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    meta = parse_card(path)
    _, _, body = text.split("---", 2)
    title, sections = split_sections(body)
    dong: list[Dong] = []
    trich: list[Trich] = []
    for name, lines in sections:
        if name == "Nguyên văn":
            trich = _parse_trich(lines)
            continue
        dong.extend(_parse_dong(name, lines))
    return The(path=meta["path"], meta=meta, title=title or meta.get("title", path.stem),
                sections=sections, dong=dong, trich=trich)


# --------------------------------------------------------------------- registry
# NameDetector chép nguyên văn từ scripts/tuvi_kb_common.py.

class NameDetector:
    """Find registry names in text. Xem docstring gốc ở scripts/tuvi_kb_common.py."""

    _WORD = r"[A-Za-z0-9À-ɏḀ-ỿ]"

    def __init__(self, entries: dict[str, list[str]]):
        patterns: list[tuple[int, str, bool, re.Pattern]] = []
        for ident, names in entries.items():
            for name in names:
                name = nfc(name.strip())
                if not name:
                    continue
                multi = " " in name
                needle = fold(name) if multi else name
                flags = re.I if multi else 0
                pat = re.compile(rf"(?<!{self._WORD}){re.escape(needle)}(?!{self._WORD})", flags)
                patterns.append((len(needle), ident, multi, pat))
        patterns.sort(key=lambda t: -t[0])
        self.patterns = patterns

    def count(self, text: str) -> dict[str, int]:
        text = nfc(text)
        folded = fold(text)
        assert len(folded) == len(text)
        nfc_chars = list(text)
        fold_chars = list(folded)
        counts: dict[str, int] = {}
        for _, ident, multi, pat in self.patterns:
            haystack = "".join(fold_chars if multi else nfc_chars)
            spans = [(m.start(), m.end()) for m in pat.finditer(haystack)]
            if not spans:
                continue
            counts[ident] = counts.get(ident, 0) + len(spans)
            for s, e in spans:
                for i in range(s, e):
                    nfc_chars[i] = " "
                    fold_chars[i] = " "
        return counts


def _table_rows(path: Path) -> list[list[str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or cells[0] == "id":
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


_STAR_ROWS_CACHE: list[list[str]] | None = None


def _star_rows() -> list[list[str]]:
    global _STAR_ROWS_CACHE
    if _STAR_ROWS_CACHE is None:
        _STAR_ROWS_CACHE = _table_rows(KB / "00-index" / "stars.md")
    return _STAR_ROWS_CACHE


def load_stars_for_detect() -> dict[str, list[str]]:
    """id -> [tên, aliases...] cho các sao có cột 'dò' bật. Đọc theo vị trí cột:
    id | tên | aliases | viết tắt | nhóm | hành | âm dương | dò | ghi chú."""
    entries: dict[str, list[str]] = {}
    for cells in _star_rows():
        if len(cells) < 8:
            continue
        sid, ten, aliases = cells[0], cells[1], cells[2]
        do_col = cells[7]
        if do_col.strip().lower() not in ("x", "yes", "co", "có"):
            continue
        entries[sid] = [ten] + _split_list(aliases)
    return entries


_STAR_DETECTOR: NameDetector | None = None


def star_detector() -> NameDetector:
    global _STAR_DETECTOR
    if _STAR_DETECTOR is None:
        _STAR_DETECTOR = NameDetector(load_stars_for_detect())
    return _STAR_DETECTOR


_R4_DETECTOR: NameDetector | None = None


def _r4_star_entries() -> dict[str, list[str]]:
    """Như load_stars_for_detect(), cộng thêm cột 'viết tắt' (Khoa, Quyền, Tả, Hữu, ...).
    Chỉ R4 dùng bản này: R4 chỉ cần tìm sao *có mặt*, dò rộng hơn là an toàn hơn
    (thiếu sót mới làm bỏ nhầm dòng khớp lá số; SKILL.md mới dùng viết tắt để dò tay,
    ở đây máy dò lại đúng những chữ viết tắt sách hay dùng trong câu 'Gặp ...')."""
    entries: dict[str, list[str]] = {}
    for cells in _star_rows():
        if len(cells) < 8:
            continue
        sid, ten, aliases, viet_tat = cells[0], cells[1], cells[2], cells[3]
        do_col = cells[7]
        if do_col.strip().lower() not in ("x", "yes", "co", "có"):
            continue
        entries[sid] = [ten] + _split_list(aliases) + _split_list(viet_tat)
    return entries


def r4_detector() -> NameDetector:
    global _R4_DETECTOR
    if _R4_DETECTOR is None:
        _R4_DETECTOR = NameDetector(_r4_star_entries())
    return _R4_DETECTOR


_STAR_NAME_MAPS: tuple[dict[str, str], dict[str, str]] | None = None


def star_names() -> tuple[dict[str, str], dict[str, str]]:
    """Trả (id -> tên, fold(tên).lower() -> id), lấy toàn bộ hàng (không lọc theo 'dò')."""
    global _STAR_NAME_MAPS
    if _STAR_NAME_MAPS is None:
        id_to_name: dict[str, str] = {}
        name_to_id: dict[str, str] = {}
        for cells in _star_rows():
            if len(cells) < 2:
                continue
            sid, ten = cells[0], cells[1]
            id_to_name[sid] = ten
            name_to_id[fold(ten).lower()] = sid
        _STAR_NAME_MAPS = (id_to_name, name_to_id)
    return _STAR_NAME_MAPS


# ------------------------------------------------------------------ khớp trích

_CHUNK_INDEX: dict[str, Path] | None = None
_CHUNK_NORM_CACHE: dict[str, str] = {}


def _chunk_index() -> dict[str, Path]:
    global _CHUNK_INDEX
    if _CHUNK_INDEX is None:
        idx: dict[str, Path] = {}
        for p in (KB / "90-source").rglob("*.md"):
            text = p.read_text(encoding="utf-8")
            m = re.search(r"^id:\s*(\S+)\s*$", text, re.M)
            if m:
                idx[m.group(1)] = p
        _CHUNK_INDEX = idx
    return _CHUNK_INDEX


def _chunk_body_norm(cid: str) -> str | None:
    if cid in _CHUNK_NORM_CACHE:
        return _CHUNK_NORM_CACHE[cid]
    p = _chunk_index().get(cid)
    if p is None:
        return None
    text = p.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    body = parts[2] if len(parts) == 3 else text
    norm = norm_quote(body)
    _CHUNK_NORM_CACHE[cid] = norm
    return norm


def khop_nguyen_van(van: str, khuc: str) -> bool:
    """Chép logic so khớp của scripts/validate_kb.py:check_quotes."""
    hay = _chunk_body_norm(khuc)
    if hay is None:
        return False
    pos = 0
    for seg in ELLIPSIS_SPLIT_RE.split(van):
        seg_n = norm_quote(seg).strip("\"'“”‘’ ")
        if not seg_n:
            continue
        found = hay.find(seg_n, pos)
        if found < 0:
            return False
        pos = found + len(seg_n)
    return True


# ---------------------------------------------------------------- G2: bộ lọc

FILTER_SECTIONS = {
    "star-card": {"Gặp sao khác", "Nam nữ", "Đối chứng"},
    "palace-card": {"Kết luận", "Điều kiện và sắc thái", "Đối chứng"},
}

MIEU_HAM_ORDER = ["bình hòa", "miếu", "vượng", "đắc", "bình", "hãm"]
MIEU_HAM_CODE = {"miếu": "M", "vượng": "V", "đắc": "Đ", "bình hòa": "B", "bình": "B", "hãm": "H"}
_MIEU_HAM_ALT = "|".join(re.escape(w) for w in MIEU_HAM_ORDER)
R2_HEAD_RE = re.compile(
    rf"^(?:(?:{_MIEU_HAM_ALT})(?:\s*địa)?(?:\s*(?:,|và|hay|hoặc)\s*)?)+",
    re.I,
)
R2_WORD_RE = re.compile(_MIEU_HAM_ALT, re.I)

R4_PREFIXES = ["gặp", "hội", "có", "thêm", "được", "đi với", "đồng cung với"]
R1_NAM_PREFIXES = ["nam mệnh", "đàn ông"]
R1_NU_PREFIXES = ["nữ mệnh", "nữ:", "đàn bà"]


def _strip_leading_markup(t: str) -> str:
    return re.sub(r"^[`*]+\s*", "", t.strip())


def loc_dong(the: The, dong: Dong, ctx: dict) -> str | None:
    """Trả mã lý do bỏ, hoặc None nếu giữ. Xem docs/plan-giam-token.md mục G2."""
    ctype = the.meta.get("type")
    allowed = FILTER_SECTIONS.get(ctype)
    if not allowed or dong.section not in allowed:
        return None

    t = _strip_leading_markup(dong.text)
    low = t.casefold()

    gioi = ctx.get("gioi")
    if gioi == "nam" and any(low.startswith(p) for p in R1_NU_PREFIXES):
        return "gioi"
    if gioi == "nu" and any(low.startswith(p) for p in R1_NAM_PREFIXES):
        return "gioi"

    colon_idx = t.find(":")
    dau = t[:colon_idx] if 0 <= colon_idx < 120 else ""

    stars_meta = the.meta.get("stars") or []
    muc_khop = "đủ" if ctype == "star-card" else ctx.get("muc_khop")
    if len(stars_meta) == 1 and muc_khop == "đủ" and stars_meta[0] in ctx.get("mieu", {}):
        sid = stars_meta[0]
        id_to_name, _ = star_names()
        star_name = id_to_name.get(sid, "")
        t2 = t
        if star_name and t.casefold().startswith(star_name.casefold()):
            t2 = t[len(star_name):].lstrip()
        m = R2_HEAD_RE.match(t2)
        if m and m.group(0).strip():
            words = [w.lower() for w in R2_WORD_RE.findall(m.group(0))]
            codes = {MIEU_HAM_CODE[w] for w in words}
            if codes and ctx["mieu"][sid] not in codes:
                return "mieu-ham"

    if dau:
        dau_low = dau.strip().casefold()
        if any(dau_low.startswith(p) for p in R4_PREFIXES):
            counts = r4_detector().count(dau)
            S = set(counts) - set(stars_meta) - {"tuan", "triet"}
            if S and not (S & ctx.get("quanh", set())):
                return "sao-kem"

    return None


def _cau_phu_first_line(sections: dict[str, list[str]], name: str) -> str:
    for line in sections.get(name, []):
        if line.strip():
            return line.strip()
    return ""


def _parse_sao_cung_line(line: str) -> list[tuple[str, str]]:
    m = re.search(r"Sao:\s*(.*?)(?:\.\s*Cung:|$)", line)
    if not m:
        return []
    entries: list[tuple[str, str]] = []
    for piece in m.group(1).split(","):
        piece = piece.strip()
        if not piece:
            continue
        pm = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", piece)
        if pm:
            entries.append((pm.group(1).strip(), pm.group(2).strip()))
        else:
            entries.append((piece, ""))
    return entries


def loc_phu(the: The, ctx: dict) -> str | None:
    """Trả mã lý do bỏ cả thẻ phú (P1, P2), hoặc None nếu giữ."""
    if the.meta.get("type") != "phu-card":
        return None
    sections = dict(the.sections)
    line = _cau_phu_first_line(sections, "Sao và cung liên quan")
    low_line = line.casefold()
    gioi = ctx.get("gioi")

    if gioi == "nam" and "(nữ mệnh)" in low_line:
        return "gioi"
    if gioi == "nu" and "(nam mệnh)" in low_line:
        return "gioi"

    cau_phu = _cau_phu_first_line(sections, "Câu phú")
    cau_phu = re.sub(r"^[-+*]\s+", "", cau_phu).strip().strip("\"“” ")
    if gioi == "nam" and cau_phu.casefold().startswith("nữ mệnh"):
        return "gioi"

    _, name_to_id = star_names()
    for name, paren in _parse_sao_cung_line(line):
        words = R2_WORD_RE.findall(paren)
        if not words:
            continue
        codes = {MIEU_HAM_CODE[w.lower()] for w in words}
        sid = name_to_id.get(fold(name).lower())
        if sid is None or sid not in ctx.get("mieu", {}):
            continue
        if ctx["mieu"][sid] not in codes:
            return "mieu-ham"
    return None


@dataclass
class LocBoEntry:
    the: str
    section: str
    line: str
    reason: str


def sections_dong(the: The) -> dict[str, list[Dong]]:
    """Nhóm the.dong theo mục, không lọc gì (dùng cho combo/han/rule — G2 không lọc các loại này)."""
    out: dict[str, list[Dong]] = {}
    for d in the.dong:
        out.setdefault(d.section, []).append(d)
    return out


def filter_the(the: The, ctx: dict) -> tuple[dict[str, list[Dong]], list[LocBoEntry]]:
    """Lọc một thẻ theo ctx. Với phu-card trả cả thẻ (rỗng nếu bị bỏ)."""
    if the.meta.get("type") == "phu-card":
        reason = loc_phu(the, ctx)
        if reason:
            removed = [LocBoEntry(the.path, name, l, reason) for name, lines in the.sections for l in lines if l.strip()]
            return {}, removed
        return {name: _parse_dong(name, lines) for name, lines in the.sections if name != "Nguyên văn"}, []

    kept: dict[str, list[Dong]] = {}
    removed: list[LocBoEntry] = []
    for d in the.dong:
        reason = loc_dong(the, d, ctx)
        if reason is None:
            kept.setdefault(d.section, []).append(d)
        else:
            removed.append(LocBoEntry(the.path, d.section, d.raw, reason))
    return kept, removed


# ------------------------------------------------------------------- self-test

def _load_test_ctx() -> dict:
    """Ctx cho lá số thang-pham-2026.json, cung Mệnh (Thìn). Xem docs/plan-giam-token.md G2."""
    import json

    chart_path = KB.parent.parent.parent / "output" / "luan-giai" / "thang-pham-2026.json"
    if not chart_path.exists():
        return {}
    data = json.loads(chart_path.read_text(encoding="utf-8"))
    branches = ["ty", "suu", "dan", "mao", "thin", "ti", "ngo", "mui", "than", "dau", "tuat", "hoi"]
    idx = {b: i for i, b in enumerate(branches)}
    stars_by_branch: dict[int, set[str]] = {}
    mieu_by_branch: dict[int, dict[str, str]] = {}
    for raw_branch, cell in data.get("cung", {}).items():
        bi = idx.get(raw_branch)
        if bi is None:
            continue
        ids, mieu = set(), {}
        for s in cell.get("sao", []):
            key = s.split(":")[0]
            ids.add(key)
            if ":" in s:
                mieu[key] = s.split(":", 1)[1]
        stars_by_branch[bi] = ids
        mieu_by_branch[bi] = mieu
    i = idx["thin"]
    tam_hop = [(i + 4) % 12, (i + 8) % 12]
    xung = (i + 6) % 12
    nhi_hop = (1 - i) % 12
    giap = [(i - 1) % 12, (i + 1) % 12]
    quanh: set[str] = set()
    for b in [i, *tam_hop, xung, nhi_hop, *giap]:
        quanh |= stars_by_branch.get(b, set())
    return {"gioi": "nam", "chi": i, "mieu": mieu_by_branch.get(i, {}), "quanh": quanh, "muc_khop": "đủ"}


TAM_LANG_CASES = [
    ("Kết luận", "Tham Lang miếu, vượng, đắc địa là người trung hậu", "giữ"),
    ("Kết luận", "Hãm địa là người gian hiểm", "mieu-ham"),
    ("Điều kiện và sắc thái", "Miếu, vượng, đắc địa: thân hình cao lớn", "giữ"),
    ("Điều kiện và sắc thái", "Miếu địa: thời trẻ vất vả", "mieu-ham"),
    ("Điều kiện và sắc thái", "Gặp nhiều sao sáng (Tả, Hữu, Khoa, Quyền, Lộc) hay Hỏa, Linh đắc địa", "giữ"),
    ("Điều kiện và sắc thái", "Vượng địa gặp Kỵ", "giữ"),
    ("Điều kiện và sắc thái", "Hãm địa: thân hình cao vừa tầm", "mieu-ham"),
    ("Điều kiện và sắc thái", "Hãm địa tại Tý, Ngọ, Tỵ, Hợi", "mieu-ham"),
    ("Điều kiện và sắc thái", "Hãm địa tại Tý, Ngọ", "mieu-ham"),
    ("Điều kiện và sắc thái", "Hãm địa tại Mão, Dậu", "mieu-ham"),
    ("Điều kiện và sắc thái", "Hãm địa gặp nhiều sao mờ ám", "mieu-ham"),
    ("Điều kiện và sắc thái", "Dù miếu, vượng, đắc hay hãm gặp Kỵ hoặc Riêu", "giữ"),
    ("Điều kiện và sắc thái", "Nam mệnh", "giữ"),
    ("Điều kiện và sắc thái", "Nữ mệnh", "gioi"),
    ("Điều kiện và sắc thái", "Cách Tham Vũ (Sửu, Mùi) xem", "giữ"),
    ("Đối chứng", "Tham Lang ở tứ mộ địa (Thìn, Tuất, Sửu, Mùi) rất hay", "giữ"),
]

PHU_CASES = [
    ("tham-lang-nhap-mieu-tho-nguyen-thoi.md", "bo"),
    ("tham-lang-ham-dia-tac-tru-nhan.md", "bo"),
    ("nu-menh-tham-lang-da-tat-do.md", "bo"),
    ("hoa-ky-van-nhan-bat-nai.md", "giu"),
    ("tham-xuong-cu-menh-phan-cot-tuy-si.md", "giu"),
]


def self_test() -> int:
    ok = True

    the = doc_the(KB / "20-palaces" / "menh-than" / "tham-lang.md")
    ket_luan = [d for d in the.dong if d.section == "Kết luận"]
    dieu_kien = [d for d in the.dong if d.section == "Điều kiện và sắc thái"]
    for cond, msg in (
        (len(ket_luan) == 2, f"Kết luận: {len(ket_luan)} dòng, cần 2"),
        (len(dieu_kien) == 13, f"Điều kiện và sắc thái: {len(dieu_kien)} dòng, cần 13"),
        (len(the.trich) >= 6, f"Nguyên văn: {len(the.trich)} trích, cần >= 6"),
    ):
        if not cond:
            print("SAI:", msg)
            ok = False

    ctx = _load_test_ctx()
    if not ctx:
        print("SAI: không tìm thấy output/luan-giai/thang-pham-2026.json để chạy ca kiểm G2")
        ok = False
    else:
        for section, start, want in TAM_LANG_CASES:
            cands = [d for d in the.dong if d.section == section and d.text.startswith(start)]
            if not cands:
                print(f"SAI: không tìm thấy dòng bắt đầu bằng {start!r} trong mục {section}")
                ok = False
                continue
            d = cands[0]
            got = loc_dong(the, d, ctx)
            got_label = got or "giữ"
            if got_label != want:
                print(f"SAI: [{section}] {start!r} -> {got_label}, cần {want}")
                ok = False

        for fname, want in PHU_CASES:
            p = KB / "60-phu" / fname
            if not p.exists():
                print(f"SAI: không có thẻ {fname}")
                ok = False
                continue
            t = doc_the(p)
            got = loc_phu(t, ctx)
            got_label = "bo" if got else "giu"
            if got_label != want:
                print(f"SAI: 60-phu/{fname} -> {got_label} ({got}), cần {want}")
                ok = False

    total = matched = 0
    for folder in ("10-stars", "20-palaces", "30-combos", "40-han", "50-rules", "60-phu"):
        d = KB / folder
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            if p.name.startswith("_"):
                continue
            t = doc_the(p)
            for tr in t.trich:
                total += 1
                if khop_nguyen_van(tr.van, tr.khuc):
                    matched += 1
                else:
                    print(f"SAI: {t.path} trích #{tr.n} không khớp khúc {tr.khuc}")
                    ok = False
    print(f"trích khớp nguyên văn: {matched}/{total}")

    print(f"self-test: {'đạt' if ok else 'KHÔNG đạt'}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if argv == ["--self-test"]:
        return self_test()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
